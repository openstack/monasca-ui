# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 Nebula, Inc.
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

from django.utils.translation import ugettext_lazy as _
from monitoring.config import local_settings as settings

import horizon


class Monitoring(horizon.Dashboard):
    name = _("Monitoring")
    slug = "monitoring"
    panels = ('overview', 'alarmdefs', 'alarms', 'notifications',)
    default_panel = 'overview'
    policy_rules = (("monitoring", "monitoring:monitoring"),)
    permissions = (('openstack.services.' + settings.MONITORING_SERVICE_TYPE),)

horizon.register(Monitoring)
