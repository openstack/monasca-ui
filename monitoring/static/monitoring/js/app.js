'use strict';

// Declare app level module which depends on filters, and services
angular.module('monitoringApp', [
  'monitoring.controllers', 'ngRoute', 'ngGrid', 'ngAnimate'
]).
config(['$routeProvider', function($routeProvider) {
  $routeProvider.when('/health', {templateUrl: '/static/horizon/js/angular/monitoring/health.html', controller: 'monitoringController'});
  $routeProvider.when('/alarms/:alarmName', {templateUrl: '/static/horizon/js/angular/monitoring/alarms.html', controller: 'alarmController'});
  $routeProvider.otherwise({redirectTo: '/health'});
}]);
