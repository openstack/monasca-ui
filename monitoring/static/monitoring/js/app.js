'use strict';

// Declare app level module which depends on filters, and services
angular.module('monitoringApp', [
  'monitoring.controllers', 'monitoring.directives', 'ngRoute'
]).
config(['$routeProvider', function($routeProvider) {
  $routeProvider.when('/health', {templateUrl: '/static/monitoring/js/health.html', controller: 'monitoringController'});
  $routeProvider.when('/alarms/:alarmName', {templateUrl: '/static/monitoring/js/alarms.html', controller: 'alarmController'});
  $routeProvider.otherwise({redirectTo: '/health'});
}]);
