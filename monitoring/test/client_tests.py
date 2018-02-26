# Copyright 2018 OP5 AB
# (c) Copyright 2018 SUSE LLC
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
#

from django.conf import settings as d_settings
from django.test.utils import override_settings
from mock import Mock
from mock import patch

from keystoneauth1.identity.generic import token
from monascaclient import client as mon_client

from monitoring.test import helpers
from monitoring.api.client import _get_auth_params_from_request
from monitoring.api.client import _get_to_verify
from monitoring.api.client import monascaclient as api_mon_client


def _mock_url_for(request, service_name):
    return getattr(request, service_name)


def _mock_get_auth_params(request=None):
    return (923, '22', 789, 55, 'monitoring_url', 'identity_url')


def _mock_request():
    request = Mock()
    request.user.user_domain_id = 923
    request.user.token.id = '22'
    request.user.tenant_id = 789
    request.user.token.project = {'domain_id': 55}
    request.monitoring = 'monitoring_url'
    request.identity = 'identity_url'
    return request


def _mock_client_args(verify):
    return ('2_0', '22', 789, 55, 923, verify, 'identity_url', 'monitoring_url')


def _expected_session_args(verify):
    return {
        'auth_url': 'identity_url', 'user_domain_id': 55, 'project_id': 789,
        'token': '22', 'endpoint': 'monitoring_url', 'verify': verify,
        'project_domain_id': 923
    }


def _mock_token():
    return token.Token('identity_url')


class ClientTests(helpers.TestCase):

    @override_settings(OPENSTACK_SSL_NO_VERIFY=False)
    @override_settings(OPENSTACK_SSL_CACERT='/etc/ssl/certs/some.crt')
    def test_ssl_verify_with_cert(self):
        insecure = getattr(d_settings, 'OPENSTACK_SSL_NO_VERIFY', False)
        cert = getattr(d_settings, 'OPENSTACK_SSL_CACERT', None)
        to_verify = _get_to_verify(insecure, cert)

        self.assertEqual(to_verify, '/etc/ssl/certs/some.crt')

    @override_settings(OPENSTACK_SSL_NO_VERIFY=True)
    def test_no_ssl_verify(self):
        insecure = getattr(d_settings, 'OPENSTACK_SSL_NO_VERIFY', False)
        cert = getattr(d_settings, 'OPENSTACK_SSL_CACERT', None)
        to_verify = _get_to_verify(insecure, cert)

        self.assertFalse(to_verify)

    def test_get_auth_params_from_request(self):
        mock_request = _mock_request()
        with patch('openstack_dashboard.api.base.url_for',
                   side_effect=_mock_url_for):
            auth_params = _get_auth_params_from_request(mock_request)

        self.assertEqual(
            auth_params,
            (923, '22', 789, 55, 'monitoring_url', 'identity_url'))

    @patch('monascaclient.client._get_session')
    def test_client_no_verify_params_for_session(self, mock_session):
        (
            version,
            token,
            project_id,
            user_domain_id,
            project_domain_id,
            verify,
            auth_url,
            endpoint
        ) = _mock_client_args(False)

        with patch('monascaclient.client._get_auth_handler') as mock_auth_handler:
            mock_token = _mock_token()
            mock_auth_handler.return_value = mock_token
            the_client = mon_client.Client(
                api_version=version,
                token=token,
                project_id=project_id,
                user_domain_id=user_domain_id,
                project_domain_id=project_domain_id,
                verify=verify,
                auth_url=auth_url,
                endpoint=endpoint
            )

        self.assertIsNotNone(the_client)
        mock_session.assert_called_with(mock_token, _expected_session_args(False))

    @patch('monascaclient.client._get_session')
    def test_client_verify_params_for_session(self, mock_session):
        cert = '/etc/ssl/certs/some.crt'
        (
            version,
            token,
            project_id,
            user_domain_id,
            project_domain_id,
            verify,
            auth_url,
            endpoint
        ) = _mock_client_args(cert)

        with patch('monascaclient.client._get_auth_handler') as mock_auth_handler:
            mock_token = _mock_token()
            mock_auth_handler.return_value = mock_token
            the_client = mon_client.Client(
                api_version=version,
                token=token,
                project_id=project_id,
                user_domain_id=user_domain_id,
                project_domain_id=project_domain_id,
                verify=verify,
                auth_url=auth_url,
                endpoint=endpoint
            )

        self.assertIsNotNone(the_client)
        mock_session.assert_called_with(mock_token, _expected_session_args(cert))

    @patch('monascaclient.client.Client')
    def test_client(self, mock_Client):
        with patch('openstack_dashboard.api.base.url_for',
                   side_effect=_mock_url_for):
            with patch('monitoring.api.client._get_auth_params_from_request',
                       side_effect=_get_auth_params_from_request):
                api_client = api_mon_client(_mock_request(), '2_0')
        self.assertIsNotNone(api_client)
        mock_Client.assert_called_with(
            api_version='2_0',
            auth_url='identity_url',
            endpoint='monitoring_url',
            project_domain_id=55,
            project_id=789,
            token='22',
            user_domain_id=923,
            verify='/etc/ssl/certs/some2.crt')
