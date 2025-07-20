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

from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy

from horizon import exceptions
from horizon import tables

from monitoring import api
from monitoring.notifications import constants


class DeleteNotification(tables.DeleteAction):
    name = "delete_notification"
    verbose_name = _("Delete Notification")

    @staticmethod
    def action_present(count):
        return ngettext_lazy(
            u"Delete Notification",
            u"Delete Notifications",
            count
        )

    @staticmethod
    def action_past(count):
        return ngettext_lazy(
            u"Deleted Notification",
            u"Deleted Notifications",
            count
        )

    def allowed(self, request, datum=None):
        return True

    def delete(self, request, obj_id):
        try:
            api.monitor.notification_delete(request, obj_id)
        except Exception:
            exceptions.handle(
                request, _('Unable to delete notification.'))


class CreateNotification(tables.LinkAction):
    name = "create_notification"
    verbose_name = _("Create Notification")
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("notification", "notification:create"),)
    ajax = True

    def get_link_url(self):
        url = constants.URL_PREFIX + 'notification_create'
        return reverse(url)

    def allowed(self, request, datum=None):
        return True


class EditNotification(tables.LinkAction):
    name = "edit_notification"
    verbose_name = _("Edit Notification")
    classes = ("ajax-modal", "btn-create")

    def get_link_url(self, datum):
        return reverse(constants.URL_PREFIX + 'notification_edit',
                       args=(datum['id'], ))

    def allowed(self, request, datum=None):
        return True


class NotificationsFilterAction(tables.FilterAction):
    def filter(self, table, notifications, filter_string):
        """Naive case-insensitive search."""
        q = filter_string.lower()
        return [notif for notif in notifications
                if q in notif['name'].lower()]


class NotificationsTable(tables.DataTable):
    target = tables.Column('name', verbose_name=_('Name'))
    type = tables.Column('type', verbose_name=_('Type'))
    address = tables.Column('address', verbose_name=_('Address'))
    period = tables.Column('period', verbose_name=_('Period'))

    def get_object_id(self, obj):
        return obj['id']

    def get_object_display(self, obj):
        return obj['name']

    class Meta(object):
        name = "notifications"
        verbose_name = _("Notifications")
        row_actions = (EditNotification, DeleteNotification, )
        table_actions = (CreateNotification, NotificationsFilterAction,
                         DeleteNotification)
