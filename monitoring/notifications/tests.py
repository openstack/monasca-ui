#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

from django.core import urlresolvers
from mock import patch, call  # noqa

from monitoring.test import helpers
from monitoring.notifications import constants


INDEX_URL = urlresolvers.reverse(
    constants.URL_PREFIX + 'index')
CREATE_URL = urlresolvers.reverse(
    constants.URL_PREFIX + 'notification_create')
EDIT_URL = urlresolvers.reverse(
    constants.URL_PREFIX + 'notification_edit', args=('12345',))


class AlarmsTest(helpers.TestCase):
    def test_index(self):
        with patch('monitoring.api.monitor', **{
            'spec_set': ['notification_list'],
            'notification_list.return_value': [],
        }) as mock:
            res = self.client.get(INDEX_URL)
            self.assertEqual(mock.notification_list.call_count, 2)

        self.assertTemplateUsed(
            res, 'monitoring/notifications/index.html')

    def test_notifications_create(self):
        with patch('monitoring.api.monitor', **{
            'spec_set': ['notification_type_list'],
            'notification_type_list.return_value': [],
        }) as mock:
            res = self.client.get(CREATE_URL)
            self.assertEqual(mock. notification_type_list.call_count, 1)

        self.assertTemplateUsed(
            res, 'monitoring/notifications/_create.html')

    def test_notifications_edit(self):
        with patch('monitoring.api.monitor', **{
            'spec_set': ['notification_get', 'notification_type_list'],
            'notification_get.return_value': {
                'alarm_actions': []
            },
            'notification_type_list.return_value': [],
        }) as mock:
            res = self.client.get(EDIT_URL)
            self.assertEqual(mock.notification_get.call_count, 1)
            self.assertEqual(mock.notification_type_list.call_count, 1)

        self.assertTemplateUsed(
            res, 'monitoring/notifications/_edit.html')
