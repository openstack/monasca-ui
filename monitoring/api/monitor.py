# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging

from django.conf import settings  # noqa
from monascaclient import client as monasca_client
from openstack_dashboard.api import base

LOG = logging.getLogger(__name__)


def format_parameters(params):
    parameters = {}
    for count, p in enumerate(params, 1):
        parameters['Parameters.member.%d.ParameterKey' % count] = p
        parameters['Parameters.member.%d.ParameterValue' % count] = params[p]
    return parameters


def monasca_endpoint(request):
    service_type = getattr(settings, 'MONITORING_SERVICE_TYPE', 'monitoring')
    endpoint = base.url_for(request, service_type)
    if endpoint.endswith('/'):
        endpoint = endpoint[:-1]
    return endpoint


def monascaclient(request, password=None):
    api_version = "2_0"
    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    cacert = getattr(settings, 'OPENSTACK_SSL_CACERT', None)
    endpoint = monasca_endpoint(request)
    LOG.debug('monascaclient connection created using token "%s" , url "%s"' %
              (request.user.token.id, endpoint))
    kwargs = {
        'token': request.user.token.id,
        'insecure': insecure,
        'ca_file': cacert,
        'username': request.user.username,
        'password': password
        # 'timeout': args.timeout,
        # 'ca_file': args.ca_file,
        # 'cert_file': args.cert_file,
        # 'key_file': args.key_file,
    }
    client = monasca_client.Client(api_version, endpoint, **kwargs)
    client.format_parameters = format_parameters
    return client


def alarm_list(request, marker=None, paginate=False):
    return monascaclient(request).alarms.list()


def alarm_list_by_service(request, service_name, marker=None, paginate=False):
    service_dim = {'service': service_name}
    return monascaclient(request).alarms.list(dimensions=service_dim)


def alarm_delete(request, alarm_id):
    return monascaclient(request).alarms.delete(alarm_id=alarm_id)


def alarm_history(request, alarm_id):
    return monascaclient(request).alarms.history(alarm_id=alarm_id)


def alarm_get(request, alarm_id):
    return monascaclient(request).alarms.get(alarm_id=alarm_id)


def alarm_patch(request, **kwargs):
    return monascaclient(request).alarms.patch(**kwargs)


def alarmdef_list(request, marker=None, paginate=False):
    return monascaclient(request).alarm_definitions.list()


def alarmdef_list_by_service(request, service_name, marker=None, paginate=False):
    service_dim = {'service': service_name}
    return monascaclient(request).alarm_definitions.list(dimensions=service_dim)


def alarmdef_delete(request, alarm_id):
    return monascaclient(request).alarm_definitions.delete(alarm_id=alarm_id)


def alarmdef_history(request, alarm_id):
    return monascaclient(request).alarm_definitions.history(alarm_id=alarm_id)


def alarmdef_get(request, alarm_id):
    return monascaclient(request).alarm_definitions.get(alarm_id=alarm_id)


def alarmdef_create(request, password=None, **kwargs):
    return monascaclient(request, password).alarm_definitions.create(**kwargs)


def alarmdef_update(request, **kwargs):
    return monascaclient(request).alarm_definitions.update(**kwargs)


def alarmdef_patch(request, **kwargs):
    return monascaclient(request).alarm_definitions.patch(**kwargs)


def notification_list(request, marker=None, paginate=False):
    return monascaclient(request).notifications.list()


def notification_delete(request, notification_id):
    return monascaclient(request).notifications.delete(
        notification_id=notification_id)


def notification_get(request, notification_id):
    return monascaclient(request).notifications. \
        get(notification_id=notification_id)


def notification_create(request, **kwargs):
    return monascaclient(request).notifications.create(**kwargs)


def notification_update(request, notification_id, **kwargs):
    return monascaclient(request).notifications. \
        update(notification_id=notification_id, **kwargs)


def metrics_list(request, marker=None, paginate=False):
    return monascaclient(request).metrics.list()
