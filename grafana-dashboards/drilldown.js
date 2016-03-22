/* global _ */

/*
 * Complex scripted dashboard
 * This script generates a dashboard object that Grafana can load. It also takes a number of user
 * supplied URL parameters (in the ARGS variable)
 *
 * Return a dashboard object, or a function
 */

'use strict';

// accessible variables in this scope
var window, document, ARGS, $, jQuery, moment, kbn;

// Setup some variables
var dashboard;

// All url parameters are available via the ARGS object
var ARGS;

// Intialize a skeleton with nothing but a rows array and service object
dashboard = {
  rows : [],
};

// Set a title
dashboard.title = 'Alarm drilldown';

// Set default time
// time can be overriden in the url using from/to parameters, but this is
// handled automatically in grafana core during dashboard initialization
dashboard.time = {
  from: "now-6h",
  to: "now"
};

var rows = 1;
var metricName = '';
var hostname = '';
var region = '';

if(!_.isUndefined(ARGS.rows)) {
  rows = parseInt(ARGS.rows, 10);
}

if(!_.isUndefined(ARGS.metric)) {
  metricName = ARGS.metric;
}

if(!_.isUndefined(ARGS.hostname)) {
  hostname = ARGS.hostname;
}

if(!_.isUndefined(ARGS.region)) {
  region = ARGS.region;
}

for (var i = 0; i < rows; i++) {

  dashboard.rows.push({
    title: 'Chart',
    height: '300px',
    panels: [
      {
        title: metricName,
        type: 'graph',
        span: 12,
        fill: 1,
        linewidth: 2,
        targets: [
          {
            "aggregator": "avg",
            "alias": hostname,
            "dimensions": [
              {
                "key": "hostname",
                "value": hostname
              },
              {
                "key": "region",
                "value": region
              }
            ],
            "metric": metricName,
            "period": "300",
          }
        ],
        tooltip: {
          shared: true
        }
      }
    ]
  });
}


return dashboard;
