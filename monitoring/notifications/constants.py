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

from django.core import validators
from django.utils.translation import gettext_lazy as _


class NotificationType(object):
    EMAIL = "EMAIL"
    WEBHOOK = "WEBHOOK"
    PAGERDUTY = "PAGERDUTY"


EMAIL_VALIDATOR = validators.EmailValidator(
    message=_("Address must contain a valid email address."))
WEBHOOK_VALIDATOR = validators.URLValidator(
    message=_("Address must contain a valid URL address."))

URL_PREFIX = 'horizon:monitoring:notifications:'
TEMPLATE_PREFIX = 'monitoring/notifications/'
