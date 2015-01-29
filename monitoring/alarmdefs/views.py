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

from django.contrib import messages
from django.core.urlresolvers import reverse_lazy, reverse  # noqa
from django.utils.translation import ugettext as _  # noqa
from django.views.generic import TemplateView  # noqa

from horizon import exceptions
from horizon import forms
from horizon import tables

import monascaclient.exc as exc
from monitoring.alarmdefs import constants
from monitoring.alarmdefs import forms as alarm_forms
from monitoring.alarmdefs import tables as alarm_tables
from monitoring import api

class IndexView(tables.DataTableView):
    table_class = alarm_tables.AlarmsTable
    template_name = constants.TEMPLATE_PREFIX + 'alarm.html'

    def get_data(self):
        results = []
        try:
            results = api.monitor.alarmdef_list(self.request)
        except Exception:
            messages.error(self.request, _("Could not retrieve alarm definitions"))
        return results


class AlarmCreateView(forms.ModalFormView):
    form_class = alarm_forms.CreateAlarmForm
    template_name = constants.TEMPLATE_PREFIX + 'create.html'

    def get_context_data(self, **kwargs):
        context = super(AlarmCreateView, self).get_context_data(**kwargs)
        context["cancel_url"] = self.get_success_url()
        context["action_url"] = reverse(constants.URL_PREFIX + 'alarm_create',
                                        args=())
        metrics = api.monitor.metrics_list(self.request)

        context["metrics"] = json.dumps(metrics)
        return context

    def get_success_url(self):
        return reverse_lazy(constants.URL_PREFIX + 'index',
                            args=())


def transform_alarm_data(obj):
    obj['apply_to'] = '1' if obj['match_by'] else '2'
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
            for id in self._object["alarm_actions"]:
                try:
                    notification = api.monitor.notification_get(
                        self.request,
                        id)
                    notifications.append(notification)
                # except exceptions.NOT_FOUND:
                except exc.HTTPException:
                    msg = _("Notification %s has already been deleted.") % id
                    notifications.append({"id": id,
                                          "name": unicode(msg),
                                          "type": "",
                                          "address": ""})
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
            for id in self._object["alarm_actions"]:
                try:
                    notification = api.monitor.notification_get(
                        self.request,
                        id)
                    notifications.append(notification)
                # except exceptions.NOT_FOUND:
                except exc.HTTPException:
                    msg = _("Notification %s has already been deleted.") % id
                    messages.warning(self.request, msg)
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
        context = super(AlarmEditView, self).get_context_data(**kwargs)
        id = self.kwargs['id']
        context["cancel_url"] = self.get_success_url()
        context["action_url"] = reverse(constants.URL_PREFIX + 'alarm_edit',
                                        args=(id,))
        return context

    def get_success_url(self):
        return reverse_lazy(constants.URL_PREFIX + 'index',
                            args=())
