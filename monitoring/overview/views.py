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
from django.http import HttpResponse  # noqa
from django.views.generic import TemplateView  # noqa
from django.utils.translation import ugettext_lazy as _  # noqa

from monitoring.overview import constants
from monitoring.alarms import tables as alarm_tables
from monitoring import api

LOG = logging.getLogger(__name__)
OVERVIEW = [
    {'name': _('OpenStack Services'),
     'groupBy': 'service'},
    {'name': _('Servers'),
     'groupBy': 'hostname'}
]

SERVICES = getattr(settings, 'MONITORING_SERVICES', OVERVIEW)


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


def show_by_dimension(data, dim_name):
    if 'dimensions' in data['metrics'][0]:
        dimensions = data['metrics'][0]['dimensions']
        if dim_name in dimensions:
            return str(data['metrics'][0]['dimensions'][dim_name])
    return ""


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
        service = alarm_tables.get_service(a)
        service_alarms = alarms_by_service.setdefault(service, [])
        service_alarms.append(a)
    for row in SERVICES:
        row['name'] = unicode(row['name'])
        if 'groupBy' in row:
            alarms_by_group = {}
            for a in alarms:
                group = show_by_dimension(a, row['groupBy'])
                if group:
                    group_alarms = alarms_by_group.setdefault(group, [])
                    group_alarms.append(a)
            services = []
            for group, group_alarms in alarms_by_group.items():
                service = {
                    'display': group,
                    'name': "%s=%s" % (row['groupBy'], group),
                    'class': get_status(group_alarms)
                }
                service['icon'] = get_icon(service['class'])
                services.append(service)
            row['services'] = services
        else:
            for service in row['services']:
                service_alarms = alarms_by_service.get(service['name'], [])
                service['class'] = get_status(service_alarms)
                service['icon'] = get_icon(service['class'])
                service['display'] = unicode(service['display'])
    return SERVICES


class IndexView(TemplateView):
    template_name = constants.TEMPLATE_PREFIX + 'index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context["token"] = self.request.user.token.id
        context["api"] = api.monitor.monasca_endpoint(self.request)
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
