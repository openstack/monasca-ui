# Copyright 2013 Hewlett-Packard Development Company, L.P.
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
from django.urls import re_path

from monitoring.config import local_settings as settings
from monitoring.overview import views


urlpatterns = [
    re_path(r'^$', views.IndexView.as_view(), name='index'),
    re_path(r'^status', views.StatusView.as_view(), name='status'),
    re_path(r'^proxy\/(?P<restpath>.*)$', views.MonascaProxyView.as_view()),
    re_path(r'^proxy', views.MonascaProxyView.as_view(), name='proxy'),
    re_path(r'^logs_proxy(?P<url>.*)$',
            views.KibanaProxyView.as_view(base_url=settings.KIBANA_HOST),
            name='kibana_proxy'
            )
]
