# Copyright 2016 Cray Inc. All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from django.test import TestCase
from django.test.utils import override_settings
from unittest.mock import Mock

import monitoring.alarms.tables


class GraphMetricLinkActionTests(TestCase):

    def test_get_link_url(self):
        table_mock = Mock()
        table_mock.request.build_absolute_uri.return_value = "http://foo/api/"

        link_action = monitoring.alarms.tables.GraphMetric(table=table_mock)

        link_url = link_action.get_link_url({
            'metrics': [
                {
                    'name': 'metric1',
                },
                {
                    'name': u'metric \u2461',
                }
            ]
        })

        self.assertEqual(
            link_url,
            r'/grafana/index.html#/dashboard/script/detail.js?'
            r'name=metric1'
            r'&threshold=[{"name": "metric1"}, {"name": "metric \u2461"}]'
            r'&api=http://foo/api/'
        )

    def test_allowed_grafana_links(self):
        allowed = self.get_allowed()
        self.assertEqual(allowed, False)

    @override_settings(GRAFANA_URL={'CustomRegion': '/grafana'})
    def test_allowed_grafana_links_nonempty(self):
        allowed = self.get_allowed()
        self.assertEqual(allowed, 'metrics')

    def get_allowed(self):
        table_mock = Mock()
        table_mock.request.build_absolute_uri.return_value = "http://foo/api/"
        link_action = monitoring.alarms.tables.GraphMetric(table=table_mock)
        return link_action.allowed(table_mock.request, {'metrics': 'metrics'})
