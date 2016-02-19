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

MONITORING_SERVICE_TYPE = getattr(
    settings, 'MONITORING_SERVICE_TYPE', 'monitoring'
)

# Grafana button titles/file names (global across all projects):
GRAFANA_LINKS = [
    {'title': _('Dashboard'), 'fileName': 'openstack.json'},
    {'title': _('Monasca Health'), 'fileName': 'monasca.json'}
]

DEFAULT_LINKS = GRAFANA_LINKS
DASHBOARDS = getattr(settings, 'GRAFANA_LINKS', GRAFANA_LINKS)

#
# Per project grafana button titles/file names.  If in this form,
# '*' will be applied to all projects not explicitly listed.
#
# Note the above form (flat) is supported for backward compatibility.
#
#GRAFANA_LINKS = [
#    {'admin': [
#        {'title': _('Dashboard'), 'fileName': 'openstack.json'},
#        {'title': _('RabbitMQ'), 'fileName': 'rabbit.json'},
#        {'title': _('Project Utilization'), 'fileName': 'libvirt.json'}]},
#    {'*': [
#        {'title': _('OpenStack Dashboard'), 'fileName': 'project.json'},
#        {'title': _('Add New Dashboard'), 'fileName': 'empty.json'}]}
#]

ENABLE_KIBANA_BUTTON = getattr(settings, 'ENABLE_KIBANA_BUTTON', False)
KIBANA_HOST = getattr(settings, 'KIBANA_HOST', 'http://192.168.10.4:5601/')

OPENSTACK_SSL_NO_VERIFY = getattr(settings, 'OPENSTACK_SSL_NO_VERIFY', False)
OPENSTACK_SSL_CACERT = getattr(settings, 'OPENSTACK_SSL_CACERT', None)
