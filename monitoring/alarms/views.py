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
from datetime import timedelta
import logging

from django.conf import settings  # noqa
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage
from django.core.urlresolvers import reverse_lazy, reverse  # noqa
from django.shortcuts import redirect
from django.utils.dateparse import parse_datetime
from django.utils.translation import ugettext as _  # noqa
from django.utils.translation import ugettext_lazy
from django.views.generic import View  # noqa

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon.utils import functions as utils

from monitoring.alarms import constants
from monitoring.alarms import forms as alarm_forms
from monitoring.alarms import tables as alarm_tables
from monitoring import api

from openstack_dashboard import policy

LOG = logging.getLogger(__name__)
SERVICES = getattr(settings, 'MONITORING_SERVICES', [])

PREV_PAGE_LIMIT = 100


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

alarm_history_default_ts_format = 'utc'
alarm_history_ts_formats = (
    ('utc', ugettext_lazy('UTC'),),
    ('bl', ugettext_lazy('Browser local'),),
)

default_service = 'all'


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

        if 'service' in kwargs:
            self.service = kwargs['service']
            del kwargs['service']
        else:
            self.service = default_service

        return super(AlarmServiceView, self).dispatch(*args, **kwargs)

    def get_data(self):
        page_offset = self.request.GET.get('page_offset')
        contacts = []

        if page_offset is None:
            page_offset = 0

        limit = utils.get_page_size(self.request)
        if self.service == default_service:
            try:
                results = api.monitor.alarm_list(self.request, page_offset,
                                                 limit)
                paginator = Paginator(results, limit)
                contacts = paginator.page(1)
            except EmptyPage:
                contacts = paginator.page(paginator.num_pages)
            except Exception:
                messages.error(self.request, _("Could not retrieve alarms"))
            return contacts
        else:
            if self.service[:2] == 'id':
                try:
                    name, value = self.service.split("=")
                    results = [api.monitor.alarm_show(self.request, value)]
                except Exception as e:
                    messages.error(self.request, _("Could not retrieve alarms"))
                    results = []
                    print "ERROR"
                    print e
                return results
            else:
                try:
                    if self.service[:3] == 'b64':
                        name, value = self.service.split(":")
                        self.service = base64.urlsafe_b64decode(str(value))
                    results = api.monitor.alarm_list_by_dimension(self.request,
                                                                  self.service,
                                                                  page_offset,
                                                                  limit)
                except Exception:
                    messages.error(self.request, _("Could not retrieve alarms"))
                    results = []
                return results

    def get_context_data(self, **kwargs):
        if not policy.check((('monitoring', 'monitoring:monitoring'), ), self.request):
            raise exceptions.NotAuthorized()
        context = super(AlarmServiceView, self).get_context_data(**kwargs)
        results = []
        num_results = 0  # make sure variable is set
        prev_page_stack = []
        page_offset = self.request.GET.get('page_offset')

        if 'prev_page_stack' in self.request.session:
            prev_page_stack = self.request.session['prev_page_stack']

        if page_offset is None:
            page_offset = 0
            prev_page_stack = []
        else:
            page_offset = int(page_offset)
        limit = utils.get_page_size(self.request)
        if self.service == 'all':
            try:
                # To judge whether there is next page, get limit + 1
                results = api.monitor.alarm_list(self.request, page_offset,
                                                 limit + 1)
                num_results = len(results)
                paginator = Paginator(results, limit)
                results = paginator.page(1)
            except EmptyPage:
                results = paginator.page(paginator.num_pages)
            except Exception:
                messages.error(self.request, _("Could not retrieve alarms"))
        else:
            if self.service[:2] == 'id':
                try:
                    name, value = self.service.split("=")
                    results = [api.monitor.alarm_show(self.request, value)]
                except Exception as e:
                    messages.error(self.request, _("Could not retrieve alarms"))
                    results = []
            else:
                try:
                    # To judge whether there is next page, get limit + 1
                    results = api.monitor.alarm_list_by_dimension(self.request,
                                                                  self.service,
                                                                  page_offset,
                                                                  limit + 1)
                    num_results = len(results)
                    paginator = Paginator(results, limit)
                    results = paginator.page(1)
                except EmptyPage:
                    results = paginator.page(paginator.num_pages)
                except Exception:
                    messages.error(self.request, _("Could not retrieve alarms"))
                    results = []

        context["contacts"] = results
        context["service"] = self.service

        if num_results < limit + 1:
            context["page_offset"] = None
        else:
            context["page_offset"] = page_offset + limit

        if page_offset in prev_page_stack:
            index = prev_page_stack.index(page_offset)
            prev_page_stack = prev_page_stack[0:index]

        prev_page_offset = prev_page_stack[-1] if prev_page_stack else None
        if prev_page_offset is not None:
            context["prev_page_offset"] = prev_page_offset

        if len(prev_page_stack) > PREV_PAGE_LIMIT:
            del prev_page_stack[0]
        prev_page_stack.append(page_offset)
        self.request.session['prev_page_stack'] = prev_page_stack

        return context


