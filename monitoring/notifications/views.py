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

import logging

from django.contrib import messages
from django.core.urlresolvers import reverse_lazy, reverse  # noqa
from django.views.generic import TemplateView

from horizon import forms
from horizon import tables

from . import forms as alarm_forms
from . import constants

from monitoring import api
from .tables import NotificationsTable

LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = NotificationsTable
    template_name = constants.TEMPLATE_PREFIX + 'index.html'

    def dispatch(self, *args, **kwargs):
        return super(IndexView, self).dispatch(*args, **kwargs)

    def get_data(self):
        results = []
        try:
            results = api.monitor.notification_list(self.request)
        except:
            messages.error(self.request, _("Could not retrieve notifications"))
        return results

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        return context


class NotificationCreateView(forms.ModalFormView):
    form_class = alarm_forms.CreateMethodForm
    template_name = constants.TEMPLATE_PREFIX + 'create.html'
    success_url = reverse_lazy(constants.URL_PREFIX + 'index')

    def get_context_data(self, **kwargs):
        context = super(NotificationCreateView, self). \
            get_context_data(**kwargs)
        context["cancel_url"] = self.get_success_url()
        action = constants.URL_PREFIX + 'notification_create'
        context["action_url"] = reverse(action)
        return context
