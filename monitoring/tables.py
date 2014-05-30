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

from django import template
from django.utils.translation import ugettext_lazy as _

from horizon import tables

from . import constants
from monitoring import api

LOG = logging.getLogger(__name__)


STATUS = ["OK", "WARNING", "CRITICAL", "UNKNOWN"]


def get_status(index):
    if index < len(STATUS):
        return STATUS[index]
    else:
        return "UNKNOWN: %d" % index


def show_status(data):
    status = data
    img_tag = '<img src="%s" title="%s"/>'
    if status == 'CRITICAL':
        return img_tag % (constants.CRITICAL_ICON, status)
    if status in ('LOW', 'MEDIUM', 'HIGH'):
        return img_tag % (constants.WARNING_ICON, status)
    if status == 'OK':
        return img_tag % (constants.OK_ICON, status)
    if status == 'UNKNOWN' or status == 'UNDETERMINED':
        return img_tag % (constants.UNKNOWN_ICON, status)
    return status


def show_severity(data):
    severity = data['severity']
    state = data['state']
    if state == 'ALARM':
        return severity
    else:
        return state


def show_service(data):
    if any(data['expression_data']['dimensions']):
        dimensions = data['expression_data']['dimensions']
        if 'service' in dimensions:
            return str(data['expression_data']['dimensions']['service'])
    return ""


def show_host(data):
    if any(data['expression_data']['dimensions']):
        dimensions = data['expression_data']['dimensions']
        if 'hostname' in dimensions:
            return str(data['expression_data']['dimensions']['hostname'])
    return ""


class ShowAlarmHistory(tables.LinkAction):
    name = 'history'
    verbose_name = _('Show History')
    url = constants.URL_PREFIX + 'history'
    classes = ('btn-edit',)


class ShowAlarmMeters(tables.LinkAction):
    name = 'meters'
    verbose_name = _('Show Meters')
    url = constants.URL_PREFIX + 'meters'
    classes = ('btn-edit',)


class CreateAlarm(tables.LinkAction):
    name = "create_alarm"
    verbose_name = _("Create Alarm")
    classes = ("ajax-modal", "btn-create")
    url = constants.URL_PREFIX + 'alarm_create'

    def allowed(self, request, datum=None):
        return True


class EditAlarm(tables.LinkAction):
    name = "edit_alarm"
    verbose_name = _("Edit Alarm")
    classes = ("ajax-modal", "btn-create")
    url = constants.URL_PREFIX + 'alarm_edit'

    def allowed(self, request, datum=None):
        return True


class DeleteAlarm(tables.DeleteAction):
    name = "delete_alarm"
    verbose_name = _("Delete Alarm")
    data_type_singular = _("Alarm")
    data_type_plural = _("Alarms")

    def allowed(self, request, datum=None):
        return True

    def delete(self, request, obj_id):
        api.monitor.alarm_delete(request, obj_id)


class CreateNotification(tables.LinkAction):
    name = "create_notification"
    verbose_name = _("Create Notification")
    classes = ("ajax-modal", "btn-create")
    url = constants.URL_PREFIX + 'notification_create'

    def allowed(self, request, datum=None):
        return True


class AlarmsTable(tables.DataTable):
    status = tables.Column(transform=show_severity, verbose_name=_('Status'),
                           status_choices={(show_status('OK'), True)},
                           filters=[show_status, template.defaultfilters.safe])
    target = tables.Column('name', verbose_name=_('Name'),
                           link=constants.URL_PREFIX + 'alarm_detail',
                           link_classes=('ajax-modal',))
    host = tables.Column(transform=show_host, verbose_name=_('Host'))
    service = tables.Column(transform=show_service, verbose_name=_('Service'))
    state = tables.Column('state', verbose_name=_('State'))
    expression = tables.Column('expression', verbose_name=_('Expression'))
    enabled = tables.Column('actions_enabled',
                            verbose_name=_('Notifications Enabled'))

    def get_object_id(self, obj):
        return obj['id']

    class Meta:
        name = "alarms"
        verbose_name = _("Alarms")
        row_actions = (ShowAlarmHistory,
                       ShowAlarmMeters,
                       EditAlarm,
                       DeleteAlarm,
                       )
        table_actions = (CreateNotification, CreateAlarm, )


class AlarmHistoryTable(tables.DataTable):
    status = tables.Column('Status', verbose_name=_('Status'),
                           status_choices={(show_status('OK'), True)},
                           filters=[show_status, template.defaultfilters.safe])
    target = tables.Column('Host', verbose_name=_('Host'))
    name = tables.Column('Service', verbose_name=_('Service'))
    lastCheck = tables.Column('Last_Check', verbose_name=_('Last Check'))
    time = tables.Column('Duration', verbose_name=_('Duration'))
    detail = tables.Column('Status_Information',
                           verbose_name=_('Status_Information'))

    def get_object_id(self, obj):
        return obj['Last_Check'] + obj['Service']

    class Meta:
        name = "users"
        verbose_name = _("Alarm History")
        row_actions = (ShowAlarmMeters,)
