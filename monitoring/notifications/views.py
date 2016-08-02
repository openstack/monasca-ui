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

import logging

from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage
from django.core.urlresolvers import reverse_lazy, reverse  # noqa
from django.utils.translation import ugettext as _  # noqa

from horizon import exceptions
from horizon import forms
from horizon import tables

from monitoring.notifications import constants
from monitoring.notifications import forms as notification_forms
from monitoring.notifications import tables as notification_tables
from monitoring import api

from openstack_dashboard import policy

LOG = logging.getLogger(__name__)
LIMIT = 10
PREV_PAGE_LIMIT = 100


class IndexView(tables.DataTableView):
    table_class = notification_tables.NotificationsTable
    template_name = constants.TEMPLATE_PREFIX + 'index.html'

    def dispatch(self, *args, **kwargs):
        return super(IndexView, self).dispatch(*args, **kwargs)

    def get_data(self):
        page_offset = self.request.GET.get('page_offset')
        results = []
        if page_offset is None:
            page_offset = 0
        try:
            results = api.monitor.notification_list(self.request, page_offset, LIMIT)
            paginator = Paginator(results, LIMIT)
            results = paginator.page(1)
        except EmptyPage:
            contacts = paginator.page(paginator.num_pages)
        except Exception:
            messages.error(self.request, _("Could not retrieve notifications"))
        return results

    def get_context_data(self, **kwargs):
        if not policy.check((('monitoring', 'monitoring:monitoring'), ), self.request):
            raise exceptions.NotAuthorized()
        context = super(IndexView, self).get_context_data(**kwargs)
        contacts = []
        results = []
        num_results = 0
        prev_page_stack = []
        page_offset = self.request.GET.get('page_offset')

        if 'prev_page_stack' in self.request.session:
            prev_page_stack = self.request.session['prev_page_stack']

        if page_offset is None:
            page_offset = 0
            prev_page_stack = []
        try:
            # To judge whether there is next page, get LIMIT + 1
            results = api.monitor.notification_list(self.request, page_offset,
                                                    LIMIT + 1)
            num_results = len(results)
            paginator = Paginator(results, LIMIT)
            contacts = paginator.page(1)
        except EmptyPage:
            contacts = paginator.page(paginator.num_pages)
        except Exception:
            messages.error(self.request, _("Could not retrieve notifications"))
            return context

        context["contacts"] = contacts

        if num_results < LIMIT + 1:
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


class NotificationCreateView(forms.ModalFormView):
    form_class = notification_forms.CreateMethodForm
    template_name = constants.TEMPLATE_PREFIX + 'create.html'
    success_url = reverse_lazy(constants.URL_PREFIX + 'index')

    def get_context_data(self, **kwargs):
        if not policy.check((('monitoring', 'monitoring:monitoring'), ), self.request):
            raise exceptions.NotAuthorized()
        context = super(NotificationCreateView, self). \
            get_context_data(**kwargs)
        context["cancel_url"] = self.get_success_url()
        action = constants.URL_PREFIX + 'notification_create'
        context["action_url"] = reverse(action)
        return context


class NotificationEditView(forms.ModalFormView):
    form_class = notification_forms.EditMethodForm
    template_name = constants.TEMPLATE_PREFIX + 'edit.html'

    def dispatch(self, *args, **kwargs):
        return super(NotificationEditView, self).dispatch(*args, **kwargs)

    def get_object(self):
        id = self.kwargs['id']
        try:
            if hasattr(self, "_object"):
                return self._object
            self._object = None
            self._object = api.monitor.notification_get(self.request, id)
            return self._object
        except Exception:
            redirect = reverse(constants.URL_PREFIX + 'index')
            exceptions.handle(self.request,
                              _('Unable to retrieve notification details.'),
                              redirect=redirect)
        return None

    def get_initial(self):
        self.notification = self.get_object()
        return self.notification

    def get_context_data(self, **kwargs):
        if not policy.check((('monitoring', 'monitoring:monitoring'), ), self.request):
            raise exceptions.NotAuthorized()
        context = super(NotificationEditView, self).get_context_data(**kwargs)
        id = self.kwargs['id']
        context["cancel_url"] = self.get_success_url()
        context["action_url"] = reverse(constants.URL_PREFIX +
                                        'notification_edit', args=(id,))
        return context

    def get_success_url(self):
        return reverse_lazy(constants.URL_PREFIX + 'index',)
