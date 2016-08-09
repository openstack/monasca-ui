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

from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage
from django.core.urlresolvers import reverse_lazy, reverse  # noqa
from django.utils.translation import ugettext as _  # noqa
from django.views.generic import TemplateView  # noqa

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon.utils import functions as utils
from horizon import workflows

import monascaclient.exc as exc
from monitoring.alarmdefs import constants
from monitoring.alarmdefs import forms as alarm_forms
from monitoring.alarmdefs import tables as alarm_tables
from monitoring.alarmdefs import workflows as alarm_workflows
from monitoring import api

from openstack_dashboard import policy


PREV_PAGE_LIMIT = 100


class IndexView(tables.DataTableView):
    table_class = alarm_tables.AlarmsTable
    template_name = constants.TEMPLATE_PREFIX + 'alarm.html'

    def get_data(self):
        page_offset = self.request.GET.get('page_offset')
        results = []
        if page_offset is None:
            page_offset = 0
        limit = utils.get_page_size(self.request)    
        try:
            results = api.monitor.alarmdef_list(self.request, page_offset, limit)
            paginator = Paginator(results, limit)
            results = paginator.page(1)
        except EmptyPage:
            contacts = paginator.page(paginator.num_pages)
        except Exception:
            messages.error(self.request, _("Could not retrieve alarm definitions"))

        return results

    def get_context_data(self, **kwargs):
        if not policy.check((('monitoring', 'monitoring:monitoring'), ), self.request):
            raise exceptions.NotAuthorized()
        context = super(IndexView, self).get_context_data(**kwargs)
        num_results = 0
        contacts = []
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
        try:
            # To judge whether there is next page, get limit + 1
            results = api.monitor.alarmdef_list(self.request, page_offset,
                                                limit + 1)
            num_results = len(results)
            paginator = Paginator(results, limit)
            contacts = paginator.page(1)
        except EmptyPage:
            contacts = paginator.page(paginator.num_pages)
        except Exception:
            messages.error(self.request, _("Could not retrieve alarm definitions"))
            return context

        context["contacts"] = contacts

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


class AlarmCreateView(workflows.WorkflowView):
    workflow_class = alarm_workflows.AlarmDefinitionWorkflow


def transform_alarm_data(obj):
    obj['match_by'] = ','.join(obj['match_by'])
    return obj


class AlarmDetailView(TemplateView):
    template_name = constants.TEMPLATE_PREFIX + 'detail.html'

    def get_object(self):
        id = self.kwargs['id']
        try:
            if hasattr(self, "_object"):
                return self._object
            self._object = None
            self._object = api.monitor.alarmdef_get(self.request, id)
            notifications = []
            # Fetch the notification object for each alarm_actions
            all_actions = set(self._object["alarm_actions"] +
                              self._object["ok_actions"] +
                              self._object["undetermined_actions"])
            for id in all_actions:
                try:
                    notification = api.monitor.notification_get(
                        self.request,
                        id)
                    notification['alarm'] = False
                    notification['ok'] = False
                    notification['undetermined'] = False
                    notifications.append(notification)
                # except exceptions.NOT_FOUND:
                except exc.HTTPException:
                    msg = _("Notification %s has already been deleted.") % id
                    notifications.append({"id": id,
                                          "name": unicode(msg),
                                          "type": "",
                                          "address": ""})

            for notification in notifications:
                if notification['id'] in self._object["alarm_actions"]:
                    notification['alarm'] = True
                if notification['id'] in self._object["ok_actions"]:
                    notification['ok'] = True
                if notification['id'] in self._object["undetermined_actions"]:
                    notification['undetermined'] = True

            self._object["notifications"] = notifications
            return self._object
        except Exception:
            redirect = self.get_success_url()
            exceptions.handle(self.request,
                              _('Unable to retrieve alarm details.'),
                              redirect=redirect)
        return None

    def get_initial(self):
        self.alarm = self.get_object()
        return transform_alarm_data(self.alarm)

    def get_context_data(self, **kwargs):
        if not policy.check((('monitoring', 'monitoring:monitoring'), ), self.request):
            raise exceptions.NotAuthorized()
        context = super(AlarmDetailView, self).get_context_data(**kwargs)
        self.get_initial()
        context["alarm"] = self.alarm
        context["cancel_url"] = self.get_success_url()
        return context

    def get_success_url(self):
        return reverse_lazy(constants.URL_PREFIX + 'index')


class AlarmEditView(forms.ModalFormView):
    form_class = alarm_forms.EditAlarmForm
    template_name = constants.TEMPLATE_PREFIX + 'edit.html'

    def get_object(self):
        id = self.kwargs['id']
        try:
            if hasattr(self, "_object"):
                return self._object
            self._object = None
            self._object = api.monitor.alarmdef_get(self.request, id)
            notifications = []
            # Fetch the notification object for each alarm_actions
            all_actions = set(self._object["alarm_actions"] +
                              self._object["ok_actions"] +
                              self._object["undetermined_actions"])
            for id in all_actions:
                try:
                    notification = api.monitor.notification_get(
                        self.request,
                        id)
                    notification['alarm'] = False
                    notification['ok'] = False
                    notification['undetermined'] = False
                    notifications.append(notification)
                # except exceptions.NOT_FOUND:
                except exc.HTTPException:
                    msg = _("Notification %s has already been deleted.") % id
                    messages.warning(self.request, msg)

            for notification in notifications:
                if notification['id'] in self._object["alarm_actions"]:
                    notification['alarm'] = True
                if notification['id'] in self._object["ok_actions"]:
                    notification['ok'] = True
                if notification['id'] in self._object["undetermined_actions"]:
                    notification['undetermined'] = True

            del self._object["alarm_actions"]
            del self._object["ok_actions"]
            del self._object["undetermined_actions"]

            self._object["notifications"] = notifications
            return self._object
        except Exception:
            redirect = self.get_success_url()
            exceptions.handle(self.request,
                              _('Unable to retrieve alarm details.'),
                              redirect=redirect)
        return None

    def get_initial(self):
        self.alarm = self.get_object()
        return transform_alarm_data(self.alarm)

    def get_context_data(self, **kwargs):
        if not policy.check((('monitoring', 'monitoring:monitoring'), ), self.request):
            raise exceptions.NotAuthorized()
        context = super(AlarmEditView, self).get_context_data(**kwargs)
        id = self.kwargs['id']
        context["cancel_url"] = self.get_success_url()
        context["action_url"] = reverse(constants.URL_PREFIX + 'alarm_edit',
                                        args=(id,))
        return context

    def get_success_url(self):
        return reverse_lazy(constants.URL_PREFIX + 'index',
                            args=())
