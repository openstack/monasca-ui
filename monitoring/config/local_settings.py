from django.utils.translation import ugettext_lazy as _

# Services being monitored
MONITORING_SERVICES = [
    {'name': _('OpenStack Services'),
     'groupBy': 'service'},
    {'name': _('Servers'),
     'groupBy': 'hostname'}
]
