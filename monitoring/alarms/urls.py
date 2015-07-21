# vim: tabstop=4 shiftwidth=4 softtabstop=4

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
from django.conf.urls import patterns  # noqa
from django.conf.urls import url  # noqa

from monitoring.alarms import views

urlpatterns = patterns(
    '',
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^alarm/filter/$',
        views.AlarmFilterView.as_view(),
        name='alarm_filter'),
    url(r'^alarm/(?P<service>[^/]+)/$',
        views.AlarmServiceView.as_view(),
        name='alarm'),
    url(r'^alarm/$',
        views.AlarmServiceView.as_view(),
        name='alarm_all'),
    url(r'^history/(?P<name>[^/]+)/(?P<id>[^/]+)$',
        views.AlarmHistoryView.as_view(),
        name='history'),

)
