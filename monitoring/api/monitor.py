# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from oslo_log import log

from openstack_dashboard.contrib.developer.profiler import api as profiler

from monitoring.api import client

LOG = log.getLogger(__name__)


@profiler.trace
def alarm_list(request, offset=0, limit=10000, marker=None, paginate=False):
    result = client.monascaclient(request).alarms.list(offset=offset,
                                                       limit=limit,
                                                       sort_by='alarm_definition_name')
    return result['elements'] if type(result) is dict else result


@profiler.trace
def alarm_list_by_dimension(request, dimensions, offset=0, limit=10000,
                            marker=None, paginate=False):
    dim_dict = {}
    metric = None
    dimensions = dimensions.split(",")
    for item in dimensions:
        if '=' in item:
            name, value = item.split('=')
            if name == 'metric':
                metric = value
            else:
                dim_dict[name] = value
        else:
            dim_dict[item] = None
    if metric:
        result = client.monascaclient(request).alarms.list(offset=offset,
                                                        limit=limit,
                                                        metric_dimensions=dim_dict,
                                                        metric_name=metric)
    else:
        result = client.monascaclient(request).alarms.list(offset=offset,
                                                        limit=limit,
                                                        metric_dimensions=dim_dict)
    return result['elements'] if type(result) is dict else result


@profiler.trace
def alarm_show(request, alarm_id):
    result = client.monascaclient(request).alarms.get(alarm_id=alarm_id)
    return result


@profiler.trace
def alarm_delete(request, alarm_id):
    return client.monascaclient(request).alarms.delete(alarm_id=alarm_id)


@profiler.trace
def alarm_history(request, alarm_id, offset=0, limit=10000):
    result = client.monascaclient(request).alarms.history(alarm_id=alarm_id,
                                                       offset=offset,
                                                       limit=limit)
    return result['elements'] if type(result) is dict else result


@profiler.trace
def alarm_get(request, alarm_id):
    return client.monascaclient(request).alarms.get(alarm_id=alarm_id)


@profiler.trace
def alarm_patch(request, **kwargs):
    return client.monascaclient(request).alarms.patch(**kwargs)


@profiler.trace
def alarmdef_list(request, offset=0, limit=10000, marker=None, paginate=False):
    result = client.monascaclient(request).alarm_definitions.list(offset=offset,
                                                                  limit=limit,
                                                                  sort_by='name')
    return result['elements'] if type(result) is dict else result


@profiler.trace
def alarmdef_list_by_service(request, service_name, marker=None,
                             paginate=False):
    service_dim = {'service': service_name}
    result = client.monascaclient(request).alarm_definitions.list(
        dimensions=service_dim)
    return result['elements'] if type(result) is dict else result


@profiler.trace
def alarmdef_delete(request, alarm_id):
    return client.monascaclient(request).alarm_definitions.delete(
        alarm_id=alarm_id)


@profiler.trace
def alarmdef_history(request, alarm_id):
    return client.monascaclient(request).alarm_definitions.history(
        alarm_id=alarm_id)


@profiler.trace
def alarmdef_get(request, alarm_id):
    return client.monascaclient(request).alarm_definitions.get(alarm_id=alarm_id)


@profiler.trace
def alarmdef_get_by_name(request, name):
    return client.monascaclient(request).alarm_definitions.list(
        name=name,
        limit=1
    )


@profiler.trace
def alarmdef_create(request, **kwargs):
    return client.monascaclient(request).alarm_definitions.create(**kwargs)


@profiler.trace
def alarmdef_update(request, **kwargs):
    return client.monascaclient(request).alarm_definitions.update(**kwargs)


@profiler.trace
def alarmdef_patch(request, **kwargs):
    return client.monascaclient(request).alarm_definitions.patch(**kwargs)


@profiler.trace
def notification_list(request, offset=0, limit=10000, marker=None,
                      paginate=False):
    result = client.monascaclient(request).notifications.list(offset=offset,
                                                              limit=limit,
                                                              sort_by='name')
    return result['elements'] if type(result) is dict else result


@profiler.trace
def notification_delete(request, notification_id):
    return client.monascaclient(request).notifications.delete(
        notification_id=notification_id)


@profiler.trace
def notification_get(request, notification_id):
    return (client.monascaclient(request).notifications.
            get(notification_id=notification_id))


@profiler.trace
def notification_create(request, **kwargs):
    return client.monascaclient(request).notifications.create(**kwargs)


@profiler.trace
def notification_update(request, notification_id, **kwargs):
    return (client.monascaclient(request).notifications.
            update(notification_id=notification_id, **kwargs))


@profiler.trace
def notification_type_list(request, **kwargs):
    result = client.monascaclient(request).notificationtypes.list(**kwargs)
    return result['elements'] if type(result) is dict else result


@profiler.trace
def metrics_list(request, **kwargs):
    result = client.monascaclient(request).metrics.list(**kwargs)
    return result['elements'] if type(result) is dict else result


@profiler.trace
def metrics_measurement_list(request, **kwargs):
    result = client.monascaclient(request).metrics.list_measurements(**kwargs)
    return result['elements'] if type(result) is dict else result


@profiler.trace
def metrics_stat_list(request, **kwargs):
    result = client.monascaclient(request).metrics.list_statistics(**kwargs)
    return result['elements'] if type(result) is dict else result
