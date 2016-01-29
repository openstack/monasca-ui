'use strict';
angular.module('monitoring.controllers', [])
    .constant('CHICKLET_TO_ICON', {
        'chicklet-error': '/monitoring/img/critical-icon.png',
        'chicklet-warning': '/monitoring/img/warning-icon.png',
        'chicklet-unknown': '/monitoring/img/unknown-icon.png',
        'chicklet-success': '/monitoring/img/ok-icon.png',
        'chicklet-notfound': '/monitoring/img/notfound-icon.png'
    })
    .controller('timestampPickerController',[
      "$scope", "$window", "$location",
      function($scope, $window, $location){
        var offset = getTimezoneOffset(),
            queryParams = urlParams()

        $scope.currentFormat = undefined
        $scope.currentOffset = undefined

        $scope.setUp = setUp;

        function setUp(currentFormat){
            if(currentFormat){
                $scope.currentFormat = currentFormat
            }
            $scope.$watch('currentFormat', onFormatChange)
            if(queryParams['ts_mode'] === 'bl'){
                $scope.currentOffset = queryParams['ts_offset']
            }
        }

         function onFormatChange(nval,oval){
           var location;

           if (nval !== '' && nval !== oval){
             location = $location.path();

             // overwrite to new values
             queryParams['ts_mode'] = nval;
             if(nval === 'utc'){
               queryParams['ts_offset'] = 0
             } else {
               queryParams['ts_offset'] = offset;
             }

             location = location.concat('?', paramsToSearch(queryParams));

             $window.location = location;
           }
        }

        function urlParams(url) {
            url = url || window.location.href;
            if (!url || (url.indexOf("?") < 0 && url.indexOf("&") < 0)) {
                return {};
            }
            if (url.indexOf('#') > -1) {
                url = url.substr(0, url.indexOf('#'));
            }
            return urlDecode(url.substr(url.indexOf("?") + 1));
        }

        function paramsToSearch(queryParams){
            var str = '';

            angular.forEach(queryParams, function it(val, key){
                str = str.concat(key, '=', encodeURIComponent(val), '&');
            });

            str = str.substr(0, str.length-1);

            return str;
        }

        function urlDecode(string, overwrite) {
            var obj = {},
                pairs = string.split('&'),
                name,
                value;
            angular.forEach(pairs, function it(pair) {
                pair = pair.split('=');
                name = decodeURIComponent(pair[0]);
                value = decodeURIComponent(pair[1]);
                obj[name] = overwrite || !obj[name] ? value : [].concat(obj[name]).concat(value);
            });
            return obj;
        }

        function getTimezoneOffset() {
            var offset = new Date().getTimezoneOffset();
            var minutes = Math.abs(offset);
            var hours = Math.floor(minutes / 60);
            var prefix = offset < 0 ? "+" : "-";
            return prefix + hours;
        }

    }])
    .controller('monitoringController',[
      "$scope", "$http", "$timeout", "$location", "CHICKLET_TO_ICON",
      function ($scope, $http, $timeout, $location, CHICKLET_TO_ICON) {
        var base_url;

        $scope.fetchStatus = function(statics_url) {
            if(statics_url && !base_url){
                base_url = statics_url;
            }

            $http({method: 'GET', url: $location.absUrl().concat('status')}).
                success(function(data, status, headers, config) {
                  // this callback will be called asynchronously
                  // when the response is available
                    var i;
                    for (i=0; i < data.series.length; i++) {
                        var group = data.series[i];
                        for (var j in group.services) {
                            var service = group.services[j];
                            service.icon = getIcon(service.class);
                        }
                    }
                    $scope._serviceModel = data.series;
               }).
                error(function(data, status, headers, config) {
                    $scope.stop();
                });

        };

        function getIcon(status) {
            var url_suffix = CHICKLET_TO_ICON[status];
            if(url_suffix){
                return base_url + url_suffix;
            }
            return undefined;
        }

        $scope.onTimeout = function(){
            mytimeout = $timeout($scope.onTimeout,10000);
            $scope.fetchStatus();
        };
        var mytimeout = $timeout($scope.onTimeout,10000);

        $scope.stop = function(){
            $timeout.cancel(mytimeout);
        };

    }])
    .controller('alarmEditController', [
      "$scope", "$http", "$timeout", "$q",
      function ($scope, $http, $timeout, $q) {
        $scope.metrics = metricsList;
        $scope.metricNames = uniqueNames(metricsList, 'name');
        $scope.currentMetric = $scope.metricNames[0];
        $scope.currentFunction = "max";
        $scope.currentComparator = ">";
        $scope.currentThreshold = 0;
        $scope.matchingMetrics= [];
        $scope.tags = [];
        $scope.possibleDimensions = function(query) {
            var deferred = $q.defer();
            var dim = {}
            var dimList = []
            angular.forEach($scope.matchingMetrics, function(value, name) {
                for (var key in value.dimensions) {
                    if (value.dimensions.hasOwnProperty(key)) {
                        var dimStr = key + "=" + value.dimensions[key]
                        if (dimStr.indexOf(query) === 0) {
                            dim[dimStr] = dimStr;
                        }
                    }
                }
            });
            angular.forEach(dim, function(value, name) {
                dimList.push(value)
            });
            deferred.resolve(dimList);
            return deferred.promise;
        };
        $scope.metricChanged = function() {
            if ($scope.defaultTag.length > 0) {
                $scope.tags = [{text: $scope.defaultTag}];
            }
            $scope.saveDimension();
        }
        $scope.saveExpression = function() {
            $('#dimension').val($scope.formatDimension());
        }
        $scope.saveDimension = function() {
            $scope.saveExpression();

            var mm = []
            angular.forEach($scope.metrics, function(value, key) {
                if (value.name === $scope.currentMetric) {
                    var match = true;
                    for (var i = 0; i < $scope.tags.length; i++) {
                        var vals = $scope.tags[i]['text'].split('=');
                        if (value.dimensions[vals[0]] !== vals[1]) {
                            match = false;
                            break;
                        }
                    }
                    if (match) {
                        mm.push(value)
                    }
                }
            });
            $scope.matchingMetrics = mm
            $scope.dimnames = ['name', 'dimensions'];
            $('#match').val($scope.formatMatchBy());
        }
        $scope.formatDimension = function() {
            var dim = ''
            angular.forEach($scope.tags, function(value, key) {
                if (dim.length) {
                    dim += ','
                }
                dim += value['text']
            })
            return $scope.currentFunction + '(' + $scope.currentMetric + '{' + dim + '}) ' + $scope.currentComparator + ' ' + $scope.currentThreshold;
        }
        $scope.formatMatchBy = function() {
            var dimNames = {}
            for (var i = 0; i < $scope.matchingMetrics.length; i++) {
                for (var attrname in $scope.matchingMetrics[i].dimensions) { dimNames[attrname] = true; }
            }
            var matches = [];
            for (var attrname in dimNames) { matches.push(attrname); }
            return matches;
        }
        $scope.init = function(defaultTag) {
            if (defaultTag.length > 0) {
                $scope.tags = [{text: defaultTag}];
            }
            $scope.defaultTag = defaultTag;
            $scope.saveDimension();
        }

        function uniqueNames(input, key) {
            var unique = {};
            var uniqueList = [];
            for(var i = 0; i < input.length; i++){
                if(typeof unique[input[i][key]] == "undefined"){
                    unique[input[i][key]] = "";
                    uniqueList.push(input[i][key]);
                }
            }
            return uniqueList.sort();
        }
    }])
    .controller('alarmNotificationFieldController', NotificationField);

