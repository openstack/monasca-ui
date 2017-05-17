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

# NOTE(dmllr): Remove me when we require monascaclient >= 1.3.0

from monascaclient import exc
from openstack_dashboard.test.test_data import exceptions


def data(TEST):
    TEST.exceptions = exceptions.data

    monitoring_exception = exc.ClientException
    TEST.exceptions.monitoring = exceptions.create_stubbed_exception(
        monitoring_exception)
