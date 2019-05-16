Team and repository tags
========================

.. image:: https://governance.openstack.org/tc/badges/monasca-ui.svg
    :target: https://governance.openstack.org/tc/reference/tags/index.html

monasca-ui
==========

Monasca UI is implemented as a Horizon plugin that adds panels to
Horizon. It is installed into devstack by the monasca-api plugin.

Deployment Set Up
=================

-  Clone Horizon:
   ``git clone https://git.openstack.org/openstack/horizon.git``

-  ``cd horizon``
-  Add ``git+https://git.openstack.org/openstack/monasca-ui.git`` to
   ``requirements.txt``.
-  Edit ``openstack_dashboard/settings.py`` to include the following two
   lines:

   -  ``import monitoring.enabled``
   -  ``monitoring.enabled,`` (Add this line to the
      ``settings.update_dashboards`` list.)

Development Environment Set Up
==============================

Get the Code
------------

::

   git clone https://git.openstack.org/openstack/monasca-ui.git  # clone monasca-ui
   git clone https://git.openstack.org/openstack/horizon.git  # clone horizon
   git clone https://github.com/monasca/grafana.git  # clone grafana
   git clone https://github.com/openstack/monasca-grafana-datasource.git # clone grafana plugins

Set up Horizon
--------------

Since Monasca UI is a Horizon plugin, the first step is to get their
development environment set up.

::

   cd horizon
   ./run_tests.sh
   cp openstack_dashboard/local/local_settings.py.example openstack_dashboard/local/local_settings.py

Pro Tip: Make sure you have Horizon running correctly before proceeding.
For more details visit: https://docs.openstack.org/horizon/latest/#setup

Set up Monasca-UI
-----------------

-  Edit ``openstack_dashboard/local/local_settings.py`` to modify the
   ``OPENSTACK_HOST`` IP address to point to devstack.
-  Add ``monasca-client`` to ``requirements.txt``. Get the latest
   version from: https://pypi.org/project/python-monascaclient
-  Link monasca into Horizon:

::

   ln -sf $(pwd)/../monasca-ui/monitoring/enabled/_50_admin_add_monitoring_panel.py \
       $(pwd)/openstack_dashboard/enabled/_50_admin_add_monitoring_panel.py
   ln -sf $(pwd)/../monasca-ui/monitoring/conf/monitoring_policy.json \
       $(pwd)/openstack_dashboard/conf/monitoring_policy.json
   ln -sfF $(pwd)/../monasca-ui/monitoring $(pwd)/monitoring
   ./run_tests #load monasca-client into virtualenv

Set up Grafana 4.1
------------------

-  The grafana4 branch of grafana is stable, as is master in
   monasca-grafana-datasource.
-  Copy ``monasca-grafana-datasource/`` into
   ``grafana/plugins/monasca-grafana-datasource/``.
-  Use the grafana docs to build and deploy grafana:

   -  http://docs.grafana.org/project/building_from_source/
   -  http://docs.grafana.org/installation/configuration/

-  Copy ``monasca-ui/grafana-dashboards/*`` to ``/public/dashboards/``
   in your grafana deployment.
-  Set ``GRAFANA_URL`` in the Horizon settings.

Start Server
------------

::

   ./run_tests.sh --runserver

Style checks
------------

To check if the code follows python coding style, run the following
command from the root directory of this project:

::

   $ tox -e pep8

Coverage checks
---------------

To measure the code coverage, run the following command from the root
directory of this project:

::

   $ tox -e cover

Unit tests
----------

To run all the unit test cases, run the following command from the root
directory of this project:

::

   $ tox -e py27,py35
