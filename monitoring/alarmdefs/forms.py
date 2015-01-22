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

from django.template.loader import get_template
from django.template import Context
from django.utils import html
from django.utils.translation import ugettext as _  # noqa

from horizon import exceptions
from horizon import forms
from horizon import messages

from monitoring import api
from monitoring.alarmdefs import constants


class ExpressionWidget(forms.Widget):
    def __init__(self, initial, attrs=None):
        super(ExpressionWidget, self).__init__(attrs)
        self.initial = initial

    def render(self, name, value, attrs):
        final_attrs = self.build_attrs(attrs, name=name)
        t = get_template(constants.TEMPLATE_PREFIX + 'expression_field.html')
        func = json.dumps([('min', _('min')), ('max', _('max')), ('sum', _('sum')),
        ('count', _('count')), ('avg', _('avg'))])
        comparators = [['>', '>'], ['>=', '>='], ['<', '<'], ['<=', '<=']]


        local_attrs = {'service': '', 'func': func, 'comparators': comparators}
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
        output = '<table id="notification_table" ' + \
            'class="table table-condensed">'
        output += '<thead><tr><th>%s</th></tr></thead>' % \
            unicode(_("Name"))
        if value:
            idx = 1
            for notification in value:
                output += '<tr><td>'
                output += ('<select id="id_notifications_%d" ' +
                           'name="notifications_%d"> ') % (idx, idx)
                options = self.render_options(
                    choices,
                    [notification['id']])
                if options:
                    output += options
                output += '</select>'
                output += '<td><a href="" id="remove_notif_button">X</a></td>'
                output += '</td></tr>'
                idx += 1
        else:
            output += '<tr><td>'
            output += '<select id="id_notifications_1" '
            output += 'name="notifications_1"> '
            options = self.render_options(choices, [value])
            if options:
                output += options
            output += '</select>'
            output += '<td><a href="" id="remove_notif_button">X</a></td>'
            output += '</td></tr>'
        output += '</table>'
        label = unicode(_("+ Add more"))
        output += '<a href="" id="add_notification_button">%s</a>' % (label)
        return html.format_html(output)

    def value_from_datadict(self, data, files, name):
        notifications = []
        i = 0
        while True:
            i += 1
            notification_id = "%s_%d" % (name, i)
            if notification_id in data:
                if len(data[notification_id]) > 0:
                    notifications.append({"id":
                                         data[notification_id]})
            else:
                break
        return notifications


class BaseAlarmForm(forms.SelfHandlingForm):
    @classmethod
    def _instantiate(cls, request, *args, **kwargs):
        return cls(request, *args, **kwargs)

    def _init_fields(self, readOnly=False, create=False, initial=None):
        required = True
        textWidget = None
        choiceWidget = forms.Select
        if create:
            expressionWidget = ExpressionWidget(initial)
            notificationWidget = NotificationCreateWidget()
        else:
            expressionWidget = textWidget
            notificationWidget = NotificationCreateWidget()

        self.fields['name'] = forms.CharField(label=_("Name"),
                                              required=required,
                                              max_length=250,
                                              widget=textWidget)
        self.fields['expression'] = forms.CharField(label=_("Expression"),
                                                    required=required,
                                                    widget=expressionWidget)
        apply_to = [['1', _('individually')],
                    ['2', _('as a group')]]
        self.fields['apply_to'] = forms.ChoiceField(label=_("Apply function to metrics"),
                                                    choices=apply_to,
                                                    required=False,
                                                    widget=forms.RadioSelect(),
                                                    initial="1")
        self.fields['description'] = forms.CharField(label=_("Description"),
                                                     required=False,
                                                     widget=textWidget)
        sev_choices = [("LOW", _("Low")),
                       ("MEDIUM", _("Medium")),
                       ("HIGH", _("High")),
                       ("CRITICAL", _("Critical"))]
        self.fields['severity'] = forms.ChoiceField(label=_("Severity"),
                                                    choices=sev_choices,
                                                    widget=choiceWidget,
                                                    required=False)
        self.fields['state'] = forms.CharField(label=_("State"),
                                               required=False,
                                               widget=textWidget)
        self.fields['actions_enabled'] = \
            forms.BooleanField(label=_("Notifications Enabled"),
                               required=False,
                               initial=True)
        self.fields['notifications'] = NotificationField(
            label=_("Notifications"),
            required=False,
            widget=notificationWidget)

    def set_notification_choices(self, request):
        try:
            notifications = api.monitor.notification_list(request)
        except Exception as e:
            notifications = []
            exceptions.handle(request,
                              _('Unable to retrieve notifications: %s') % e)
        notification_choices = [(notification['id'], notification['name'])
                                for notification in notifications]
        if notification_choices:
            if len(notification_choices) > 1:
                notification_choices.insert(
                    0, ("", unicode(_("Select Notification"))))
        else:
            notification_choices.insert(
                0, ("", unicode(_("No notifications available."))))

        self.fields['notifications'].choices = notification_choices

    def clean_expression(self):
        data = self.cleaned_data['expression']
        value = data.split(' ')[2]
        try:
            float(value)
        except ValueError:
            raise forms.ValidationError("Value must be a number")

        # Always return the cleaned data, whether you have changed it or
        # not.
        return data


class CreateAlarmForm(BaseAlarmForm):
    def __init__(self, request, *args, **kwargs):
        super(CreateAlarmForm, self).__init__(request, *args, **kwargs)
        super(CreateAlarmForm, self)._init_fields(readOnly=False, create=True,
                                                  initial=kwargs['initial'])
        super(CreateAlarmForm, self).set_notification_choices(request)
        self.fields.pop('state')

    def handle(self, request, data):
        try:
            alarm_actions = [notification.get('id')
                             for notification in data['notifications']]
            api.monitor.alarmdef_create(
                request,
                name=data['name'],
                expression=data['expression'],
                description=data['description'],
                severity=data['severity'],
                match_by=request.POST['match_by'].split(',') if request.POST['apply_to'] == '1' else None,
                alarm_actions=alarm_actions,
                ok_actions=alarm_actions,
                undetermined_actions=alarm_actions,
            )
            messages.success(request,
                             _('Alarm Definition has been created successfully.'))
        except Exception as e:
            exceptions.handle(request, _('Unable to create the alarm definition: %s') % e.message)
            return False
        return True


class EditAlarmForm(BaseAlarmForm):
    def __init__(self, request, *args, **kwargs):
        super(EditAlarmForm, self).__init__(request, *args, **kwargs)
        super(EditAlarmForm, self)._init_fields(readOnly=False)
        super(EditAlarmForm, self).set_notification_choices(request)
        self.fields.pop('state')

    def handle(self, request, data):
        try:
            alarm_actions = []
            alarm_def = api.monitor.alarmdef_get(request, self.initial['id'])
            if data['notifications']:
                alarm_actions = [notification.get('id')
                                 for notification in data['notifications']]
            api.monitor.alarmdef_update(
                request,
                alarm_id=self.initial['id'],
                severity=data['severity'],
                name=data['name'],
                expression=data['expression'],
                description=data['description'],
                match_by = alarm_def['match_by'],
                actions_enabled=data['actions_enabled'],
                alarm_actions=alarm_actions,
                ok_actions=alarm_actions,
                undetermined_actions=alarm_actions,
            )
            messages.success(request,
                             _('Alarm definition has been updated.'))
        except Exception as e:
            exceptions.handle(request, _('Unable to edit the alarm definition: %s') % e)
            return False
        return True
