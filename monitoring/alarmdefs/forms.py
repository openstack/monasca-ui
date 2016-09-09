# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import json
from itertools import chain

from django.template.loader import get_template
from django.template import Context
from django.utils.translation import ugettext as _  # noqa

from horizon import exceptions
from horizon import forms
from horizon import messages

from monitoring import api
from monitoring.alarmdefs import constants


def _get_metrics(request):
    metrics = api.monitor.metrics_list(request)
    return json.dumps(metrics)


def _get_notifications(request):
    notifications = api.monitor.notification_list(request)
    return [(notification['id'],
             notification['name'],
             notification['type'],
             notification['address'])
            for notification in notifications]


class ExpressionWidget(forms.Widget):

    func = json.dumps(
        [('min', _('min')), ('max', _('max')), ('sum', _('sum')),
         ('count', _('count')), ('avg', _('avg'))])
    comparators = [['>', '>'], ['>=', '>='], ['<', '<'], ['<=', '<=']]
    operators = json.dumps([('AND', _('AND')), ('OR', _('OR'))])

    def __init__(self, initial, attrs=None):
        super(ExpressionWidget, self).__init__(attrs)
        self.initial = initial

    def render(self, name, value, attrs=None):
        final_attrs = self.build_attrs(attrs, name=name)
        t = get_template(constants.TEMPLATE_PREFIX + 'expression_field.html')

        local_attrs = {
            'func': ExpressionWidget.func,
            'comparators': ExpressionWidget.comparators,
            'operators': ExpressionWidget.operators,
            'metrics': self.metrics
        }

        local_attrs.update(final_attrs)

        return t.render(Context(local_attrs))


class ExpressionField(forms.CharField):

    def _get_metrics(self):
        return self._metrics

    def _set_metrics(self, value):
        self._metrics = self.widget.metrics = value

    metrics = property(_get_metrics, _set_metrics)


class MatchByWidget(forms.Widget):
    def __init__(self, initial, attrs=None):
        super(MatchByWidget, self).__init__(attrs)
        self.initial = initial

    def render(self, name, value, attrs=None):
        final_attrs = self.build_attrs(attrs, name=name)
        t = get_template(constants.TEMPLATE_PREFIX + 'match_by_field.html')

        local_attrs = {'service': ''}
        local_attrs.update(final_attrs)
        context = Context(local_attrs)
        return t.render(context)


class NotificationField(forms.MultiValueField):
    def __init__(self, *args, **kwargs):
        super(NotificationField, self).__init__(*args, **kwargs)

    def _get_choices(self):
        return self._choices

    def _set_choices(self, value):
        # Setting choices also sets the choices on the widget.
        # choices can be any iterable, but we call list() on it because
        # it will be consumed more than once.
        self._choices = self.widget.choices = list(value)

    choices = property(_get_choices, _set_choices)

    def compress(self, data_list):
        return data_list

    def clean(self, value):
        return value


class NotificationCreateWidget(forms.Select):
    def __init__(self, *args, **kwargs):
        super(NotificationCreateWidget, self).__init__(*args, **kwargs)

    def render(self, name, value, attrs=None, choices=()):
        final_attrs = self.build_attrs(attrs, name=name)
        tpl = get_template(constants.TEMPLATE_PREFIX + 'notification_field.html')

        selected = {}
        for item in value if value else []:
            selected[item['id']] = {'alarm': item['alarm'],
                                    'ok': item['ok'],
                                    'undetermined': item['undetermined']}
        data = []
        for id, label, type, address in chain(self.choices, choices):
            if id in selected:
                actions = selected[id]
                data.append((id, label, type, address, actions['alarm'],
                             actions['ok'], actions['undetermined'], True))
            else:
                data.append((id, label, type, address, True, True, True, False))

        local_attrs = {'data': json.dumps(data)}
        local_attrs.update(final_attrs)
        return tpl.render(Context(local_attrs))

    def value_from_datadict(self, data, files, name):
        return [{"id": _id} for _id in data.getlist(name)]


