from django.core import urlresolvers
from mock import patch, call  # noqa

from monitoring.test import helpers
from monitoring.alarms import constants


INDEX_URL = urlresolvers.reverse(
    constants.URL_PREFIX + 'index')
ALARMS_URL = urlresolvers.reverse(
    constants.URL_PREFIX + 'alarm',  args=('service=nova',))


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
