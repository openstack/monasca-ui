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
    img_tag = '<img src="{img}" title="{label}" class="status-icon" />{label}'
    if status == 'CRITICAL':
        return img_tag.format(img=constants.CRITICAL_ICON, label=status)
    if status in ('LOW', 'MEDIUM', 'HIGH'):
        return img_tag.format(img=constants.WARNING_ICON, label=status)
    if status == 'OK':
        return img_tag.format(img=constants.OK_ICON, label=status)
    if status == 'UNKNOWN' or status == 'UNDETERMINED':
        return img_tag.format(img=constants.UNKNOWN_ICON, label=status)
    return status


def show_severity(data):
    severity = data['alarm_definition']['severity']
    state = data['state']
    if state == 'ALARM':
        return severity
    else:
        return state


def show_metric_name(data):
    return data['metrics'][0]['name']


def show_def_name(data):
    return data['alarm_definition']['name']


def show_def_severity(data):
    return data['alarm_definition']['severity']


def show_metric_dimensions(data):
    if len(data['metrics']) > 1:
        commondimensions = data['metrics'][0]['dimensions']
        for metric in data['metrics'][1:]:
            for k in commondimensions.keys():
                if k not in metric['dimensions'].keys() or commondimensions[k] != metric['dimensions'][k]:
                    del commondimensions[k]
        return ','.join(["%s=%s" % (n, v) for n,v in commondimensions.items()])
    else:
        return ','.join(["%s=%s" % (n, v) for n,v in data['metrics'][0]['dimensions'].items()])


def get_service(data):
    if len(data['metrics']) == 1 and 'service' in data['metrics'][0]['dimensions']:
        return data['metrics'][0]['dimensions']['service']
    else:
        return ''


class ShowAlarmHistory(tables.LinkAction):
    name = 'history'
    verbose_name = _('Show History')
    classes = ('btn-edit',)

    def get_link_url(self, datum):
        return urlresolvers.reverse(constants.URL_PREFIX + 'history',
                                    args=(datum['alarm_definition']['id'], datum['id'], ))

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
        name = datum['metrics'][0]['name']
        threshold = datum['metrics']
        token = self.table.request.user.token.id
        endpoint = api.monitor.monasca_endpoint(self.table.request)
        self.attrs['target'] = '_blank'
        url = '/static/grafana/index.html#/dashboard/script/detail.js'
        query = "?token=%s&name=%s&threshold=%s&api=%s" % \
                (token, name, threshold, endpoint)
        return url + query

    def allowed(self, request, datum=None):
        return datum['metrics']


class ShowAlarmDefinition(tables.LinkAction):
    name = "show_alarm_definition"
    verbose_name = _("Show Alarm Definition")

    def get_link_url(self, datum=None):
        return urlresolvers.reverse_lazy('horizon:monitoring:alarmdefs:alarm_detail',
                                         args=(datum['alarm_definition']['id'],))


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
                if q in alarm['metrics'][0]['name'].lower()]


class AlarmsTable(tables.DataTable):
    state = tables.Column(transform=show_severity, verbose_name=_('Status'),
                           status_choices={(show_status('OK'), True)},
                           filters=[show_status, template.defaultfilters.safe])
    metrics = tables.Column(transform=show_metric_name, verbose_name=_('Metric Name'))
    dimensions = tables.Column(transform=show_metric_dimensions, verbose_name=_('Metric Dimensions'))
    name = tables.Column(transform=show_def_name, verbose_name=_('Definition'))

    def get_object_id(self, obj):
        return obj['id']

    def get_object_display(self, obj):
        return obj['id']

    class Meta:
        name = "alarms"
        verbose_name = _("Alarms")
        row_actions = (GraphMetric,
                       ShowAlarmHistory,
                       ShowAlarmDefinition,
                       DeleteAlarm,
                       )
        table_actions = (AlarmsFilterAction,
                         DeleteAlarm,
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
