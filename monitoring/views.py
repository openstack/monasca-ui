# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.import logging

import datetime
import logging
import json
import random

from django.core.urlresolvers import reverse_lazy, reverse  # noqa
from django.template import defaultfilters as filters
from django.http import HttpResponse   # noqa
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from horizon import exceptions
from horizon import forms
from horizon import tables

from monitoring import api
from .tables import AlarmsTable
from .tables import AlarmHistoryTable
from .tables import show_service
from .tables import show_severity
from . import forms as alarm_forms
from . import constants

LOG = logging.getLogger(__name__)

SAMPLE = [{'name': _('Platform Services'),
           'services': [{'name': 'MaaS',
                         'display': _('MaaS')},
                        {'name': 'DBaaS',
                         'display': _('DBaaS')},
                        {'name': 'LBaaS',
                         'display': _('LBaaS')},
                        {'name': 'DNSaaS',
                         'display': _('DNSaaS')},
                        {'name': 'MSGaaS',
                         'display': _('MSGaaS')},
                        ]},
          {'name': _('The OverCloud Services'),
           'services': [{'name': 'nova',
                         'display': _('Nova')},
                        {'name': 'swift',
                         'display': _('Swift')},
                        {'name': 'bock',
                         'display': _('Cinder')},
                        {'name': 'glance',
                         'display': _('Glance')},
                        {'name': 'quantum',
                         'display': _('Neutron')},
                        {'name': 'mysql',
                         'display': _('MySQL')},
                        {'name': 'rabbitmq',
                         'display': _('RabbitMQ')},
                        {'name': 'mini-mon',
                         'display': _('Monitoring')},
                        ]},
          {'name': _('The UnderCloud Services'),
           'services': [{'name': 'nova',
                         'display': _('Nova')},
                        {'name': 'swift',
                         'display': _('Cinder')},
                        {'name': 'glance',
                         'display': _('Glance')},
                        {'name': 'horizon',
                         'display': _('Horizon')},
                        ]},
          {'name': _('Network Services'),
           'services': [{'name': 'dhcp',
                         'display': _('DHCP')},
                        {'name': 'dns',
                         'display': _('DNS')},
                        {'name': 'dns-servers',
                         'display': _('DNS Servers')},
                        {'name': 'http',
                         'display': _('http')},
                        {'name': 'web_proxy',
                         'display': _('Web Proxy')},
                        ]}
          ]


def get_icon(status):
    if status == 'chicklet-success':
        return constants.OK_ICON
    if status == 'chicklet-error':
        return constants.CRITICAL_ICON
    if status == 'chicklet-warning':
        return constants.WARNING_ICON
    if status == 'chicklet-unknown':
        return constants.UNKNOWN_ICON
    if status == 'chicklet-notfound':
        return constants.NOTFOUND_ICON


priorities = [
    {'status': 'chicklet-success', 'severity': 'OK'},
    {'status': 'chicklet-unknown', 'severity': 'UNDETERMINED'},
    {'status': 'chicklet-warning', 'severity': 'LOW'},
    {'status': 'chicklet-warning', 'severity': 'MEDIUM'},
    {'status': 'chicklet-warning', 'severity': 'HIGH'},
    {'status': 'chicklet-error', 'severity': 'CRITICAL'},
]
index_by_severity = {d['severity']: i for i, d in enumerate(priorities)}


def get_status(alarms):
    if not alarms:
        return 'chicklet-notfound'
    status_index = 0
    for a in alarms:
        severity = show_severity(a)
        severity_index = index_by_severity[severity]
        status_index = max(status_index, severity_index)
    return priorities[status_index]['status']


def generate_status(request):
    alarms = api.monitor.alarm_list(request)
    alarms_by_service = {}
    for a in alarms:
        service = show_service(a)
        service_alarms = alarms_by_service.setdefault(service, [])
        service_alarms.append(a)
    for row in SAMPLE:
        for service in row['services']:
            service_alarms = alarms_by_service.get(service['name'], [])
            service['class'] = get_status(service_alarms)
            service['icon'] = get_icon(service['class'])
    return SAMPLE


class IndexView(TemplateView):
    template_name = constants.TEMPLATE_PREFIX + 'index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context["date"] = datetime.datetime.utcnow()
        context["service_groups"] = generate_status(self.request)

        return context


class StatusView(TemplateView):
    template_name = ""

    def get(self, request, *args, **kwargs):
        ret = {
            'series': generate_status(self.request),
            'settings': {}
        }

        return HttpResponse(json.dumps(ret),
                            content_type='application/json')


class AlarmServiceView(tables.DataTableView):
    table_class = AlarmsTable
    template_name = constants.TEMPLATE_PREFIX + 'alarm.html'

    def dispatch(self, *args, **kwargs):
        self.service = kwargs['service']
        del kwargs['service']
        return super(AlarmServiceView, self).dispatch(*args, **kwargs)

    def get_data(self):
        alarms_json = api.monitor.alarm_list_by_service(
            self.request,
            self.service)
        return alarms_json

    def get_context_data(self, **kwargs):
        context = super(AlarmServiceView, self).get_context_data(**kwargs)
        context["service"] = self.service
        return context


class AlarmView(tables.DataTableView):
    table_class = AlarmsTable
    template_name = constants.TEMPLATE_PREFIX + 'alarm.html'

    def dispatch(self, *args, **kwargs):
        return super(AlarmView, self).dispatch(*args, **kwargs)

    def get_data(self):
        alarms = api.monitor.alarm_list(self.request)
        results = alarms

        return results

    def get_context_data(self, **kwargs):
        context = super(AlarmView, self).get_context_data(**kwargs)
        context["service"] = 'All'
        return context


