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

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

# Service group names (global across all projects):
MONITORING_SERVICES_GROUPS = [
    {'name': _('OpenStack Services'), 'groupBy': 'service'},
    {'name': _('Servers'), 'groupBy': 'hostname'}
]

# Services being monitored
MONITORING_SERVICES = getattr(
    settings,
    'MONITORING_SERVICES_GROUPS',
    MONITORING_SERVICES_GROUPS
)

#
# Per project service groups.  If in this form,
# '*' will be applied to all projects not explicitly listed.
#
# Note the above form (flat) is supported for backward compatibility.
#
# MONITORING_SERVICES_GROUPS = [
#    {'admin': [
#         {'name': _('OpenStack Services'), 'groupBy': 'service'},
#         {'name': _('Servers'), 'groupBy': 'hostname'}]},
#    {'*': [
#         {'name': _('Services'), 'groupBy': 'service'},
#         {'name': _('Instances'), 'groupBy': 'hostname'}]},
# ]

MONITORING_SERVICE_VERSION = getattr(
    settings, 'MONITORING_SERVICE_VERSION', '2_0'
)
MONITORING_SERVICE_TYPE = getattr(
    settings, 'MONITORING_SERVICE_TYPE', 'monitoring'
)
MONITORING_ENDPOINT_TYPE = getattr(
    # NOTE(trebskit) # will default to OPENSTACK_ENDPOINT_TYPE
    settings, 'MONITORING_ENDPOINT_TYPE', None
)

# Grafana button titles/file names (global across all projects):
GRAFANA_LINKS = []
DASHBOARDS = getattr(settings, 'GRAFANA_LINKS', GRAFANA_LINKS)

#
# Horizon will link to the grafana home page when using Grafana2.
# For any Grafana version additional links to specific dashboards can be
# created in two formats.
# Flat:
# GRAFANA_LINKS = [ {'title': _('Dashboard'), 'path': 'openstack'} ]
#
# Per project: '*' will be applied to all projects not explicitly listed.
# GRAFANA_LINKS = [
#    {'admin': [
#        {'title': _('Dashboard'), 'path': 'openstack'}]},
#    {'*': [
#        {'title': _('OpenStack Dashboard'), 'path': 'project'}]}
# ]

GRAFANA_URL = getattr(settings, 'GRAFANA_URL', None)

ENABLE_KIBANA_BUTTON = getattr(settings, 'ENABLE_KIBANA_BUTTON', False)
KIBANA_POLICY_RULE = getattr(settings, 'KIBANA_POLICY_RULE',
                             'monitoring:kibana_access')
KIBANA_POLICY_SCOPE = getattr(settings, 'KIBANA_POLICY_SCOPE',
                              'monitoring')
KIBANA_HOST = getattr(settings, 'KIBANA_HOST', 'http://192.168.10.4:5601/')

OPENSTACK_SSL_NO_VERIFY = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
OPENSTACK_SSL_CACERT = getattr(settings, 'OPENSTACK_SSL_CACERT', None)

POLICY_FILES = getattr(settings, 'POLICY_FILES', {})
POLICY_FILES.update({'monitoring': 'monitoring_policy.json',}) # noqa
setattr(settings, 'POLICY_FILES', POLICY_FILES)
