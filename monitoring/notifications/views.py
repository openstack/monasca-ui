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

from django.core.urlresolvers import reverse_lazy, reverse  # noqa
from django.views.generic import TemplateView

from horizon import forms

from . import forms as alarm_forms
from . import constants

LOG = logging.getLogger(__name__)


class IndexView(TemplateView):
    template_name = constants.TEMPLATE_PREFIX + 'index.html'


class NotificationCreateView(forms.ModalFormView):
    form_class = alarm_forms.CreateMethodForm
    template_name = constants.TEMPLATE_PREFIX + 'notifications/create.html'

    def get_context_data(self, **kwargs):
        context = super(NotificationCreateView, self). \
            get_context_data(**kwargs)
        context["cancel_url"] = self.get_success_url()
        action = constants.URL_PREFIX + 'notification_create'
        context["action_url"] = reverse(action)
        return context

    def get_success_url(self):
        return reverse_lazy(constants.URL_PREFIX + 'index',
                            args=(self.service,))
