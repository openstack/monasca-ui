from django.utils.translation import ugettext_lazy as _

# Services being monitored
MONITORING_SERVICES = [
    {'name': _('OpenStack Services'),
     'groupBy': 'service'},
    {'name': _('Servers'),
     'groupBy': 'hostname'}
]

# Grafana button titles/file names
GRAFANA_LINKS = [
    {'title': 'Dashboard', 'fileName': 'openstack.json'},
    {'title': 'Monasca Health', 'fileName': 'monasca.json'}
]
