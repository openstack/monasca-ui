# Copyright 2013 Hewlett-Packard Development Company, L.P.
# Copyright 2016-2017 FUJITSU LIMITED
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

from django.urls import reverse
from unittest.mock import patch

from monitoring.alarmdefs import constants
from monitoring.test import helpers


INDEX_URL = reverse(constants.URL_PREFIX + 'index')
CREATE_URL = reverse(constants.URL_PREFIX + 'alarm_create', args=())
DETAIL_URL = reverse(constants.URL_PREFIX + 'alarm_detail', args=('12345',))
EDIT_URL = reverse(constants.URL_PREFIX + 'alarm_edit', args=('12345',))


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
