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
from .tables import RealAlarmsTable
from .tables import AlarmHistoryTable
from . import forms as alarm_forms
from . import constants

LOG = logging.getLogger(__name__)

SAMPLE = [{'name': _('Platform Services'),
           'services': [{'name': 'MaaS',
                         'class': 'alert-success',
                         'icon': '/static/monitoring/img/ok-icon.png',
                         'display': _('MaaS')},
                        {'name': 'DBaaS',
                         'class': 'alert-success',
                         'icon': '/static/monitoring/img/ok-icon.png',
                         'display': _('DBaaS')},
                        {'name': 'LBaaS',
                         'class': 'alert-success',
                         'icon': '/static/monitoring/img/ok-icon.png',
                         'display': _('LBaaS')},
                        {'name': 'DNSaaS',
                         'class': 'alert-success',
                         'icon': '/static/monitoring/img/ok-icon.png',
                         'display': _('DNSaaS')},
                        {'name': 'MSGaaS',
                         'class': 'alert-success',
                         'icon': '/static/monitoring/img/ok-icon.png',
                         'display': _('MSGaaS')},
                        ]},
          {'name': _('The OverCloud Services'),
           'services': [{'name': 'nova',
                         'class': 'alert-success',
                         'icon': '/static/monitoring/img/ok-icon.png',
                         'display': _('Nova')},
                        {'name': 'swift',
                         'class': 'alert-success',
                         'icon': '/static/monitoring/img/ok-icon.png',
                         'display': _('Swift')},
                        {'name': 'bock',
                         'class': 'alert-error',
                         'icon': '/static/monitoring/img/critical-icon.png',
                         'display': _('Cinder')},
                        {'name': 'glance',
                         'class': 'alert-success',
                         'icon': '/static/monitoring/img/ok-icon.png',
                         'display': _('Glance')},
                        {'name': 'quantum',
                         'class': 'alert-success',
                         'icon': '/static/monitoring/img/ok-icon.png',
                         'display': _('Neutron')},
                        {'name': 'mysql',
                         'class': 'alert-success',
                         'icon': '/static/monitoring/img/ok-icon.png',
                         'display': _('MySQL')},
                        {'name': 'rabbitmq',
                         'class': 'alert-success',
                         'icon': '/static/monitoring/img/ok-icon.png',
                         'display': _('RabbitMQ')},
                        ]},
          {'name': _('The UnderCloud Services'),
           'services': [{'name': 'nova',
                         'icon': '/static/monitoring/img/warning-icon.png',
                         'display': _('Nova')},
                        {'name': 'swift',
                         'class': 'alert-success',
                         'icon': '/static/monitoring/img/ok-icon.png',
                         'display': _('Cinder')},
                        {'name': 'glance',
                         'class': 'alert-success',
                         'icon': '/static/monitoring/img/ok-icon.png',
                         'display': _('Glance')},
                        {'name': 'horizon',
                         'class': 'alert-success',
                         'icon': '/static/monitoring/img/ok-icon.png',
                         'display': _('Horizon')},
                         {'name': 'monitoring',
                         'class': 'alert-success',
                         'icon': '/static/monitoring/img/ok-icon.png',
                         'display': _('Monitoring')},
                        ]},
          {'name': _('Network Services'),
           'services': [{'name': 'dhcp',
                         'class': 'alert-success',
                         'icon': '/static/monitoring/img/ok-icon.png',
                         'display': _('DHCP')},
                        {'name': 'dns',
                         'class': 'alert-success',
                         'icon': '/static/monitoring/img/ok-icon.png',
                         'display': _('DNS')},
                        {'name': 'dns-servers',
                         'class': 'alert-success',
                         'icon': '/static/monitoring/img/ok-icon.png',
                         'display': _('DNS Servers')},
                        {'name': 'http',
                         'class': 'alert-success',
                         'icon': '/static/monitoring/img/ok-icon.png',
                         'display': _('http')},
                        {'name': 'web_proxy',
                         'class': 'alert-success',
                         'icon': '/static/monitoring/img/ok-icon.png',
                         'display': _('Web Proxy')},
                        ]},
            ]

