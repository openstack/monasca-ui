'use strict';
angular.module('monitoring.controllers', [])
    .controller('monitoringController', function ($scope, $http, $timeout) {
         $scope.fetchStatus = function() {
            $http({method: 'GET', url: '/overcloud/status'}).
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
                  // reload page if there was an error, login may be required
                    window.top.location.reload(true)
                });
        }
        $scope.onTimeout = function(){
            mytimeout = $timeout($scope.onTimeout,10000);
            $scope.fetchStatus()
        }
        var mytimeout = $timeout($scope.onTimeout,10000);

        $scope.stop = function(){
            $timeout.cancel(mytimeout);
        }
    })
    .controller('alarmEditController', function ($scope, $http, $timeout, $q) {
        $scope.metrics = metricsList;
        $scope.currentMetric = $scope.metrics[0];
        $scope.possibleDimensions = function() {
            var deferred = $q.defer();
            deferred.resolve($scope.currentMetric["dimensions"]);
            return deferred.promise;
        };
        $scope.metricChanged = function() {
            if ($scope.defaultTag.length > 0) {
                $scope.tags = [{text: $scope.defaultTag}];
            }
            $scope.saveDimension();
        }
        $scope.saveDimension = function() {
            $('#dimension').val($scope.formatDimension());
        }
        $scope.formatDimension = function() {
            var dim = ''
            angular.forEach($scope.tags, function(value, key) {
                if (dim.length) {
                    dim += ','
                }
                dim += value['text']
            })
            return $scope.currentMetric['name'] + '{' + dim + '}';
        }
        $scope.init = function(defaultTag) {
            if (defaultTag.length > 0) {
                $scope.defaultTag = defaultTag;
                $scope.tags = [{text: $scope.defaultTag}];
            }
            $scope.saveDimension();
        }

    });

function getIcon(status) {
    if (status === 'chicklet-error')
        return '/static/monitoring/img/critical-icon.png'
    else if (status === 'chicklet-warning')
        return '/static/monitoring/img/warning-icon.png'
    else if (status === 'chicklet-unknown')
        return '/static/monitoring/img/unknown-icon.png'
    else if (status === 'chicklet-success')
        return '/static/monitoring/img/ok-icon.png'
    else if (status === 'chicklet-notfound')
        return '/static/monitoring/img/notfound-icon.png'
}