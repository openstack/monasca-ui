from django.core import urlresolvers
from mock import patch, call  # noqa

from monitoring.test import helpers
from monitoring.alarms import constants


INDEX_URL = urlresolvers.reverse(
    constants.URL_PREFIX + 'index')
ALARMS_URL_BY_DIMENSION = urlresolvers.reverse(
    constants.URL_PREFIX + 'alarm',  args=('nova',))
ALARMS_URL = urlresolvers.reverse(
    constants.URL_PREFIX + 'alarm',  args=('all',))

class AlarmsTest(helpers.TestCase):
    def test_alarms_get_by_dimension(self):
        with patch('monitoring.api.monitor', **{
            'spec_set': ['alarm_list_by_dimension'],
            'alarm_list_by_dimension.return_value': [],
        }) as mock:
            res = self.client.get(ALARMS_URL_BY_DIMENSION)
            self.assertEqual(mock.alarm_list_by_dimension.call_count, 2)

        self.assertTemplateUsed(
            res, 'monitoring/alarms/alarm.html')

    def test_alarms_get(self):
        with patch('monitoring.api.monitor', **{
            'spec_set': ['alarm_list'],
            'alarm_list.return_value': [],
        }) as mock:
            res = self.client.get(ALARMS_URL)
            self.assertEqual(mock.alarm_list.call_count, 2)

        self.assertTemplateUsed(
            res, 'monitoring/alarms/alarm.html')
