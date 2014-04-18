
from django.conf.urls.defaults import patterns, url

from .views import IndexView, AlertView, AlertHistoryView, AlertMeterView

urlpatterns = patterns(
    'openstack_dashboard.dashboards.admin.monitoring.views',
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^alert/(?P<service>[^/]+)/$', AlertView.as_view(), name='alert'),
    url(r'^alert/(?P<service>[^/]+)/history$', AlertHistoryView.as_view(), name='history'),
    url(r'^alert/(?P<service>[^/]+)/meters$', AlertMeterView.as_view(), name='meters'),
    )
