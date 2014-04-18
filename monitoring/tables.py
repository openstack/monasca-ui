'''
Created on Jun 19, 2011

@author: lcheng

User tables
'''

import logging

from django.utils.translation import ugettext_lazy as _
from django import template

from horizon import tables

LOG = logging.getLogger(__name__)



STATUS = ["OK", "WARNING", "CRITICAL", "UNKNOWN"]
CRITICAL_ICON = '/static/monitoring/img/critical-icon.png'
WARNING_ICON = '/static/monitoring/img/warning-icon.png'
OK_ICON = '/static/monitoring/img/ok-icon.png'
UNKNOWN_ICON = '/static/monitoring/img/unknown-icon.png'
NOTFOUND_ICON = '/static/monitoring/img/notfound-icon.png'


def get_status(index):
    if index < len(STATUS):
        return STATUS[index]
    else:
        return "UNKNOWN: %d" % index


def show_status(data):
    status = data
    img_tag = '<img style="margin-right:5px;" src="%s"/>%s'
    if status == 'CRITICAL':
        return img_tag % (CRITICAL_ICON, status)
    if status == 'WARNING':
        return img_tag % (WARNING_ICON, status)
    if status == 'OK':
        return img_tag % (OK_ICON, status)
    if status == 'UNKNOWN':
        return img_tag % (UNKNOWN_ICON, status)
    return status


class ShowAlarmHistory(tables.LinkAction):
    name = 'history'
    verbose_name = _('Show History')
    url = 'history'
    classes = ('btn-edit',)


class ShowAlarmMeters(tables.LinkAction):
    name = 'meters'
    verbose_name = _('Show Meters')
    url = 'meters'
    classes = ('btn-edit',)


class AlertsTable(tables.DataTable):
    target = tables.Column('Host', verbose_name=_('Host'))
    name = tables.Column('Service', verbose_name=_('Service'))
    status = tables.Column('Status', verbose_name=_('Status'),
                           status_choices={(show_status('OK'), True)},
                           filters=[show_status, template.defaultfilters.safe])
    lastCheck = tables.Column('Last_Check', verbose_name=_('Last Check'))
    time = tables.Column('Duration', verbose_name=_('Duration'))
    detail = tables.Column('Status_Information',
                           verbose_name=_('Status_Information'))

    def get_object_id(self, obj):
        return obj['Host'] + obj['Service']

    class Meta:
        name = "users"
        verbose_name = _("Alarms for Nova in the UnderCloud")
        row_actions = (ShowAlarmHistory, ShowAlarmMeters,)
        status_columns = ['status']


class AlertHistoryTable(tables.DataTable):
    target = tables.Column('Host', verbose_name=_('Host'))
    name = tables.Column('Service', verbose_name=_('Service'))
    status = tables.Column('Status', verbose_name=_('Status'),
                           status_choices={(show_status('OK'), True)},
                           filters=[show_status, template.defaultfilters.safe])
    lastCheck = tables.Column('Last_Check', verbose_name=_('Last Check'))
    time = tables.Column('Duration', verbose_name=_('Duration'))
    detail = tables.Column('Status_Information',
                           verbose_name=_('Status_Information'))

    def get_object_id(self, obj):
        return obj['Last_Check'] + obj['Service']

    class Meta:
        name = "users"
        verbose_name = _("Alarm History for Nova in the UnderCloud")
        row_actions = (ShowAlarmMeters,)
        status_columns = ['status']
