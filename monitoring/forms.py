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

from django import forms as django_forms
from django.utils.html import escape
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon import forms
from horizon import messages

from monitoring import api
from monitoring import constants


def get_expression(meter):
    expr = meter['name']
    args = None
    for name, value in meter['dimensions'].items():
        if name != 'detail':
            if args:
                args += ', '
            else:
                args = ''
            args += "%s=%s" % (name, value)
    return "%s{%s}" % (expr, args)


class SimpleExpressionWidget(django_forms.MultiWidget):
    def __init__(self, meters=None, attrs=None):
        choices = [(get_expression(m), get_expression(m)) for m in meters]
        comparators = [('>', '>'), ('>=', '>='), ('<', '<'), ('<=', '<=')]
        func = [('min', _('min')), ('max', _('max')), ('sum', _('sum')),
                ('count', _('count')), ('avg', _('avg'))]
        _widgets = (
            django_forms.widgets.Select(attrs=attrs, choices=func),
            django_forms.widgets.Select(attrs=attrs, choices=choices),
            django_forms.widgets.Select(attrs=attrs, choices=comparators),
            django_forms.widgets.TextInput(attrs=attrs),
        )
        super(SimpleExpressionWidget, self).__init__(_widgets, attrs)

    def decompress(self, expr):
        return [None, None, None]

    def format_output(self, rendered_widgets):
        return ''.join(rendered_widgets)

    def value_from_datadict(self, data, files, name):
        values = [
            widget.value_from_datadict(data, files, name + '_%s' % i)
            for i, widget in enumerate(self.widgets)]
        try:
            expression = '%s(%s)%s%s' % (values[0],
                                         values[1],
                                         values[2],
                                         values[3])
        except ValueError:
            return ''
        else:
            return expression


class NotificationTableWidget(forms.Widget):
    FIELD_ID_IDX = 0
    FIELD_NAME_IDX = 1

    def __init__(self, *args, **kwargs):
        self.fields = kwargs.pop('fields')
        super(NotificationTableWidget, self).__init__(*args, **kwargs)

    def render(self, name, value, attrs):
        output = '<table class="table table-condensed"><thead><tr>'
        for field in self.fields:
            output += '<th>%s</th>' % unicode(field[self.FIELD_NAME_IDX])
        output += '</tr></thead>'
        if value:
            for notification in value:
                output += "<tr>"
                for field in self.fields:
                    field_value = notification[field[self.FIELD_ID_IDX]]
                    output += '<td>%s</td>' % escape(field_value)
                output += "</tr>"
        output += '</table>'
        return format_html(output)


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
                    [notification['notification_id']])
                if options:
                    output += options
                output += '</select>'
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
            output += '</td></tr>'
        output += '</table>'
        label = unicode(_("+ Add more"))
        output += '<a href="" id="add_notification_button">%s</a>' % (label)
        return format_html(output)

    def value_from_datadict(self, data, files, name):
        notifications = []
        i = 0
        while True:
            i += 1
            notification_id = "%s_%d" % (name, i)
            if notification_id in data:
                if len(data[notification_id]) > 0:
                    notifications.append({"notification_id":
                                         data[notification_id]})
            else:
                break
        return notifications


class BaseAlarmForm(forms.SelfHandlingForm):
    @classmethod
    def _instantiate(cls, request, *args, **kwargs):
        return cls(request, *args, **kwargs)

    def _init_fields(self, readOnly=False, create=False):
        required = True
        textWidget = None
        textAreaWidget = forms.Textarea(attrs={'class': 'large-text-area'})
        readOnlyTextInput = forms.TextInput(attrs={'readonly': 'readonly'})
        choiceWidget = forms.Select
        if readOnly:
            required = False
            textWidget = readOnlyTextInput
            choiceWidget = readOnlyTextInput
            textAreaWidget = forms.Textarea(attrs={'readonly': 'readonly',
                                                   'class': 'large-text-area'
                                                   })
            expressionWidget = textAreaWidget
        else:
            meters = api.monitor.metrics_list(self.request)
            if create:
                expressionWidget = SimpleExpressionWidget(meters=meters)
            else:
                expressionWidget = textAreaWidget

        if create:
            notificationWidget = NotificationCreateWidget()
        else:
            notificationWidget = NotificationTableWidget(
                fields=[('name', _('Name')),
                        ('type', _('Type')),
                        ('address', _('Address')), ])

        self.fields['name'] = forms.CharField(label=_("Name"),
                                              required=required,
                                              max_length=250,
                                              widget=textWidget)
        self.fields['expression'] = forms.CharField(label=_("Expression"),
                                                    required=required,
                                                    widget=expressionWidget)
        self.fields['description'] = forms.CharField(label=_("Description"),
                                                     required=False,
                                                     widget=textAreaWidget)
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


