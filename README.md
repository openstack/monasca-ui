monasca-ui
==========

Monasca UI is implemented as a horizon plugin that adds panels to horizon. It is installed into devstack
by monasca-vagrant.

#Deployment Set Up

* git clone https://git.openstack.org/openstack/horizon.git  # clone horizon

* cd horizon
* Add git+https://git.openstack.org/openstack/monasca-ui.git  to requirements.txt
* Edit openstack_dashboard/settings.py to include the following two lines:
* import monitoring.enabled
* monitoring.enabled, #Add to the settings.update_dashboards list


#Development Environment Set Up

##Get the Code

```
git clone https://git.openstack.org/openstack/monasca-ui.git  # clone monasca-ui
git clone https://git.openstack.org/openstack/horizon.git  # clone horizon
git clone https://github.com/twc-openstack/grafana.git  # clone grafana
git clone https://github.com/twc-openstack/grafana-plugins.git # clone grafana plugins
```

##Set up Horizon

Since Monasca UI is a horizon plugin the first step is to get their development environment set up.

```
cd horizon
./run_tests.sh
cp openstack_dashboard/local/local_settings.py.example openstack_dashboard/local/local_settings.py
```

Pro Tip: Make sure you have horizon running correctly before proceeding.
For more details go to http://docs.openstack.org/developer/horizon/quickstart.html#setup

##Set up Monasca-UI

* Edit openstack_dashboard/local/local_settings.py to modify the OPENSTACK_HOST IP address to point to devstack.
* Add monasca-client to requirements.txt. Get the latest version from https://pypi.python.org/pypi/python-monascaclient
* Link monasca into Horizon:

```
cp ../monasca-ui/monitoring/enabled/_50_admin_add_monitoring_panel.py openstack_dashboard/enabled/.
ln -s ../monasca-ui/monitoring monitoring
./run_tests #load monasca-client into virtualenv
```

##Set up Grafana 2.6

* The v2.6.0-keystone branch of grafana is stable, as is v2.6.0 in grafana-plugins
* Copy grafana-plugins/datasources/monasca into the grafana/public/app/plugins/datasource/
* Use the grafana docs to build and deploy grafana
* http://docs.grafana.org/project/building_from_source/
* http://docs.grafana.org/installation/configuration/
* Copy monasca-ui/grafana-dashboards/* to /public/dashboards/ in your grafana deployment.
* Set GRAFANA_URL in the horizon settings

##Start Server

```
./run_tests.sh --runserver
```

##Removing notification panel
If you want to disable the notification panel copy over _70_remove_monasca_notification_panel to the openstack_dashboard/enabled directory

#License

Copyright (c) 2014 Hewlett-Packard Development Company, L.P.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0
    
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied.
See the License for the specific language governing permissions and
limitations under the License.

