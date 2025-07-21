# Copyright 2013 Hewlett-Packard Development Company, L.P.
# Copyright 2016 Cray Inc. All rights reserved.
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

import json

from django.conf import settings
from django import template
from django.urls import reverse
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext_lazy

from horizon import tables

from monitoring.alarms import constants
from monitoring import api
from monitoring.overview import constants as ov_constants


STATUS = ["OK", "WARNING", "CRITICAL", "UNKNOWN"]


def get_status(index):
    if index < len(STATUS):
        return STATUS[index]
    else:
        return "UNKNOWN: %d" % index


def show_status(data):
    status = data.upper()
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
        return severity.upper()
    else:
        return state.upper()


def show_alarm_id(data):
    return data['id']


def show_metric_names(data):
    names = set(metric['name'] for metric in data['metrics'])
    return ', '.join(names)


def show_def_name(data):
    return data['alarm_definition']['name']


def show_def_severity(data):
    return data['alarm_definition']['severity']


def show_metric_dimensions(data):
    if len(data['metrics']) > 1:
        commondimensions = data['metrics'][0]['dimensions']
        for metric in data['metrics'][1:]:
            for k in tuple(commondimensions):
                if k not in metric['dimensions'].keys() or \
                        commondimensions[k] != metric['dimensions'][k]:
                    del commondimensions[k]
        return ','.join(["%s=%s" % (n, v) for n, v
                         in commondimensions.items()])
    else:
        return ','.join(["%s=%s" % (n, v) for n, v
                         in data['metrics'][0]['dimensions'].items()])


def get_service(data):
    if len(data['metrics']) == 1 and 'service'in\
            data['metrics'][0]['dimensions']:
        return data['metrics'][0]['dimensions']['service']
    else:
        return ''


class ShowAlarmHistory(tables.LinkAction):
    name = 'history'
    verbose_name = _('Show History')
    classes = ('btn-edit',)

    def get_link_url(self, datum):
        return reverse(constants.URL_PREFIX + 'history',
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
        return reverse(constants.URL_PREFIX + 'alarm_create',
                       args=(self.table.kwargs['service'],))

    def allowed(self, request, datum=None):
        return True


class EditAlarm(tables.LinkAction):
    name = "edit_alarm"
    verbose_name = _("Edit Alarm")
    classes = ("ajax-modal", "btn-create")

    def get_link_url(self, datum):
        return reverse(constants.URL_PREFIX + 'alarm_edit',
                       args=(self.table.kwargs['service'], datum['id'], ))

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
        url = ''
        query = ''
        self.attrs['target'] = '_blank'
        try:
            region = self.table.request.user.services_region
            grafana_url = getattr(settings, 'GRAFANA_URL').get(region, '')
            url = grafana_url + \
                '/dashboard/script/drilldown.js'
            metric = datum['metrics'][0]['name']
            dimensions = datum['metrics'][0].get('dimensions', {})
            query = "?metric=%s" % metric
            for key, value in dimensions.items():
                query += "&%s=%s" % (key, value)
        except AttributeError:
            # Catches case where Grafana 2 is not enabled.
            name = datum['metrics'][0]['name']
            threshold = json.dumps(datum['metrics'])
            endpoint = str(reverse_lazy(ov_constants.URL_PREFIX + 'proxy'))
            endpoint = self.table.request.build_absolute_uri(endpoint)
            url = '/grafana/index.html#/dashboard/script/detail.js'
            query = "?name=%s&threshold=%s&api=%s" % \
                (name, threshold, endpoint)
        return url + query

    def allowed(self, request, datum=None):
        return (getattr(settings, 'GRAFANA_URL', None) is not None and
                datum['metrics'])


class ShowAlarmDefinition(tables.LinkAction):
    name = "show_alarm_definition"
    verbose_name = _("Show Alarm Definition")

    def get_link_url(self, datum=None):
        url = 'horizon:monitoring:alarmdefs:alarm_detail'
        args = (datum['alarm_definition']['id'],)
        return reverse_lazy(url, args=args)


class DeleteAlarm(tables.DeleteAction):
    name = "delete_alarm"
    verbose_name = _("Delete Alarm")

    @staticmethod
    def action_present(count):
        return ngettext_lazy(
            "Delete Alarm",
            "Delete Alarms",
            count
        )

    @staticmethod
    def action_past(count):
        return ngettext_lazy(
            "Deleted Alarm",
            "Deleted Alarms",
            count
        )

    def allowed(self, request, datum=None):
        return True

    def delete(self, request, obj_id):
        api.monitor.alarm_delete(request, obj_id)


class AlarmsFilterAction(tables.LinkAction):
    name = "filter"
    verbose_name = _("Filter Alarms")
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (("alarm", "alarm:filter"),)
    ajax = True

    def get_link_url(self):
        return reverse(constants.URL_PREFIX + 'alarm_filter', args=())

    def allowed(self, request, datum=None):
        return True


class AlarmsTable(tables.DataTable):
    state = tables.Column(transform=show_severity, verbose_name=_('Status'),
                          status_choices={(show_status('OK'), True)},
                          filters=[show_status, template.defaultfilters.safe])
    name = tables.Column(transform=show_def_name, verbose_name=_('Name'))
    alarmId = tables.Column(transform=show_alarm_id, verbose_name=_('Alarm Id'))
    metrics = tables.Column(transform=show_metric_names,
                            verbose_name=_('Metric Names'))
    dimensions = tables.Column(transform=show_metric_dimensions,
                               verbose_name=_('Metric Dimensions'))

    def get_object_id(self, obj):
        return obj['id']

    def get_object_display(self, obj):
        return obj['id']

    class Meta(object):
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


def show_timestamp(data):
    return data['timestamp'].replace('.000Z', '').replace('T', ' ')


class AlarmHistoryTable(tables.DataTable):
    timestamp = tables.Column(transform=show_timestamp,
                              verbose_name=_('Timestamp'),
                              attrs={"data-type": "timestamp"})
    old_state = tables.Column('old_state', verbose_name=_('Old State'))
    new_state = tables.Column('new_state', verbose_name=_('New State'))
    alarmDimensions = tables.Column(transform=show_metric_dimensions,
                                    verbose_name=_('Alarm Metric Dimensions'))
    reason = tables.Column('reason', verbose_name=_('Reason'))
    # reason_data = tables.Column('reason_data', verbose_name=_('Reason Data'))

    def get_object_id(self, obj):
        return obj['alarm_id'] + obj['timestamp']

    class Meta(object):
        name = "history"
        verbose_name = _("Alarm History")
