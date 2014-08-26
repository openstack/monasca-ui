from django.core import urlresolvers
from mock import patch, call  # noqa

from monitoring.test import helpers
from monitoring.overview import constants


INDEX_URL = urlresolvers.reverse(
    constants.URL_PREFIX + 'index')


class OverviewTest(helpers.TestCase):
    def test_index_get(self):
        res = self.client.get(INDEX_URL)
        self.assertTemplateUsed(
            res, 'monitoring/overview/index.html')
        self.assertTemplateUsed(res, 'monitoring/overview/monitor.html')

