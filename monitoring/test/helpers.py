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

import os
import unittest
import warnings

from django.core.handlers import wsgi
import mock
from openstack_dashboard.test import helpers

from monitoring.test.test_data import utils as test_data_utils


# Makes output of failing mox tests much easier to read.
wsgi.WSGIRequest.__repr__ = lambda self: "<class 'django.http.HttpRequest'>"

# Silences the warning about with statements.
warnings.filterwarnings('ignore', 'With-statements now directly support '
                        'multiple context managers', DeprecationWarning,
                        r'^tuskar_ui[.].*[._]tests$')


def create_stubs(stubs_to_create=None):
    if stubs_to_create is None:
        stubs_to_create = {}
    return helpers.create_stubs(stubs_to_create)


class MonitoringTestsMixin(object):
    def _setup_test_data(self):
        super(MonitoringTestsMixin, self)._setup_test_data()
        test_data_utils.load_test_data(self)
        self.policy_patcher = mock.patch(
            'openstack_auth.policy.check', lambda action, request: True)
        self.policy_check = self.policy_patcher.start()


@unittest.skipIf(os.environ.get('SKIP_UNITTESTS', False),
                 "The SKIP_UNITTESTS env variable is set.")
class TestCase(MonitoringTestsMixin, helpers.TestCase):
    pass


class BaseAdminViewTests(MonitoringTestsMixin, helpers.BaseAdminViewTests):
    pass


class APITestCase(MonitoringTestsMixin, helpers.APITestCase):
    pass
