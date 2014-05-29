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

from django.conf import settings
from monclient import client as mon_client

LOG = logging.getLogger(__name__)


def format_parameters(params):
    parameters = {}
    for count, p in enumerate(params, 1):
        parameters['Parameters.member.%d.ParameterKey' % count] = p
        parameters['Parameters.member.%d.ParameterValue' % count] = params[p]
    return parameters


def monclient(request, password=None):
    api_version = "2_0"
    insecure = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
    cacert = getattr(settings, 'OPENSTACK_SSL_CACERT', None)
    endpoint = getattr(settings, 'MONITORING_ENDPOINT',
                       'http://192.168.10.4:8080/v2.0')
    project_id = getattr(settings, 'MONITORING_PROJECT',
                       '82510970543135')
    LOG.debug('monclient connection created using token "%s" and url "%s"' %
              (request.user.token.id, endpoint))
    kwargs = {
        'token': project_id,  # workaround API should be request.user.token.id
        'insecure': insecure,
        'ca_file': cacert,
        'username': request.user.username,
        'password': password
        #'timeout': args.timeout,
        #'ca_file': args.ca_file,
        #'cert_file': args.cert_file,
        #'key_file': args.key_file,
    }
    client = mon_client.Client(api_version, endpoint, **kwargs)
    client.format_parameters = format_parameters
    return client


def alarm_list(request, marker=None, paginate=False):
    return monclient(request).alarms.list()


def alarm_list_by_service(request, service_name, marker=None, paginate=False):
    service_dim = {'service': service_name}
    return monclient(request).alarms.list(dimensions=service_dim)


def alarm_delete(request, alarm_id):
    return monclient(request).alarms.delete(alarm_id=alarm_id)


def alarm_get(request, alarm_id):
    return monclient(request).alarms.get(alarm_id=alarm_id)


def alarm_create(request, password=None, **kwargs):
    return monclient(request, password).alarms.create(**kwargs)


def alarm_update(request, **kwargs):
    return monclient(request).alarms.update(**kwargs)


def notification_list(request, marker=None, paginate=False):
    return monclient(request).notifications.list()


def notification_delete(request, notification_id):
    return monclient(request).notifications.delete(notification_id)


def notification_get(request, notification_id):
    return monclient(request).notifications. \
        get(notification_id=notification_id)


def notification_create(request, **kwargs):
    return monclient(request).notifications.create(**kwargs)


def notification_update(request, notification_id, **kwargs):
    return monclient(request).notifications.update(notification_id, **kwargs)


def metrics_list(request, marker=None, paginate=False):
    return monclient(request).metrics.list()
