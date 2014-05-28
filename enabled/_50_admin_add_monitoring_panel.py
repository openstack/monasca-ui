# The name of the panel to be added to HORIZON_CONFIG. Required.
PANEL = 'monitoring'
# The name of the dashboard the PANEL associated with. Required.
PANEL_DASHBOARD = 'overcloud'
# The name of the panel group the PANEL is associated with.
PANEL_GROUP = 'default'

DEFAULT_PANEL = 'monitoring'

# Python panel class of the PANEL to be added.
ADD_PANEL = \
    'monitoring.panel.Monitoring'

# A list of applications to be added to INSTALLED_APPS.
ADD_INSTALLED_APPS = ['monitoring']

# A list of angular modules to be added as dependencies to horizon app.
#ADD_ANGULAR_MODULE = ['monitoringApp']
