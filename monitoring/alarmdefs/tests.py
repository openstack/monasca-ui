# Copyright 2013 Hewlett-Packard Development Company, L.P.
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

from django.core import urlresolvers
from mock import patch, call  # noqa

from monitoring.test import helpers
from monitoring.alarmdefs import constants
from monitoring.alarmdefs import views
from monitoring.alarmdefs import workflows


INDEX_URL = urlresolvers.reverse(
    constants.URL_PREFIX + 'index')
CREATE_URL = urlresolvers.reverse(
    constants.URL_PREFIX + 'alarm_create',  args=())
DETAIL_URL = urlresolvers.reverse(
    constants.URL_PREFIX + 'alarm_detail',  args=('12345',))
EDIT_URL = urlresolvers.reverse(
    constants.URL_PREFIX + 'alarm_edit',  args=('12345',))


class AlarmDefinitionsTest(helpers.TestCase):

    def test_alarmdefs_get(self):
        with patch('monitoring.api.monitor', **{
            'spec_set': ['alarmdef_list'],
            'alarmdef_list.return_value': [],
        }) as mock:
            res = self.client.get(INDEX_URL)
            self.assertEqual(mock.alarmdef_list.call_count, 2)

        self.assertTemplateUsed(
            res, 'monitoring/alarmdefs/alarm.html')

    def test_alarmdefs_create(self):
        with patch('monitoring.api.monitor', **{
            'spec_set': ['notification_list', 'metrics_list'],
            'notification_list.return_value': [],
            'metrics_list.return_value': [],
        }) as mock:
            res = self.client.get(CREATE_URL)
            self.assertEqual(mock.notification_list.call_count, 1)
            self.assertEqual(mock.metrics_list.call_count, 1)

        workflow = res.context['workflow']
        self.assertTemplateUsed(res, views.AlarmCreateView.template_name)
        self.assertEqual(res.context['workflow'].name,
                         workflows.AlarmDefinitionWorkflow.name)

        self.assertQuerysetEqual(
            workflow.steps,
            ['<SetDetailsStep: setalarmdefinitionaction>',
             '<SetExpressionStep: setalarmdefinitionexpressionaction>',
             '<SetNotificationsStep: setalarmnotificationsaction>'])

        # verify steps
        step = workflow.get_step('setalarmdefinitionaction')
        self.assertIsNotNone(step)

        step = workflow.get_step('setalarmdefinitionexpressionaction')
        self.assertIsNotNone(step)

        step = workflow.get_step('setalarmnotificationsaction')
        self.assertIsNotNone(step)

        self.assertContains(res, '<input class="form-control" id="id_name"')
        self.assertContains(res, '<input class="form-control" '
                                 'id="id_description"')
        self.assertContains(res, '<select class="form-control" '
                                 'id="id_severity"')

        self.assertContains(res, '<mon-alarm-expression')

        self.assertContains(res, '<input type="hidden" name="alarm_actions"')
        self.assertContains(res, '<input type="hidden" name="ok_actions"')
        self.assertContains(res, '<input type="hidden" '
                                 'name="undetermined_actions"')

    def test_alarmdefs_detail(self):
        with patch('monitoring.api.monitor', **{
            'spec_set': ['alarmdef_get'],
            'alarmdef_get.return_value': {
                'alarm_actions': [],
                'ok_actions': [],
                'undetermined_actions': [],
                'match_by': [],
            }
        }) as mock:
            res = self.client.get(DETAIL_URL)
            self.assertEqual(mock.alarmdef_get.call_count, 1)

        self.assertTemplateUsed(
            res, 'monitoring/alarmdefs/_detail.html')

    def test_alarmdefs_edit(self):
        with patch('monitoring.api.monitor', **{
            'spec_set': ['alarmdef_get'],
            'alarmdef_get.return_value': {
                'alarm_actions': [],
                'ok_actions': [],
                'undetermined_actions': [],
                'match_by': [],
            }
        }) as mock:
            res = self.client.get(EDIT_URL)
            self.assertEqual(mock.alarmdef_get.call_count, 1)

        self.assertTemplateUsed(
            res, 'monitoring/alarmdefs/_edit.html')
