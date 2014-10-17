from django.core import urlresolvers
from mock import patch, call  # noqa

from monitoring.test import helpers
from monitoring.alarms import constants


INDEX_URL = urlresolvers.reverse(
    constants.URL_PREFIX + 'index')
ALARMS_URL = urlresolvers.reverse(
    constants.URL_PREFIX + 'alarm',  args=('service=nova',))
CREATE_URL = urlresolvers.reverse(
    constants.URL_PREFIX + 'alarm_create',  args=('nova',))
DETAIL_URL = urlresolvers.reverse(
    constants.URL_PREFIX + 'alarm_detail',  args=('12345',))


class AlarmsTest(helpers.TestCase):
    def test_alarms_get(self):
        with patch('monitoring.api.monitor', **{
            'spec_set': ['alarm_list'],
            'alarm_list.return_value': [],
        }) as mock:
            res = self.client.get(ALARMS_URL)
            self.assertEqual(mock.alarm_list.call_count, 1)

        self.assertTemplateUsed(
            res, 'monitoring/alarms/alarm.html')

    def test_alarms_create(self):
        with patch('monitoring.api.monitor', **{
            'spec_set': ['notification_list', 'metrics_list'],
            'notification_list.return_value': [],
            'metrics_list.return_value': [],
        }) as mock:
            res = self.client.get(CREATE_URL)
            self.assertEqual(mock.notification_list.call_count, 1)
            self.assertEqual(mock.metrics_list.call_count, 1)

        self.assertTemplateUsed(
            res, 'monitoring/alarms/_create.html')

    def test_alarms_detail(self):
        with patch('monitoring.api.monitor', **{
            'spec_set': ['alarm_get'],
            'alarm_get.return_value': {
                'alarm_actions': []
            }
        }) as mock:
            res = self.client.get(DETAIL_URL)
            self.assertEqual(mock.alarm_get.call_count, 1)

        self.assertTemplateUsed(
            res, 'monitoring/alarms/_detail.html')
