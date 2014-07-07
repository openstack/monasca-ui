# The name of the panel to be added to HORIZON_CONFIG. Required.
PANEL = 'monitoring'
# The name of the dashboard the PANEL associated with. Required.
PANEL_DASHBOARD = 'overcloud'
# The name of the panel group the PANEL is associated with.
PANEL_GROUP = 'monitoring'

DEFAULT_PANEL = 'alarms'

# Python panel class of the PANEL to be added.
ADD_PANEL = \
    'monitoring.alarms.panel.Monitoring'

# A list of applications to be added to INSTALLED_APPS.
ADD_INSTALLED_APPS = ['monitoring', 'grafana']

# A list of angular modules to be added as dependencies to horizon app.
ADD_ANGULAR_MODULES = ['monitoringApp']

# A list of javascript files to be included for all pages
ADD_JS_FILES = ['monitoring/js/app.js',
                'monitoring/js/controllers.js',
                'monitoring/js/ng-tags-input.js']

from monclient import exc
# A dictionary of exception classes to be added to HORIZON['exceptions'].
ADD_EXCEPTIONS = {
    'recoverable': (exc.HTTPUnProcessable,),
    'not_found': (exc.HTTPNotFound,),
    'unauthorized': (exc.HTTPUnauthorized,),
}