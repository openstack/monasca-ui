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

from django.utils.translation import ugettext_lazy as _  # noqa

from horizon import exceptions
from horizon import forms
from horizon import messages

from monitoring import api
from monitoring.notifications import constants


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
                                              widget=textWidget,
                                              help_text=_("A descriptive name of "
                                                          "the notification method."))
        self.fields['type'] = forms.ChoiceField(
            label=_("Type"),
            required=required,
            widget=selectWidget,
            choices=constants.NotificationType.CHOICES,
            initial=constants.NotificationType.EMAIL,
            help_text=_("The type of notification method (i.e. email)."))
        self.fields['address'] = forms.CharField(label=_("Address"),
                                                 required=required,
                                                 max_length="512",
                                                 widget=textWidget,
                                                 help_text=_("The email/url address to notify."))
        self.fields['period'] = forms.IntegerField(label=_("Period"),
                                                   min_value=0,
                                                   initial=0,
                                                   required=required,
                                                   help_text=_("The notification period."))

    def clean_period(self):
        '''Check to make sure period is zero unless type is WEBHOOK.
        '''
        data = self.cleaned_data
        if data['type'] != constants.NotificationType.WEBHOOK and data['period'] != 0:
            raise forms.ValidationError("Period must be zero except for type webhook.")

        return data['period']


class CreateMethodForm(BaseNotificationMethodForm):
    def __init__(self, request, *args, **kwargs):
        super(CreateMethodForm, self).__init__(request, *args, **kwargs)
        super(CreateMethodForm, self)._init_fields(readOnly=False)

    def clean_address(self):
        '''Check to make sure address is the correct format depending on the
        type of notification
        '''
        data = self.cleaned_data
        if data['type'] == constants.NotificationType.EMAIL:
            constants.EMAIL_VALIDATOR(data['address'])
        elif data['type'] == constants.NotificationType.WEBHOOK:
            constants.WEBHOOK_VALIDATOR(data['address'])
        elif data['type'] == constants.NotificationType.PAGERDUTY:
            pass

        return data['address']

    def handle(self, request, data):
        try:
            api.monitor.notification_create(
                request,
                name=data['name'],
                type=data['type'],
                address=data['address'],
                period=data['period'])
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


class EditMethodForm(BaseNotificationMethodForm):
    def __init__(self, request, *args, **kwargs):
        super(EditMethodForm, self).__init__(request, *args, **kwargs)
        super(EditMethodForm, self)._init_fields(readOnly=False)

    def handle(self, request, data):
        try:
            kwargs = {}
            kwargs['notification_id'] = self.initial['id']
            kwargs['name'] = data['name']
            kwargs['type'] = data['type']
            kwargs['address'] = data['address']
            kwargs['period'] = data['period']
            api.monitor.notification_update(
                request,
                **kwargs
            )
            messages.success(request,
                             _('Notification has been edited successfully.'))
        except Exception as e:
            exceptions.handle(request,
                              _('Unable to edit the notification: %s') % e)
            return False
        return True
