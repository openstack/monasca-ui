'use strict';
angular.module('monitoring.controllers', [])
    .controller('monitoringController', function ($scope, $http) {
         $scope.fetchStatus = function() {
            $http({method: 'GET', url: '/admin/monitoring/status'}).
                success(function(data, status, headers, config) {
                  // this callback will be called asynchronously
                  // when the response is available
                    var i;
                    for (i=0; i < data.series.length; i++) {
                        var group = data.series[i]
                        for (var j in group.services) {
                            var service = group.services[j]
                            service['icon'] = getIcon(service['class'])
                        }
                    }
                    $scope._serviceModel = data.series
               }).
                error(function(data, status, headers, config) {
                  // called asynchronously if an error occurs
                  // or server returns response with an error status.
                    alert("error")
                });
        }
    })
    .controller('alarmController', function($scope) {
        $scope.myData = [{name: "API Response Time", status: 'Normal'},
                         {name: "System Health", status: 'Normal'},
                         {name: "Database Access", status: 'Normal'},
                         {name: "Network Latency", status: 'Normal'},
                         {name: "Rabbit Health", status: 'Normal'}];
        $scope.gridOptions = { data: 'myData' ,
                columnDefs: [{field:'name', displayName:'Name'}, {field:'status', displayName:'Status'}]};
    });

function getIcon(status) {
    if (status === 'alert-error')
        return '/static/monitoring/img/critical-icon.png'
    else if (status === 'alert-warning')
        return '/static/monitoring/img/warning-icon.png'
    else if (status === 'alert-unknown')
        return '/static/monitoring/img/unknown-icon.png'
    else if (status === 'alert-success')
        return '/static/monitoring/img/ok-icon.png'
    else if (status === 'alert-notfound')
        return '/static/monitoring/img/notfound-icon.png'
}