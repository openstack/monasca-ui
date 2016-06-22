'use strict';

// Declare app level module which depends on filters, and services
angular
    .module('monitoringApp', [
        'monitoring.controllers',
        'monitoring.directives',
        'monitoring.filters',
        'monitoring.services',
        'ngTagsInput'
    ])
    .config(config);

config.$inject = ['$provide', '$windowProvider'];

function config($provide, $windowProvider) {
    var path = $windowProvider.$get().STATIC_URL + 'monitoring/widgets/';
    $provide.constant('monitoringApp.staticPath', path);
}
