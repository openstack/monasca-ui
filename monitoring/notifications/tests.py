from django.core import urlresolvers
from mock import patch, call  # noqa

from monitoring.test import helpers
from monitoring.notifications import constants


INDEX_URL = urlresolvers.reverse(
    constants.URL_PREFIX + 'index')
CREATE_URL = urlresolvers.reverse(
    constants.URL_PREFIX + 'notification_create')
EDIT_URL = urlresolvers.reverse(
    constants.URL_PREFIX + 'notification_edit',  args=('12345',))


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
        res = self.client.get(CREATE_URL)

        self.assertTemplateUsed(
            res, 'monitoring/notifications/_create.html')

    def test_notifications_edit(self):
        with patch('monitoring.api.monitor', **{
            'spec_set': ['notification_get'],
            'notification_get.return_value': {
                'alarm_actions': []
            }
        }) as mock:
            res = self.client.get(EDIT_URL)
            self.assertEqual(mock.notification_get.call_count, 1)

        self.assertTemplateUsed(
            res, 'monitoring/notifications/_edit.html')
