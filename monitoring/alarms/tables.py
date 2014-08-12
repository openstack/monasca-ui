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

from django.core import urlresolvers
from django import template
from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon import tables

from monitoring.alarms import constants
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
    if 'dimensions' in data['expression_data']:
        dimensions = data['expression_data']['dimensions']
        if 'service' in dimensions:
            return str(data['expression_data']['dimensions']['service'])
    return ""


def show_host(data):
    if 'dimensions' in data['expression_data']:
        dimensions = data['expression_data']['dimensions']
        if 'hostname' in dimensions:
            return str(data['expression_data']['dimensions']['hostname'])
    return ""


class ShowAlarmHistory(tables.LinkAction):
    name = 'history'
    verbose_name = _('Show History')
    classes = ('btn-edit',)

    def get_link_url(self, datum):
        return urlresolvers.reverse(constants.URL_PREFIX + 'history',
                                    args=(datum['name'], datum['id'], ))

    def allowed(self, request, datum=None):
        return True


class CreateAlarm(tables.LinkAction):
    name = "create_alarm"
    verbose_name = _("Create Alarm")
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("alarm", "alarm:create"),)
    ajax = True

    def get_link_url(self):
        return urlresolvers.reverse(constants.URL_PREFIX + 'alarm_create',
                                    args=(self.table.kwargs['service'],))

    def allowed(self, request, datum=None):
        return True


class EditAlarm(tables.LinkAction):
    name = "edit_alarm"
    verbose_name = _("Edit Alarm")
    classes = ("ajax-modal", "btn-create")

    def get_link_url(self, datum):
        return urlresolvers.reverse(constants.URL_PREFIX + 'alarm_edit',
                                    args=(self.table.kwargs['service'],
                                          datum['id'], ))

    def allowed(self, request, datum=None):
        return True


class GraphMetric(tables.LinkAction):
    name = "graph_alarm"
    verbose_name = _("Graph Metric")
    icon = "dashboard"

    def render(self):
        self.attrs['target'] = 'newtab'
        return super(self, GraphMetric).render()

    def get_link_url(self, datum):
        name = datum['expression_data']['metric_name']
        self.attrs['target'] = '_blank'
        return "/static/grafana/index.html#/dashboard/script/detail.js?token=%s&name=%s" % \
               (self.table.request.user.token.id, name)

    def allowed(self, request, datum=None):
        return 'metric_name' in datum['expression_data']


class DeleteAlarm(tables.DeleteAction):
    name = "delete_alarm"
    verbose_name = _("Delete Alarm")
    data_type_singular = _("Alarm")
    data_type_plural = _("Alarms")

    def allowed(self, request, datum=None):
        return True

    def delete(self, request, obj_id):
        api.monitor.alarm_delete(request, obj_id)


class AlarmsFilterAction(tables.FilterAction):
    def filter(self, table, alarms, filter_string):
        """Naive case-insensitive search."""
        q = filter_string.lower()
        return [alarm for alarm in alarms
                if q in alarm.name.lower()]


class AlarmsTable(tables.DataTable):
    status = tables.Column(transform=show_severity, verbose_name=_('Status'),
                           status_choices={(show_status('OK'), True)},
                           filters=[show_status, template.defaultfilters.safe])
    target = tables.Column('name', verbose_name=_('Name'),
                           link=constants.URL_PREFIX + 'alarm_detail',
                           link_classes=('ajax-modal',))
    description = tables.Column('description', verbose_name=_('Description'))
    host = tables.Column(transform=show_host, verbose_name=_('Host'))
    service = tables.Column(transform=show_service, verbose_name=_('Service'))
    state = tables.Column('state', verbose_name=_('State'))
    enabled = tables.Column('actions_enabled',
                            verbose_name=_('Notifications Enabled'))

    def get_object_id(self, obj):
        return obj['id']

    def get_object_display(self, obj):
        return obj['name']

    class Meta:
        name = "alarms"
        verbose_name = _("Alarms")
        row_actions = (GraphMetric,
                       ShowAlarmHistory,
                       EditAlarm,
                       DeleteAlarm,
                       )
        table_actions = (CreateAlarm,
                         AlarmsFilterAction,
                        )


class AlarmHistoryTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Name'))
    old_state = tables.Column('old_state', verbose_name=_('Old State'))
    new_state = tables.Column('new_state', verbose_name=_('New State'))
    timestamp = tables.Column('timestamp', verbose_name=_('Timestamp'))
    reason = tables.Column('reason', verbose_name=_('Reason'))
    # reason_data = tables.Column('reason_data', verbose_name=_('Reason Data'))

    def get_object_id(self, obj):
        return obj['alarm_id'] + obj['timestamp']

    class Meta:
        name = "users"
        verbose_name = _("Alarm History")