class CreateAlarmForm(BaseAlarmForm):
    def __init__(self, request, *args, **kwargs):
        super(CreateAlarmForm, self).__init__(request, *args, **kwargs)
        super(CreateAlarmForm, self)._init_fields(readOnly=False, create=True)
        super(CreateAlarmForm, self).set_notification_choices(request)
        self.fields.pop('state')

    def handle(self, request, data):
        try:
            alarm_actions = [notification.get('notification_id')
                             for notification in data['notifications']]
            api.monitor.alarm_create(
                request,
                name=data['name'],
                expression=data['expression'],
                description=data['description'],
                severity=data['severity'],
                alarm_actions=alarm_actions)
            messages.success(request,
                             _('Alarm has been created successfully.'))
        except Exception as e:
            exceptions.handle(request, _('Unable to create the alarm: %s') % e)
            return False
        return True


class DetailAlarmForm(BaseAlarmForm):
    def __init__(self, request, *args, **kwargs):
        super(DetailAlarmForm, self).__init__(request, *args, **kwargs)
        super(DetailAlarmForm, self)._init_fields(readOnly=True)

    def handle(self, request, data):
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
            if data['notifications']:
                alarm_actions = [notification.get('notification_id')
                                 for notification in data['notifications']]
            api.monitor.alarm_update(
                request,
                alarm_id=self.initial['id'],
                actions_enabled=self.initial['actions_enabled'],
                state=self.initial['state'],
                severity=data['severity'],
                name=data['name'],
                expression=data['expression'],
                description=data['description'],
                alarm_actions=alarm_actions,
            )
            messages.success(request,
                             _('Alarm has been edited successfully.'))
        except Exception as e:
            exceptions.handle(request, _('Unable to edit the alarm: %s') % e)
            return False
        return True


READONLY_TEXTINPUT = forms.TextInput(attrs={'readonly': 'readonly'})


class BaseNotificationMethodForm(forms.SelfHandlingForm):
    @classmethod
    def _instantiate(cls, request, *args, **kwargs):
        return cls(request, *args, **kwargs)

    def _init_fields(self, readOnly=False, create=False):
        required = True
        textWidget = None
        selectWidget = None
        readOnlyTextInput = READONLY_TEXTINPUT
        readOnlySelectInput = forms.Select(attrs={'disabled': 'disabled'})
        if readOnly:
            required = False
            textWidget = readOnlyTextInput
            selectWidget = readOnlySelectInput

        self.fields['name'] = forms.CharField(label=_("Name"),
                                              required=required,
                                              max_length="250",
                                              widget=textWidget)
        self.fields['type'] = forms.ChoiceField(
            label=_("Type"),
            required=False,
            widget=selectWidget,
            choices=constants.NotificationType.CHOICES,
            initial=constants.NotificationType.EMAIL)
        self.fields['address'] = forms.CharField(label=_("Address"),
                                                 required=required,
                                                 max_length="100",
                                                 widget=textWidget)


class CreateMethodForm(BaseNotificationMethodForm):
    def __init__(self, request, *args, **kwargs):
        super(CreateMethodForm, self).__init__(request, *args, **kwargs)
        super(CreateMethodForm, self)._init_fields(readOnly=False)

    def clean(self):
        '''Check to make sure address is the correct format depending on the
        type of notification
        '''
        data = super(forms.Form, self).clean()
        if data['type'] == constants.NotificationType.EMAIL:
            constants.EMAIL_VALIDATOR(data['address'])
        elif data['type'] == constants.NotificationType.SMS:
            constants.PHONE_VALIDATOR(data['address'])

        return data

    def handle(self, request, data):
        try:
            api.monitor.notification_create(
                request,
                name=data['name'],
                type=data['type'],
                address=data['address'])
            messages.success(request,
                             _('Notification method has been created '
                               'successfully.'))
        except Exception as e:
            exceptions.handle(request,
                              _('Unable to create the notification '
                                'method: %s') % e)
            return False
        return True


class DetailMethodForm(BaseNotificationMethodForm):
    def __init__(self, request, *args, **kwargs):
        super(DetailMethodForm, self).__init__(request, *args, **kwargs)
        super(DetailMethodForm, self)._init_fields(readOnly=True)

    def handle(self, request, data):
        return True
