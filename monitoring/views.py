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

from django.http import HttpResponse   # noqa
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from horizon import tables
from .tables import AlertsTable
from .tables import AlertHistoryTable
from openstack_dashboard import api

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
    template_name = 'admin/monitoring/index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context["date"] = datetime.datetime.utcnow()
        context["service_groups"] = SAMPLE

        return context


class StatusView(TemplateView):
    template_name = "admin/metering/samples.csv"

    def get(self, request, *args, **kwargs):
        services = ['MaaS',
                    ]
        #api.monitoring.alarm_list(self.request)
        for group in SAMPLE:
            for service in group['services']:
                service['class'] = get_random_status()
        ret = {}
        ret['series'] = SAMPLE
        ret['settings'] = {}

        return HttpResponse(json.dumps(ret),
            content_type='application/json')

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


class AlertView(tables.DataTableView):
    table_class = AlertsTable
    template_name = 'admin/monitoring/alert.html'

    def dispatch(self, *args, **kwargs):
        self.service = kwargs['service']
        del kwargs['service']
        return super(AlertView, self).dispatch(*args, **kwargs)

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
        context = super(AlertView, self).get_context_data(**kwargs)
        context["service"] = self.service
        return context


class AlertHistoryView(tables.DataTableView):
    table_class = AlertHistoryTable
    template_name = 'admin/monitoring/alert_history.html'

    def dispatch(self, *args, **kwargs):
        self.service = kwargs['service']
        del kwargs['service']
        return super(AlertHistoryView, self).dispatch(*args, **kwargs)

    def get_data(self):
        results = [
            {'Host': 'Compute1', 'Service': 'Nova', 'Status': 'CRITICAL', 'Last_Check': 'Feb 12 2014 2:34 CST', 'Status_Information': 'API Response Time'},
            {'Host': 'Compute1', 'Service': 'Nova', 'Status': 'OK', 'Last_Check': 'Feb 12 2014 2:45 CST', 'Status_Information': 'API Response Time'},
            {'Host': 'Compute1', 'Service': 'Nova', 'Status': 'WARNING', 'Last_Check': 'April 18 2014 8:45 CST', 'Status_Information': 'API Response Time'}
        ]

        return results

    def get_context_data(self, **kwargs):
        context = super(AlertHistoryView, self).get_context_data(**kwargs)
        context["service"] = self.service
        return context


class AlertMeterView(TemplateView):
    template_name = 'admin/monitoring/alert_meter.html'