def transform_alarm_history(results, name, ts_mode, ts_offset):
    new_list = []

    def get_ts_val(val):
        if ts_mode == 'bl':
            offset = int((ts_offset or '0').replace('+', ''))
            dt_val = parse_datetime(val) + timedelta(hours=offset)
            dt_val_formatter = dt_val.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            return dt_val_formatter.replace('000Z', '')
        elif ts_mode != 'utc':
            raise ValueError('%s is not supported timestamp format' % ts_mode)
        else:
            return val  # utc case

    for item in results:
        new_list.append({'alarm_id': item['alarm_id'],
                         'name': name,
                         'old_state': item['old_state'],
                         'new_state': item['new_state'],
                         'timestamp': get_ts_val(item['timestamp']),
                         'reason': item['reason'],
                         'metrics': item['metrics'],
                         'reason_data': item['reason_data']})
    return new_list


class AlarmHistoryView(tables.DataTableView):
    table_class = alarm_tables.AlarmHistoryTable
    template_name = constants.TEMPLATE_PREFIX + 'alarm_history.html'

    def dispatch(self, *args, **kwargs):
        return super(AlarmHistoryView, self).dispatch(*args, **kwargs)

    def get_data(self):
        page_offset = self.request.GET.get('page_offset')
        ts_mode = self.request.GET.get('ts_mode')
        ts_offset = self.request.GET.get('ts_offset')

        contacts = []
        object_id = self.kwargs['id']
        name = self.kwargs['name']

        if not ts_mode:
            ts_mode = alarm_history_default_ts_format
        if not page_offset:
            page_offset = 0
        limit = utils.get_page_size(self.request)
        try:
            results = api.monitor.alarm_history(self.request,
                                                object_id,
                                                page_offset,
                                                limit)
            paginator = Paginator(results, limit)
            contacts = paginator.page(1)
        except EmptyPage:
            contacts = paginator.page(paginator.num_pages)
        except Exception:
            messages.error(self.request,
                           _("Could not retrieve alarm history for %s") % object_id)

        try:
            return transform_alarm_history(contacts, name, ts_mode, ts_offset)
        except ValueError as err:
            LOG.warning('Failed to transform alarm history due to %s' %
                        err.message)
            messages.warning(self.request, _('Failed to present alarm '
                                             'history'))
        return []

    def get_context_data(self, **kwargs):
        if not policy.check((('monitoring', 'monitoring:monitoring'), ), self.request):
            raise exceptions.NotAuthorized()
        context = super(AlarmHistoryView, self).get_context_data(**kwargs)

        object_id = kwargs['id']
        ts_mode = self.request.GET.get('ts_mode')
        ts_offset = self.request.GET.get('ts_offset')

        try:
            alarm = api.monitor.alarm_get(self.request, object_id)
        except Exception:
            messages.error(self.request,
                           _("Could not retrieve alarm for %s") % object_id)
        context['alarm'] = alarm

        num_results = 0
        contacts = []
        prev_page_stack = []
        page_offset = self.request.GET.get('page_offset')
        limit = utils.get_page_size(self.request)
        if 'prev_page_stack' in self.request.session:
            prev_page_stack = self.request.session['prev_page_stack']

        if page_offset is None:
            page_offset = 0
            prev_page_stack = []
        try:
            # To judge whether there is next page, get limit + 1
            results = api.monitor.alarm_history(self.request, object_id, page_offset,
                                                limit + 1)
            num_results = len(results)
            paginator = Paginator(results, limit)
            contacts = paginator.page(1)
        except EmptyPage:
            contacts = paginator.page(paginator.num_pages)
        except Exception:
            messages.error(self.request,
                           _("Could not retrieve alarm history for %s") % object_id)
            return context

        context["contacts"] = contacts
        context['timestamp_formats'] = alarm_history_ts_formats
        context['timestamp_selected'] = ts_mode or ''
        context['timestamp_offset'] = ts_offset or 0

        if num_results < limit + 1:
            context["page_offset"] = None
        else:
            context["page_offset"] = contacts.object_list[-1]["id"]

        if page_offset in prev_page_stack:
            index = prev_page_stack.index(page_offset)
            prev_page_stack = prev_page_stack[0:index]

        prev_page_offset = prev_page_stack[-1] if prev_page_stack else None
        if prev_page_offset is not None:
            context["prev_page_offset"] = prev_page_offset

        if len(prev_page_stack) > PREV_PAGE_LIMIT:
            del prev_page_stack[0]
        prev_page_stack.append(str(page_offset))
        self.request.session['prev_page_stack'] = prev_page_stack

        return context


class AlarmFilterView(forms.ModalFormView):
    template_name = constants.TEMPLATE_PREFIX + 'filter.html'
    form_class = alarm_forms.CreateAlarmForm

    def get_context_data(self, **kwargs):
        if not policy.check((('monitoring', 'monitoring:monitoring'), ), self.request):
            raise exceptions.NotAuthorized()
        context = super(AlarmFilterView, self).get_context_data(**kwargs)
        context["cancel_url"] = self.get_success_url()
        context["action_url"] = reverse(constants.URL_PREFIX + 'alarm_filter',
                                        args=())
        context["alarm_url"] = reverse_lazy(constants.URL_PREFIX + 'alarm_all',
                                            args=())
        return context

    def get_success_url(self):
        return reverse_lazy(constants.URL_PREFIX + 'index',
                            args=())
