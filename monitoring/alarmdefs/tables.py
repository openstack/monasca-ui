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

from horizon import tables

from monitoring.alarmdefs import constants
from monitoring import api


class CreateAlarm(tables.LinkAction):
    name = "create_alarm"
    verbose_name = _("Create Alarm Definition")
    classes = ("ajax-modal", "btn-create")
    icon = "plus"
    policy_rules = (("alarm", "alarm:create"),)
    ajax = True

    def get_link_url(self):
        return reverse(constants.URL_PREFIX + 'alarm_create', args=())

    def allowed(self, request, datum=None):
        return True


class EditAlarm(tables.LinkAction):
    name = "edit_alarm"
    verbose_name = _("Edit Alarm Definition")
    classes = ("ajax-modal", "btn-create")

    def get_link_url(self, datum):
        return reverse(constants.URL_PREFIX + 'alarm_edit', args=(datum['id'], ))

    def allowed(self, request, datum=None):
        return True


class DeleteAlarm(tables.DeleteAction):
    name = "delete_alarm"
    verbose_name = _("Delete Alarm Definition")

    @staticmethod
    def action_present(count):
        return ngettext_lazy(
            u"Delete Alarm Definition",
            u"Delete Alarm Definitions",
            count
        )

    @staticmethod
    def action_past(count):
        return ngettext_lazy(
            u"Deleted Alarm Definition",
            u"Deleted Alarm Definitions",
            count
        )

    def allowed(self, request, datum=None):
        return True

    def delete(self, request, obj_id):
        api.monitor.alarmdef_delete(request, obj_id)


class AlarmsFilterAction(tables.FilterAction):
    def filter(self, table, alarms, filter_string):
        """Naive case-insensitive search."""
        q = filter_string.lower()
        return [alarm for alarm in alarms
                if q in alarm['name'].lower()]


class AlarmsTable(tables.DataTable):
    target = tables.Column('name', verbose_name=_('Name'),
                           link=constants.URL_PREFIX + 'alarm_detail',
                           )
    description = tables.Column('description', verbose_name=_('Description'))
    enabled = tables.Column('actions_enabled',
                            verbose_name=_('Notifications Enabled'))

    def get_object_id(self, obj):
        return obj['id']

    def get_object_display(self, obj):
        return obj['name']

    class Meta(object):
        name = "alarms"
        verbose_name = _("Alarm Definitions")
        row_actions = (EditAlarm,
                       DeleteAlarm,
                       )
        table_actions = (CreateAlarm,
                         AlarmsFilterAction,
                         DeleteAlarm,
                         )