class IndexView(TemplateView):
    template_name = constants.TEMPLATE_PREFIX + 'index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context["date"] = datetime.datetime.utcnow()
        context["service_groups"] = SAMPLE

        return context


class StatusView(TemplateView):
    template_name = ""

    def get(self, request, *args, **kwargs):
        services = ['MaaS',
                    ]
        #monitoring.alarm_list(self.request)
        for group in SAMPLE:
            for service in group['services']:
                service['class'] = get_random_status()
        ret = {}
        ret['series'] = SAMPLE
        ret['settings'] = {}

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
        results = [{'Host': 'Compute1', 'Service': 'Nova',
                    'Status': 'WARNING',
                    'Status_Information': 'API Response Time'},
                   {'Host': 'Compute2', 'Service': 'Nova',
                    'Status': 'OK', 'Status_Information': 'System Health'},
                   {'Host': 'Compute3', 'Service': 'Nova', 'Status': 'OK',
                    'Status_Information': 'Database Access'},
                   {'Host': 'Compute4', 'Service': 'Nova', 'Status': 'OK',
                    'Status_Information': 'Network Latency'},
                   {'Host': 'Compute5', 'Service': 'Nova', 'Status': 'OK',
                    'Status_Information': 'Rabbit Health'},
                   ]

        return results

    def get_context_data(self, **kwargs):
        context = super(AlarmServiceView, self).get_context_data(**kwargs)
        context["service"] = self.service
        return context


class AlarmView(tables.DataTableView):
    table_class = RealAlarmsTable
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
            for notif_id in self._object["alarm_actions"]:
                try:
                    notification = api.monitor.notification_get(
                        self.request,
                        notif_id)
                    notifications.append(notification)
                except exceptions.NOT_FOUND:
                    msg = _("Notification %s has already been deleted.") % \
                        notif_id
                    notifications.append({"id": notif_id,
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
            for notif_id in self._object["alarm_actions"]:
                try:
                    notification = api.monitor.notification_get(
                        self.request,
                        notif_id)
                    notifications.append(notification)
                except exceptions.NOT_FOUND:
                    msg = _("Notification %s has already been deleted.") % \
                        notif_id
                    notifications.append({"id": notif_id,
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
        context["action_url"] = reverse(constants.URL_PREFIX + 'alarm_edit', args=(id,))
        return context


class AlarmHistoryView(tables.DataTableView):
    table_class = AlarmHistoryTable
    template_name = constants.TEMPLATE_PREFIX + 'alarm_history.html'

    def dispatch(self, *args, **kwargs):
        return super(AlarmHistoryView, self).dispatch(*args, **kwargs)

    def get_data(self):
        results = [
            {'Host': 'Compute1', 'Service': 'Nova', 'Status': 'CRITICAL', 'Last_Check': 'Feb 12 2014 2:34 CST', 'Status_Information': 'API Response Time'},
            {'Host': 'Compute1', 'Service': 'Nova', 'Status': 'OK', 'Last_Check': 'Feb 12 2014 2:45 CST', 'Status_Information': 'API Response Time'},
            {'Host': 'Compute1', 'Service': 'Nova', 'Status': 'WARNING', 'Last_Check': 'April 18 2014 8:45 CST', 'Status_Information': 'API Response Time'}
        ]

        return results

    def get_context_data(self, **kwargs):
        context = super(AlarmHistoryView, self).get_context_data(**kwargs)
        return context


class AlarmMeterView(TemplateView):
    template_name = constants.TEMPLATE_PREFIX + 'alarm_meter.html'


def get_random_status():
    distribution = [
        {'prob':.04, 'value':'alert-error'},
        {'prob':.04, 'value':'alert-warning'},
        {'prob':.04, 'value':'alert-unknown'},
        {'prob':.04, 'value':'alert-notfound'},
        {'prob':1.0, 'value':'alert-success'},
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
        context = super(NotificationCreateView, self).get_context_data(**kwargs)
        context["cancel_url"] = self.success_url
        context["action_url"] = reverse(constants.URL_PREFIX + 'notification_create')
        return context
