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

import json
import logging

from django.conf import settings  # noqa
from django.contrib import messages
from django.core.urlresolvers import reverse_lazy, reverse  # noqa
from django.shortcuts import redirect
from django.template import defaultfilters as filters
from django.utils.translation import ugettext as _  # noqa
from django.views.generic import View  # noqa
from django.views.generic import TemplateView  # noqa

from horizon import exceptions
from horizon import forms
from horizon import tables

import monascaclient.exc as exc
from monitoring.alarms import constants
from monitoring.alarms import forms as alarm_forms
from monitoring.alarms import tables as alarm_tables
from monitoring import api

LOG = logging.getLogger(__name__)
SERVICES = getattr(settings, 'MONITORING_SERVICES', [])


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
        severity = alarm_tables.show_severity(a)
        severity_index = index_by_severity[severity]
        status_index = max(status_index, severity_index)
    return priorities[status_index]['status']


def generate_status(request):
    try:
        alarms = api.monitor.alarm_list(request)
    except Exception:
        alarms = []
    alarms_by_service = {}
    for a in alarms:
        service = alarm_tables.show_service(a)
        service_alarms = alarms_by_service.setdefault(service, [])
        service_alarms.append(a)
    for row in SERVICES:
        row['name'] = unicode(row['name'])
        for service in row['services']:
            service_alarms = alarms_by_service.get(service['name'], [])
            service['class'] = get_status(service_alarms)
            service['icon'] = get_icon(service['class'])
            service['display'] = unicode(service['display'])
    return SERVICES


class IndexView(View):
    def dispatch(self, request, *args, **kwargs):
        return redirect(constants.URL_PREFIX + 'alarm', service='all')


class AlarmServiceView(tables.DataTableView):
    table_class = alarm_tables.AlarmsTable
    template_name = constants.TEMPLATE_PREFIX + 'alarm.html'

    def dispatch(self, *args, **kwargs):
        self.service = kwargs['service']
        del kwargs['service']
        return super(AlarmServiceView, self).dispatch(*args, **kwargs)

    def get_data(self):
        results = []
        try:
            results = api.monitor.alarm_list(self.request)
        except Exception:
            messages.error(self.request, _("Could not retrieve alarms"))
        if self.service != 'all':
            name, value = self.service.split('=')
            filtered = []
            for row in results:
                if (name in row['metrics'][0]['dimensions'] and
                    row['metrics'][0]['dimensions'][name] == value):
                    filtered.append(row)
            results = filtered
        results.sort(key=lambda x: x['state'])
        return results

    def get_context_data(self, **kwargs):
        context = super(AlarmServiceView, self).get_context_data(**kwargs)
        context["service"] = self.service
        return context


def transform_alarm_history(results, name):
    newlist = []
    for item in results:
        temp = {}
        temp['alarm_id'] = item['alarm_id']
        temp['name'] = name
        temp['old_state'] = item['old_state']
        temp['new_state'] = item['new_state']
        temp['timestamp'] = item['timestamp']
        temp['reason'] = item['reason']
        temp['reason_data'] = item['reason_data']
        newlist.append(temp)
    return newlist


class AlarmHistoryView(tables.DataTableView):
    table_class = alarm_tables.AlarmHistoryTable
    template_name = constants.TEMPLATE_PREFIX + 'alarm_history.html'

    def dispatch(self, *args, **kwargs):
        return super(AlarmHistoryView, self).dispatch(*args, **kwargs)

    def get_data(self):
        id = self.kwargs['id']
        name = self.kwargs['name']
        results = []
        try:
            results = api.monitor.alarm_history(self.request, id)
        except Exception:
            messages.error(self.request,
                           _("Could not retrieve alarm history for %s") % id)
        return transform_alarm_history(results, name)

    def get_context_data(self, **kwargs):
        context = super(AlarmHistoryView, self).get_context_data(**kwargs)
        return context
