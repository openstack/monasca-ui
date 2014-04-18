import logging

from datetime import datetime

from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView

from horizon import tables
from .tables import AlertsTable, AlertHistoryTable

LOG = logging.getLogger(__name__)


class IndexView(TemplateView):
    template_name = 'admin/monitoring/index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context["date"] = datetime.utcnow()
        context["service_groups"] = [{'name': _('Platform Services'),
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

        return context


class AlertView(tables.DataTableView):
    table_class = AlertsTable
    template_name = 'admin/monitoring/alert.html'

    def dispatch(self, *args, **kwargs):
        self.service = kwargs['service']
        del kwargs['service']
        return super(AlertView, self).dispatch(*args, **kwargs)

    def get_data(self):
        results = [{'Host': 'Compute1', 'Service': 'Nova', 'Status': 'WARNING', 'Status_Information': 'API Response Time'},
                   {'Host': 'Compute2', 'Service': 'Nova', 'Status': 'OK', 'Status_Information': 'System Health'},
                   {'Host': 'Compute3', 'Service': 'Nova', 'Status': 'OK', 'Status_Information': 'Database Access'},
                   {'Host': 'Compute4', 'Service': 'Nova', 'Status': 'OK', 'Status_Information': 'Network Latency'},
                   {'Host': 'Compute5', 'Service': 'Nova', 'Status': 'OK', 'Status_Information': 'Rabbit Health'},
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
