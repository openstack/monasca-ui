from django.core import urlresolvers
from mock import patch, call  # noqa

from monitoring.test import helpers
from monitoring.alarmdefs import constants


INDEX_URL = urlresolvers.reverse(
    constants.URL_PREFIX + 'index')
CREATE_URL = urlresolvers.reverse(
    constants.URL_PREFIX + 'alarm_create',  args=())
DETAIL_URL = urlresolvers.reverse(
    constants.URL_PREFIX + 'alarm_detail',  args=('12345',))


class AlarmDefinitionsTest(helpers.TestCase):
    def test_alarmdefs_get(self):
        with patch('monitoring.api.monitor', **{
            'spec_set': ['alarmdef_list'],
            'alarmdef_list.return_value': [],
        }) as mock:
            res = self.client.get(INDEX_URL)
            self.assertEqual(mock.alarmdef_list.call_count, 1)

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

        self.assertTemplateUsed(
            res, 'monitoring/alarmdefs/_create.html')

    def test_alarmdefs_detail(self):
        with patch('monitoring.api.monitor', **{
            'spec_set': ['alarmdef_get'],
            'alarmdef_get.return_value': {
                'alarm_actions': [],
                'apply_to': '1',
                'match_by': [],
            }
        }) as mock:
            res = self.client.get(DETAIL_URL)
            self.assertEqual(mock.alarmdef_get.call_count, 1)

        self.assertTemplateUsed(
            res, 'monitoring/alarmdefs/_detail.html')
