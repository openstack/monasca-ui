DASHBOARD = "monitoring"

# A list of applications to be added to INSTALLED_APPS.
ADD_INSTALLED_APPS = ['monitoring']

# A list of angular modules to be added as dependencies to horizon app.
ADD_ANGULAR_MODULES = ['monitoringApp']

# A list of javascript files to be included for all pages
ADD_JS_FILES = ['monitoring/js/app.js',
                'monitoring/js/filters.js',
                'monitoring/js/controllers.js',
                'monitoring/js/directives.js',
                'monitoring/js/services.js',
                'monitoring/js/ng-tags-input.js']

ADD_SCSS_FILES = [
    'monitoring/css/alarm-create.scss']

from monascaclient import exc
# A dictionary of exception classes to be added to HORIZON['exceptions'].
ADD_EXCEPTIONS = {
    'recoverable': (exc.HTTPUnProcessable, exc.HTTPConflict, exc.HTTPException),
    'not_found': (exc.HTTPNotFound,),
    'unauthorized': (exc.HTTPUnauthorized,),
}