class AlarmCreateView(forms.ModalFormView):
    form_class = alarm_forms.CreateAlarmForm
    template_name = constants.TEMPLATE_PREFIX + 'alarms/create.html'
    success_url = reverse_lazy(constants.URL_PREFIX + 'alarm')

    def get_context_data(self, **kwargs):
        context = super(AlarmCreateView, self).get_context_data(**kwargs)
        context["cancel_url"] = self.success_url
        context["action_url"] = reverse(constants.URL_PREFIX + 'alarm_create')
        return context


def transform_alarm_data(obj):
    return obj
    return {'id': getattr(obj, 'id', None),
            'name': getattr(obj, 'name', None),
            'expression': getattr(obj, 'expression', None),
            'state': filters.title(getattr(obj, 'state', None)),
            'severity': filters.title(getattr(obj, 'severity', None)),
            'actions_enabled': filters.title(getattr(obj, 'actions_enabled',
                                                     None)),
            'notifications': getattr(obj, 'alarm_actions', None), }


class AlarmDetailView(forms.ModalFormView):
    form_class = alarm_forms.DetailAlarmForm
    template_name = constants.TEMPLATE_PREFIX + 'alarms/detail.html'
    success_url = reverse_lazy(constants.URL_PREFIX + 'alarm')

    def get_object(self):
        id = self.kwargs['id']
        try:
            if hasattr(self, "_object"):
                return self._object
            self._object = None
            self._object = api.monitor.alarm_get(self.request, id)
            notifications = []
            # Fetch the notification object for each alarm_actions
            for id in self._object["alarm_actions"]:
                try:
                    notification = api.monitor.notification_get(
                        self.request,
                        id)
                    notifications.append(notification)
                except exceptions.NOT_FOUND:
                    msg = _("Notification %s has already been deleted.") % id
                    notifications.append({"id": id,
                                          "name": unicode(msg),
                                          "type": "",
                                          "address": ""})
            self._object["notifications"] = notifications
            return self._object
        except Exception:
            redirect = reverse(constants.URL_PREFIX + 'alarm')
            exceptions.handle(self.request,
                              _('Unable to retrieve alarm details.'),
                              redirect=redirect)
        return None

    def get_initial(self):
        self.alarm = self.get_object()
        return transform_alarm_data(self.alarm)

    def get_context_data(self, **kwargs):
        context = super(AlarmDetailView, self).get_context_data(**kwargs)
        context["alarm"] = self.alarm
        context["cancel_url"] = self.success_url
        return context


class AlarmEditView(forms.ModalFormView):
    form_class = alarm_forms.EditAlarmForm
    template_name = constants.TEMPLATE_PREFIX + 'alarms/edit.html'
    success_url = reverse_lazy(constants.URL_PREFIX + 'alarm')

    def get_object(self):
        id = self.kwargs['id']
        try:
            if hasattr(self, "_object"):
                return self._object
            self._object = None
            self._object = api.monitor.alarm_get(self.request, id)
            notifications = []
            # Fetch the notification object for each alarm_actions
            for id in self._object["alarm_actions"]:
                try:
                    notification = api.monitor.notification_get(
                        self.request,
                        id)
                    notifications.append(notification)
                except exceptions.NOT_FOUND:
                    msg = _("Notification %s has already been deleted.") % id
                    notifications.append({"id": id,
                                          "name": unicode(msg),
                                          "type": "",
                                          "address": ""})
            self._object["notifications"] = notifications
            return self._object
        except Exception:
            redirect = reverse(constants.URL_PREFIX + 'alarm')
            exceptions.handle(self.request,
                              _('Unable to retrieve alarm details.'),
                              redirect=redirect)
        return None

    def get_initial(self):
        self.alarm = self.get_object()
        return transform_alarm_data(self.alarm)

    def get_context_data(self, **kwargs):
        context = super(AlarmEditView, self).get_context_data(**kwargs)
        id = self.kwargs['id']
        context["cancel_url"] = self.success_url
        context["action_url"] = reverse(constants.URL_PREFIX + 'alarm_edit',
                                        args=(id,))
        return context


class AlarmHistoryView(tables.DataTableView):
    table_class = AlarmHistoryTable
    template_name = constants.TEMPLATE_PREFIX + 'alarm_history.html'

    def dispatch(self, *args, **kwargs):
        return super(AlarmHistoryView, self).dispatch(*args, **kwargs)

    def get_data(self):
        # to be implemented
        results = []

        return results

    def get_context_data(self, **kwargs):
        context = super(AlarmHistoryView, self).get_context_data(**kwargs)
        return context


class AlarmMeterView(TemplateView):
    template_name = constants.TEMPLATE_PREFIX + 'alarm_meter.html'


def get_random_status():
    distribution = [
        {'prob': .04, 'value': 'chicklet-error'},
        {'prob': .04, 'value': 'chicklet-warning'},
        {'prob': .04, 'value': 'chicklet-unknown'},
        {'prob': .04, 'value': 'chicklet-notfound'},
        {'prob': 1.0, 'value': 'chicklet-success'},
    ]
    num = random.random()
    for dist in distribution:
        if num < dist["prob"]:
            return dist["value"]
        num = num - dist["prob"]
    return distribution[len(distribution) - 1]["value"]


class NotificationCreateView(forms.ModalFormView):
    form_class = alarm_forms.CreateMethodForm
    template_name = constants.TEMPLATE_PREFIX + 'notifications/create.html'
    success_url = reverse_lazy(constants.URL_PREFIX + 'alarm')

    def get_context_data(self, **kwargs):
        context = super(NotificationCreateView, self). \
            get_context_data(**kwargs)
        context["cancel_url"] = self.success_url
        action = constants.URL_PREFIX + 'notification_create'
        context["action_url"] = reverse(action)
        return context
