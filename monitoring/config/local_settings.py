from django.utils.translation import ugettext_lazy as _

# Services being monitored
MONITORING_SERVICES = [
    {'name': _('OpenStack Services'),
     'groupBy': 'service'},
    {'name': _('Servers'),
     'groupBy': 'hostname'}
]

# Grafana button titles/file names (global across all projects):
GRAFANA_LINKS = [
    {'title': 'Dashboard', 'fileName': 'openstack.json'},
    {'title': 'Monasca Health', 'fileName': 'monasca.json'}
]

#
# Per project grafana button titles/file names.  If in this form,
# '*' will be applied to all projects not explicitly listed.
#
# Note the above form (flat) is supported for backward compatibility.
#
#GRAFANA_LINKS = [
#    {'admin': [
#        {'title': 'Dashboard', 'fileName': 'openstack.json'},
#        {'title': 'RabbitMQ', 'fileName': 'rabbit.json'},
#        {'title': 'Project Utilization', 'fileName': 'libvirt.json'}]},
#    {'*': [
#        {'title': 'OpenStack Dashboard', 'fileName': 'project.json'},
#        {'title': 'Add New Dashboard', 'fileName': 'empty.json'}]}
#]
