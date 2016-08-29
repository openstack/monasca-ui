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
#    under the License.

import base64
import copy
import json
import logging
import urllib
import urllib2

from django import http
from django.contrib import messages
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponse  # noqa
from django.utils.translation import ugettext_lazy as _  # noqa
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView  # noqa
from openstack_auth import utils as auth_utils
from openstack_dashboard import policy

from horizon import exceptions

from monitoring import api
from monitoring.alarms import tables as alarm_tables
from monitoring.config import local_settings as settings
from monitoring.overview import constants

LOG = logging.getLogger(__name__)


STATUS_FA_ICON_MAP = {'btn-success': "fa-check",
                      'btn-danger': "fa-exclamation-triangle",
                      'btn-warning': "fa-exclamation",
                      'btn-default': "fa-question-circle"}


def get_icon(status):
    return STATUS_FA_ICON_MAP.get(status,  "fa-question-circle")


priorities = [
    {'status': 'btn-success', 'severity': 'OK'},
    {'status': 'btn-default', 'severity': 'UNDETERMINED'},
    {'status': 'btn-warning', 'severity': 'LOW'},
    {'status': 'btn-warning', 'severity': 'MEDIUM'},
    {'status': 'btn-warning', 'severity': 'HIGH'},
    {'status': 'btn-danger', 'severity': 'CRITICAL'},
]
index_by_severity = {d['severity']: i for i, d in enumerate(priorities)}


def get_dashboard_links(request):
    #
    # GRAFANA_LINKS is a list of dictionaries, but can either
    # be a nested list of dictionaries indexed by project name
    # (or '*'), or simply the list of links to display.  This
    # code is a bit more complicated as a result but will allow
    # for backward compatibility and ensure existing installations
    # that don't take advantage of project specific dashboard
    # links are unaffected.  The 'non_project_keys' are the
    # expected dictionary keys for the list of dashboard links,
    # so if we encounter one of those, we know we're supporting
    # legacy/non-project specific behavior.
    #
    # See examples of both in local_settings.py
    #
    non_project_keys = {'fileName', 'title'}
    try:
        for project_link in settings.DASHBOARDS:
            key = project_link.keys()[0]
            value = project_link.values()[0]
            if key in non_project_keys:
                #
                # we're not indexed by project, just return
                # the whole list.
                #
                return settings.DASHBOARDS
            elif key == request.user.project_name:
                #
                # we match this project, return the project
                # specific links.
                #
                return value
            elif key == '*':
                #
                # this is a global setting, squirrel it away
                # in case we exhaust the list without a project
                # match
                #
                return value
        return settings.DEFAULT_LINKS
    except Exception:
        LOG.warn("Failed to parse dashboard links by project, returning defaults.")
        pass
    #
    # Extra safety here -- should have got a match somewhere above,
    # but fall back to defaults.
    #
    return settings.DASHBOARDS


def get_monitoring_services(request):
    #
    # GRAFANA_LINKS is a list of dictionaries, but can either
    # be a nested list of dictionaries indexed by project name
    # (or '*'), or simply the list of links to display.  This
    # code is a bit more complicated as a result but will allow
    # for backward compatibility and ensure existing installations
    # that don't take advantage of project specific dashboard
    # links are unaffected.  The 'non_project_keys' are the
    # expected dictionary keys for the list of dashboard links,
    # so if we encounter one of those, we know we're supporting
    # legacy/non-project specific behavior.
    #
    # See examples of both in local_settings.py
    #
    non_project_keys = {'name', 'groupBy'}
    try:
        for group in settings.MONITORING_SERVICES:
            key = group.keys()[0]
            value = group.values()[0]
            if key in non_project_keys:
                #
                # we're not indexed by project, just return
                # the whole list.
                #
                return settings.MONITORING_SERVICES
            elif key == request.user.project_name:
                #
                # we match this project, return the project
                # specific links.
                #
                return value
            elif key == '*':
                #
                # this is a global setting, squirrel it away
                # in case we exhaust the list without a project
                # match
                #
                return value
        return settings.MONITORING_SERVICES
    except Exception:
        LOG.warn("Failed to parse monitoring services by project, returning defaults.")
        pass
    #
    # Extra safety here -- should have got a match somewhere above,
    # but fall back to defaults.
    #
    return settings.MONITORING_SERVICES


def show_by_dimension(data, dim_name):
    if 'dimensions' in data['metrics'][0]:
        dimensions = data['metrics'][0]['dimensions']
        if dim_name in dimensions:
            return str(data['metrics'][0]['dimensions'][dim_name].encode('utf-8'))
    return ""


def get_status(alarms):
    if not alarms:
        return 'chicklet-notfound'
    status_index = 0
    for a in alarms:
        severity = alarm_tables.show_severity(a)
        severity_index = index_by_severity.get(severity, None)
        status_index = max(status_index, severity_index)
    return priorities[status_index]['status']


