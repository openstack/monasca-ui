# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.conf import settings

URL_PREFIX = 'horizon:monitoring:overview:'
TEMPLATE_PREFIX = 'monitoring/overview/'

prefix = settings.STATIC_URL or ''
CRITICAL_ICON = prefix + 'monitoring/img/critical-icon.png'
WARNING_ICON = prefix + 'monitoring/img/warning-icon.png'
OK_ICON = prefix + 'monitoring/img/ok-icon.png'
UNKNOWN_ICON = prefix + 'monitoring/img/unknown-icon.png'
NOTFOUND_ICON = prefix + 'monitoring/img/notfound-icon.png'