class EditAlarmForm(forms.SelfHandlingForm):

    def __init__(self, request, *args, **kwargs):
        super(EditAlarmForm, self).__init__(request, *args, **kwargs)
        self._init_fields(readOnly=False)
        self.set_notification_choices(request)

    @classmethod
    def _instantiate(cls, request, *args, **kwargs):
        return cls(request, *args, **kwargs)

    def _init_fields(self, readOnly=False, create=False, initial=None):
        required = True
        textWidget = None
        choiceWidget = forms.Select
        if create:
            expressionWidget = ExpressionWidget(initial)
            matchByWidget = MatchByWidget(initial)
            notificationWidget = NotificationCreateWidget()
        else:
            expressionWidget = textWidget
            matchByWidget = forms.TextInput(attrs={'readonly': 'readonly'})
            notificationWidget = NotificationCreateWidget()

        self.fields['name'] = forms.CharField(label=_("Name"),
                                              required=required,
                                              max_length=250,
                                              widget=textWidget,
                                              help_text=_("An unique name of the alarm."))
        self.fields['expression'] = forms.CharField(label=_("Expression"),
                                                    required=required,
                                                    widget=expressionWidget,
                                                    help_text=_("An alarm expression."))
        self.fields['match_by'] = forms.CharField(label=_("Match by"),
                                                  required=False,
                                                  widget=matchByWidget,
                                                  help_text=_("The metric dimensions used "
                                                              "to create unique alarms."))
        self.fields['description'] = forms.CharField(label=_("Description"),
                                                     required=False,
                                                     widget=textWidget,
                                                     help_text=_("A description of an alarm."))
        sev_choices = [("LOW", _("Low")),
                       ("MEDIUM", _("Medium")),
                       ("HIGH", _("High")),
                       ("CRITICAL", _("Critical"))]
        self.fields['severity'] = forms.ChoiceField(label=_("Severity"),
                                                    choices=sev_choices,
                                                    initial=sev_choices[0],
                                                    widget=choiceWidget,
                                                    required=False,
                                                    help_text=_("Severity of an alarm. "
                                                                "Must be either LOW, MEDIUM, HIGH "
                                                                "or CRITICAL. Default is LOW."))
        if not create:
            self.fields['actions_enabled'] = \
                forms.BooleanField(label=_("Notifications Enabled"),
                                   required=False,
                                   initial=True)
        self.fields['notifications'] = NotificationField(
            label=_("Notifications"),
            required=False,
            widget=notificationWidget,
            help_text=_("Notification methods. "
                        "Notifications can be sent when an alarm state transition occurs."))
        self.fields['alarm_actions'] = NotificationField(
            label=_("Alarm Actions"),
            widget=forms.MultipleHiddenInput())
        self.fields['ok_actions'] = NotificationField(
            label=_("OK Actions"),
            widget=forms.MultipleHiddenInput())
        self.fields['undetermined_actions'] = NotificationField(
            label=_("Undetermined Actions"),
            widget=forms.MultipleHiddenInput())

    def set_notification_choices(self, request):
        try:
            notifications = api.monitor.notification_list(request)
        except Exception as e:
            notifications = []
            exceptions.handle(request,
                              _('Unable to retrieve notifications: %s') % e)
        notification_choices = [(notification['id'],
                                 notification['name'],
                                 notification['type'],
                                 notification['address'])
                                for notification in notifications]

        self.fields['notifications'].choices = notification_choices

    def handle(self, request, data):
        try:
            alarm_def = api.monitor.alarmdef_get(request, self.initial['id'])
            api.monitor.alarmdef_update(
                request,
                alarm_id=self.initial['id'],
                severity=data['severity'],
                name=data['name'],
                expression=data['expression'],
                description=data['description'],
                match_by=alarm_def['match_by'],
                actions_enabled=data['actions_enabled'],
                alarm_actions=data['alarm_actions'],
                ok_actions=data['ok_actions'],
                undetermined_actions=data['undetermined_actions'],
            )
            messages.success(request,
                             _('Alarm definition has been updated.'))
        except Exception as e:
            exceptions.handle(request, _('%s') % e)
            return False
        return True