function NotificationField(){

    var vm = this;
    var allOptions = {};

    vm.empty = true;
    vm.list = [];
    vm.select = {
        model:null,
        options:[]
    };


    vm.init = function(data){
        data = JSON.parse(data);
        vm.empty = data.length === 0;
        data.forEach(prepareNotify);
    };
    vm.add = function(){
        if(vm.select.model){
            vm.list.push(allOptions[vm.select.model]);

            removeFromSelect();
            vm.select.model = null;
        }
    };
    vm.remove = function(id){
        for(var i = 0;i<vm.list.length;i+=1){
            if(vm.list[i].id === id){
                vm.list.splice(i, 1);
                vm.select.options.push(allOptions[id]);
                break;
            }
        }
        vm.select.model = null;
    };

    function prepareNotify(item){
        var selected = item[4]
        var notify = {
            id: item[0],
            label: item[1] +' ('+ item[2] +')',
            name: item[1],
            type: item[2],
            address: item[3]
        };
        allOptions[notify.id] = notify;
        if(selected){
            vm.list.push(notify);
        } else {
            vm.select.options.push(notify);
        }
    }

    function removeFromSelect(){
         var opts = vm.select.options;
         for(var i = 0;i<opts.length;i+=1){
            if(opts[i].id === vm.select.model){
                opts.splice(i, 1);
                break;
            }
         }
    }
}

NotificationField.$inject = [];

angular.module('monitoring.filters', [])
    .filter('spacedim', function () {
        return function(text) {
            if (typeof text == "string")
                return text;
            return JSON.stringify(text).split(',').join(', ');
        }
    })