def generate_status(request):
    try:
        alarms = api.monitor.alarm_list(request)
    except Exception as e:
        messages.error(request,
                       _('Unable to list alarms: %s') % str(e))
        alarms = []
    alarms_by_service = {}
    for a in alarms:
        service = alarm_tables.get_service(a)
        service_alarms = alarms_by_service.setdefault(service, [])
        service_alarms.append(a)
    monitoring_services = copy.deepcopy(get_monitoring_services(request))
    for row in monitoring_services:
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
                name = '%s=%s' % (row['groupBy'], group)
                # Encode as base64url to be able to include '/'
                name = 'b64:' + base64.urlsafe_b64encode(name)
                service = {
                    'display': group,
                    'name': name,
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
    return monitoring_services


class IndexView(TemplateView):
    template_name = constants.TEMPLATE_PREFIX + 'index.html'

    def get_context_data(self, **kwargs):
        if not policy.check((('monitoring', 'monitoring:monitoring'), ), self.request):
            raise exceptions.NotAuthorized()
        context = super(IndexView, self).get_context_data(**kwargs)
        try:
            region = self.request.user.services_region
            context["grafana_url"] = getattr(settings, 'GRAFANA_URL').get(region, '')
        except AttributeError:
            # Catches case where Grafana 2 is not enabled.
            proxy_url_path = str(reverse_lazy(constants.URL_PREFIX + 'proxy'))
            api_root = self.request.build_absolute_uri(proxy_url_path)
            context["api"] = api_root
        context["dashboards"] = get_dashboard_links(self.request)
        context['can_access_logs'] = policy.check(
            (('identity', 'admin_required'), ), self.request
        )
        context['enable_kibana_button'] = settings.ENABLE_KIBANA_BUTTON
        return context


class MonascaProxyView(TemplateView):
    template_name = ""

    def _convert_dimensions(self, req_kwargs):
        """this method converts the dimension string
        service:monitoring  (requested by a query string arg)
        into a python dict that looks like
        {"service": "monitoring"} (used by monasca api calls)
        """
        dim_dict = {}
        if 'dimensions' in req_kwargs:
            dimensions_str = req_kwargs['dimensions'][0]
            dimensions_str_array = dimensions_str.split(',')
            for dimension in dimensions_str_array:
                dimension_name_value = dimension.split(':')
                if len(dimension_name_value) == 2:
                    name = dimension_name_value[0].encode('utf8')
                    value = dimension_name_value[1].encode('utf8')
                    dim_dict[name] = urllib.unquote(value)
                else:
                    raise Exception('Dimensions are malformed')

            #
            # If the request specifies 'INJECT_REGION' as the region, we'll
            # replace with the horizon scoped region.  We can't do this by
            # default, since some implementations don't publish region as a
            # dimension for all metrics (mini-mon for one).
            #
            if 'region' in dim_dict and dim_dict['region'] == 'INJECT_REGION':
                dim_dict['region'] = self.request.user.services_region
            req_kwargs['dimensions'] = dim_dict

        return req_kwargs

    def get(self, request, *args, **kwargs):
        # monasca_endpoint = api.monitor.monasca_endpoint(self.request)
        restpath = self.kwargs['restpath']

        results = None
        parts = restpath.split('/')
        if "metrics" == parts[0]:
            req_kwargs = dict(self.request.GET)
            self._convert_dimensions(req_kwargs)
            if len(parts) == 1:
                results = {'elements': api.monitor.
                           metrics_list(request,
                                        **req_kwargs)}
            elif "statistics" == parts[1]:
                results = {'elements': api.monitor.
                           metrics_stat_list(request,
                                             **req_kwargs)}
            elif "measurements" == parts[1]:
                results = {'elements': api.monitor.
                           metrics_measurement_list(request,
                                                    **req_kwargs)}
        if not results:
            LOG.warn("There was a request made for the path %s that"
                     " is not supported." % restpath)
            results = {}
        return HttpResponse(json.dumps(results),
                            content_type='application/json')


class StatusView(TemplateView):
    template_name = ""

    def get(self, request, *args, **kwargs):
        ret = {
            'series': generate_status(self.request),
            'settings': {}
        }

        return HttpResponse(json.dumps(ret),
                            content_type='application/json')


class _HttpMethodRequest(urllib2.Request):

    def __init__(self, method, url, **kwargs):
        urllib2.Request.__init__(self, url, **kwargs)
        self.method = method

    def get_method(self):
        return self.method


def proxy_stream_generator(response):
    while True:
        chunk = response.read(1000 * 1024)
        if not chunk:
            break
        yield chunk


class KibanaProxyView(generic.View):

    base_url = None
    http_method_names = ['GET', 'POST', 'PUT', 'DELETE', 'HEAD']

    def read(self, method, url, data, headers):

        proxy_request_url = self.get_absolute_url(url)
        proxy_request = _HttpMethodRequest(
            method, proxy_request_url, data=data, headers=headers
        )
        try:
            response = urllib2.urlopen(proxy_request)

        except urllib2.HTTPError as e:
            return http.HttpResponse(
                e.read(),
                status=e.code,
                content_type=e.hdrs['content-type']
            )
        except urllib2.URLError as e:
            return http.HttpResponse(e.reason, 404)

        else:
            status = response.getcode()
            return http.StreamingHttpResponse(
                proxy_stream_generator(response),
                status=status,
                content_type=response.headers['content-type']
            )

    @csrf_exempt
    def dispatch(self, request, url):
        if not url:
            url = '/'

        if request.method not in self.http_method_names:
            return http.HttpResponseNotAllowed(request.method)

        if not self._can_access_kibana():
            error_msg = (_('User %s does not have sufficient '
                           'privileges to access Kibana')
                         % auth_utils.get_user(request))
            LOG.error(error_msg)
            return http.HttpResponseForbidden(content=error_msg)

        # passing kbn version explicitly for kibana >= 4.3.x
        headers = {
            'X-Auth-Token': request.user.token.id,
            'kbn-version': request.META.get('HTTP_KBN_VERSION', '')
        }

        return self.read(request.method, url, request.body, headers)

    def get_relative_url(self, url):
        url = urllib.quote(url.encode('utf-8'))
        params_str = self.request.GET.urlencode()

        if params_str:
            return '{0}?{1}'.format(url, params_str)
        return url

    def get_absolute_url(self, url):
        return self.base_url + self.get_relative_url(url).lstrip('/')

    def _can_access_kibana(self):
        return policy.check(
            (('identity', 'admin_required'),), self.request
        )
