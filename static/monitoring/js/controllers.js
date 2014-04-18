'use strict';
angular.module('monitoring.controllers', [])
    .controller('monitoringController', function ($scope) {
          $scope._serviceModel = [{'name': 'Platform Services',
           'services': [{'name': 'MaaS',
                         'display': 'MaaS'},
                        {'name': 'DBaaS',
                         'display': 'DBaaS'},
                        {'name': 'LBaaS',
                         'display': 'LBaaS'},
                        {'name': 'DNSaaS',
                         'display': 'DNSaaS'},
                        {'name': 'MSGaaS',
                         'display': 'MSGaaS'},
                        ]},
          {'name': 'The OverCloud Services',
           'services': [{'name': 'nova',
                         'display': 'Nova'},
                        {'name': 'swift',
                         'display': 'Swift'},
                        {'name': 'bock',
                         'display': 'Cinder'},
                        {'name': 'glance',
                         'display': 'Glance'},
                        {'name': 'quantum',
                         'display': 'Neutron'},
                        {'name': 'mysql',
                         'display': 'MySQL'},
                        {'name': 'rabbitmq',
                         'display': 'RabbitMQ'},
                        ]},
          {'name': 'The UnderCloud Services',
           'services': [{'name': 'nova',
                         'display': 'Nova'},
                        {'name': 'swift',
                         'display': 'Cinder'},
                        {'name': 'glance',
                         'display': 'Glance'},
                        {'name': 'horizon',
                         'display': 'Horizon'},
                        ]},
          {'name': 'Network Services',
           'services': [{'name': 'dhcp',
                         'display': 'DHCP'},
                        {'name': 'dns',
                         'display': 'DNS'},
                        {'name': 'dns-servers',
                         'display': 'DNS Servers'},
                        {'name': 'http',
                         'display': 'http'},
                        {'name': 'web_proxy',
                         'display': 'Web Proxy'}
                        ]}
            ]
        $scope.setStatus = function() {
            var i;
            for (i=0; i < $scope._serviceModel.length; i++) {
                var group = $scope._serviceModel[i]
                for (var j in group.services) {
                    var service = group.services[j]
                    service['class'] = getRandomStatusValue()
                    service['icon'] = getIcon(service['class'])
                }
            }
        };
        $scope.serviceModel = function() {
            $scope.setStatus()
            return $scope._serviceModel
        }
        $scope.current = 1;
        $scope.showService = function(ev) {
            // href="#/alarms/{{service.name}}"
            console.log(ev.clientX, ev.clientY);
            $("#current"+$scope.current)[0].style.webkitTransform = "scale3d(10, 10, +1)"
            //$("#current"+$scope.current).style.opacity = "0"
            //$("#current"+$scope.current).style.visibility = false
            $scope.current += 1;
            $("#current"+$scope.current)[0].style.webkitTransform = "translate3d(0,-400px,-1)"
        };
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

function getRandomStatusValue() {
    var distribution = [
        {prob:.04, value:'alert-error'},
        {prob:.04, value:'alert-warning'},
        {prob:.04, value:'alert-unknown'},
        {value:'alert-success'},
    ]
    var num = Math.random()
    for (var i=0; i < distribution.length - 1; i++) {
        if (num < distribution[i]["prob"])
            return distribution[i]["value"]
        num = num - distribution[i]["prob"]
    }
    return distribution[distribution.length - 1]["value"]
}

function getIcon(status) {
    if (status === 'alert-error')
        return '/static/dashboard/img/critical-icon.png'
    else if (status === 'alert-warning')
        return '/static/dashboard/img/warning-icon.png'
    else if (status === 'alert-unknown')
        return '/static/dashboard/img/unknown-icon.png'
    else if (status === 'alert-success')
        return '/static/dashboard/img/ok-icon.png'
    else if (status === 'alert-notfound')
        return '/static/dashboard/img/notfound-icon.png'
}