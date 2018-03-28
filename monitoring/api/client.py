# Copyright 2017 Fujitsu LIMITED
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from horizon import exceptions
from horizon.utils import memoized

from oslo_log import log as logging

from openstack_dashboard.api import base

from monascaclient import client as mon_client
from monitoring.config import local_settings as settings

LOG = logging.getLogger(__name__)

INSECURE = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
CACERT = getattr(settings, 'OPENSTACK_SSL_CACERT', None)

KEYSTONE_SERVICE = 'identity'
MONITORING_SERVICE = getattr(settings, 'MONITORING_SERVICE_TYPE', 'monitoring')

VERSIONS = base.APIVersionManager(
    MONITORING_SERVICE,
    preferred_version=getattr(settings,
                              'OPENSTACK_API_VERSIONS',
                              {}).get(MONITORING_SERVICE, 2.0)
)
VERSIONS.load_supported_version(2.0, {'client': mon_client, 'version': '2_0'})


def _get_endpoint(request):
    try:
        endpoint = base.url_for(request,
                                service_type=settings.MONITORING_SERVICE_TYPE,
                                endpoint_type=settings.MONITORING_ENDPOINT_TYPE)
    except exceptions.ServiceCatalogException:
        endpoint = 'http://127.0.0.1:8070/v2.0'
        LOG.warning('Monasca API location could not be found in Service '
                    'Catalog, using default: {0}'.format(endpoint))
    return endpoint


def _get_auth_params_from_request(request):
    """Extracts the properties from the request object needed by the monascaclient
    call below. These will be used to memoize the calls to monascaclient
    """
    LOG.debug('Extracting intel from request')
    return (
        request.user.user_domain_id,
        request.user.token.id,
        request.user.tenant_id,
        request.user.token.project.get('domain_id'),
        base.url_for(request, MONITORING_SERVICE),
        base.url_for(request, KEYSTONE_SERVICE)
    )


def _get_to_verify(insecure, cacert):
    to_verify = cacert

    if insecure:
        to_verify = False

    return to_verify


@memoized.memoized_with_request(_get_auth_params_from_request)
def monascaclient(request_auth_params, version=None):

    (
        user_domain_id,
        token_id,
        project_id,
        project_domain_id,
        monasca_url,
        auth_url
    ) = request_auth_params

    # NOTE(trebskit) this is bit hacky, we should
    # go straight into using numbers as version representation
    version = (VERSIONS.get_active_version()['version']
               if not version else version)

    LOG.debug('Monasca::Client <Url: %s> <Version: %s>'
              % (monasca_url, version))

    to_verify = _get_to_verify(INSECURE, CACERT)

    c = mon_client.Client(api_version=version,
                          token=token_id,
                          project_id=project_id,
                          user_domain_id=user_domain_id,
                          project_domain_id=project_domain_id,
                          verify=to_verify,
                          auth_url=auth_url,
                          endpoint=monasca_url)
    return c
