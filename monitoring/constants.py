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

from django.core import validators
from django.utils.translation import ugettext_lazy as _  # noqa


class NotificationType(object):
    SMS = "SMS"
    EMAIL = "EMAIL"

    CHOICES = [(EMAIL, _("Email")),
               (SMS, _("SMS")), ]

    @staticmethod
    def get_label(key):
        for choice in NotificationType.CHOICES:
            if choice[0] == key:
                return choice[1]
        return key

PHONE_VALIDATOR = validators.RegexValidator(
    regex=r"^\+[()0-9 ]{5,20}$",
    message=_("Address must contain a valid phone number."))
EMAIL_VALIDATOR = validators.EmailValidator(
    message=_("Address must contain a valid email address."))

URL_PREFIX = 'horizon:overcloud:monitoring:'
TEMPLATE_PREFIX = 'overcloud/monitoring/'

CRITICAL_ICON = '/static/monitoring/img/critical-icon.png'
WARNING_ICON = '/static/monitoring/img/warning-icon.png'
OK_ICON = '/static/monitoring/img/ok-icon.png'
UNKNOWN_ICON = '/static/monitoring/img/unknown-icon.png'
NOTFOUND_ICON = '/static/monitoring/img/notfound-icon.png'
