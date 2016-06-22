# Copyright 2016 FUJITSU LIMITED
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

from django.utils.translation import ugettext as _  # noqa
from django.views.decorators.debug import sensitive_variables  # noqa

from horizon import exceptions
from horizon import forms
from horizon import workflows
from horizon.utils import memoized

from monitoring import api
from monitoring.alarmdefs import constants
from monitoring.alarmdefs import forms as ad_forms


class SetAlarmNotificationsAction(workflows.Action):
    notifications = ad_forms.NotificationField(
        label=_('Notifications'),
        required=False,
        widget=ad_forms.NotificationCreateWidget(),
        help_text=_('Notification methods. '
                    'Notifications can be sent when an alarm '
                    'state transition occurs.'))

    alarm_actions = ad_forms.NotificationField(
        label=_("Alarm Actions"),
        required=False,
        widget=forms.MultipleHiddenInput()
    )
    ok_actions = ad_forms.NotificationField(
        label=_("OK Actions"),
        required=False,
        widget=forms.MultipleHiddenInput()
    )
    undetermined_actions = ad_forms.NotificationField(
        label=_("Undetermined Actions"),
        required=False,
        widget=forms.MultipleHiddenInput()
    )

    class Meta(object):
        name = _('Notifications')
        help_text_template = ("monitoring/alarmdefs/"
                              "_create_ad_notification_help.html")

    def __init__(self, request, context, *args, **kwargs):
        super(SetAlarmNotificationsAction, self).__init__(
            request, context, *args, **kwargs
        )
        try:
            notifications = ad_forms._get_notifications(request)
            self.fields['notifications'].choices = notifications
        except Exception as e:
            exceptions.handle(request,
                              _('Unable to retrieve notifications: %s') % e)


_SEVERITY_CHOICES = [("LOW", _("Low")),
                     ("MEDIUM", _("Medium")),
                     ("HIGH", _("High")),
                     ("CRITICAL", _("Critical"))]


class SetAlarmDefinitionAction(workflows.Action):
    name = forms.CharField(label=_('Name'),
                           required=True,
                           max_length=250,
                           help_text=_('An unique name of the alarm.'))

    description = forms.CharField(label=_('Description'),
                                  required=False,
                                  help_text=_('A description of an alarm.'))

    severity = forms.ChoiceField(label=_('Severity'),
                                 choices=_SEVERITY_CHOICES,
                                 initial=_SEVERITY_CHOICES[0],
                                 widget=forms.SelectWidget,
                                 required=False,
                                 help_text=_('Severity of an alarm. Must be '
                                             'either LOW, MEDIUM, HIGH '
                                             'or CRITICAL. Default is LOW.'))

    class Meta(object):
        name = _('Details')
        help_text_template = ("monitoring/alarmdefs/"
                              "_create_ad_details_help.html")

    def clean(self):
        cleaned_data = super(SetAlarmDefinitionAction, self).clean()

        alarm_def_name = cleaned_data.get('name', '')
        is_name_valid = self._is_alarm_def_name_unique_validator(
            alarm_def_name)
        if not is_name_valid:
            self.add_error('name',
                           _('Alarm definition with %s name already exists'
                             % alarm_def_name))

    def _is_alarm_def_name_unique_validator(self, value):
        try:
            ret = self._get_alarm_def_by_name(value)
            return not (ret and len(ret))
        except Exception:
            exceptions.handle(request=self.request,
                              message=_('Failed to validate name'),
                              ignore=True)
        return True

    @memoized.memoized_method
    def _get_alarm_def_by_name(self, value):
        return api.monitor.alarmdef_get_by_name(self.request, value)


class SetAlarmDefinitionExpressionAction(workflows.Action):
    expression = ad_forms.ExpressionField(label=_("Expression"),
                                          required=True,
                                          widget=ad_forms.ExpressionWidget(''),
                                          help_text=_(
                                              'An alarm expression.'))

    match_by = forms.CharField(label=_('Match by'),
                               required=False,
                               widget=ad_forms.MatchByWidget(''),
                               help_text=_('The metric dimensions used '
                                           'to create unique alarms.'))

    class Meta(object):
        name = _('Expression')
        help_text_template = ("monitoring/alarmdefs/"
                              "_create_ad_expression_help.html")

    def __init__(self, request, context, *args, **kwargs):
        super(SetAlarmDefinitionExpressionAction, self).__init__(request,
                                                                 context,
                                                                 *args,
                                                                 **kwargs)

        try:
            self.fields['expression'].metrics = ad_forms._get_metrics(request)
        except Exception as ex:
            exceptions.handle(request, _('Unable to retrieve metrics'))


class SetDetailsStep(workflows.Step):
    action_class = SetAlarmDefinitionAction
    contributes = ('name', 'description', 'severity')
    template_name = 'monitoring/alarmdefs/workflow_step.html'


class SetExpressionStep(workflows.Step):
    action_class = SetAlarmDefinitionExpressionAction
    contributes = ('expression', 'match_by')
    template_name = 'monitoring/alarmdefs/workflow_step.html'

    def contribute(self, data, context):
        context = (super(SetExpressionStep, self)
                   .contribute(data, context))

        if 'expression' in data and data['expression']:
            context['expression'] = data['expression'].strip()

        if 'match_by' in data and data['match_by']:
            context['match_by'] = context['match_by'].split(',')
        else:
            context['match_by'] = []

        return context


class SetNotificationsStep(workflows.Step):
    action_class = SetAlarmNotificationsAction
    contributes = ('alarm_actions', 'ok_actions', 'undetermined_actions')
    template_name = 'monitoring/alarmdefs/workflow_step.html'


class AlarmDefinitionWorkflow(workflows.Workflow):
    slug = 'create_alarm_definition'
    name = _('Create Alarm Definition')
    finalize_button_name = _('Create Alarm Definition')
    success_message = _('Alarm definition %s has been created')
    failure_message = _('Unable to create alarm definition %s')
    success_url = constants.URL_PREFIX + 'index'
    wizard = True
    default_steps = (
        SetDetailsStep,
        SetExpressionStep,
        SetNotificationsStep
    )

    def format_status_message(self, message):
        name = self.context.get('name', _('Unknown name'))
        return message % name

    @sensitive_variables('alarm_actions',
                         'ok_actions',
                         'undetermined_actions')
    def handle(self, request, context):
        try:
            api.monitor.alarmdef_create(
                request,
                name=context['name'],
                expression=context['expression'],
                description=context['description'],
                severity=context['severity'],
                match_by=context['match_by'],
                alarm_actions=context['alarm_actions'],
                ok_actions=context['ok_actions'],
                undetermined_actions=context['undetermined_actions'],
            )
        except Exception as e:
            exceptions.handle(request, e, escalate=True)
            return False

        return True
