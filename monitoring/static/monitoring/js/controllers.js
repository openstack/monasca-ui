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
               queryParams['ts_offset'] = 0;
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
                    $scope._serviceModel = data.series;
               }).
                error(function(data, status, headers, config) {
                    $scope.stop();
                });

        };

        $scope.onTimeout = function(){
            mytimeout = $timeout($scope.onTimeout,10000);
            $scope.fetchStatus();
        };
        var mytimeout = $timeout($scope.onTimeout,10000);

        $scope.stop = function(){
            $timeout.cancel(mytimeout);
        };

    }])
    .controller('alarmNotificationFieldController',
        ['$rootScope', NotificationField]
    )
    .controller('alarmMatchByController',
        ['$q', '$rootScope', MatchByController]
    );

function MatchByController($q, $rootScope) {
    // model
    var vm = this;

    vm.matchBy = [];
    vm.matchByTags = [];

    // api
    vm.saveDimKey = saveDimKey;
    vm.possibleDimKeys = possibleDimKeys;

    function possibleDimKeys(query) {
        return $q(function(resolve, reject) {
            var dimList = [];
            angular.forEach(vm.matchBy, function(value) {
                if (value.indexOf(query) === 0) {
                    dimList.push(value);
                }
            });
            resolve(dimList);
        });
    }

    function saveDimKey() {
        var matchByTags = []
        for (var i = 0; i < vm.matchByTags.length; i++) {
            matchByTags.push(vm.matchByTags[i]['text'])
        }
        $('#id_match_by').val(matchByTags.join(','));
    }

    // init
    $rootScope.$on('$destroy', (function() {

        var watcher = $rootScope.$on('mon_match_by_changed', onMatchByChange);

        return function destroyer() {
            watcher();
        }

        function onMatchByChange(event, matchBy) {
            // remove from tags those match by that do not match
            vm.matchByTags = vm.matchByTags.filter(function filter(tag){
                return matchBy.indexOf(tag['text']) >= 0;
            });
            vm.matchBy = matchBy || [];
        }

    }()));
}

function NotificationField($rootScope) {

    var vm = this;
    var allOptions = {};
    var oldUndetermined = {};

    vm.empty = true;
    vm.list = [];
    vm.select = {
        model:null,
        options:[]
    };
    vm.isDeterministic = false;


    vm.init = function(data){
        data = JSON.parse(data);
        vm.empty = data.length === 0;
        data.forEach(prepareNotify);
    };
    vm.add = function(){
        var opt;
        if (vm.select.model) {
            opt = allOptions[vm.select.model];

            oldUndetermined[opt.id] = opt.undetermined;
            opt.undetermined = !vm.isDeterministic;

            vm.list.push(opt);

            removeFromSelect();
            vm.select.model = undefined;

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
        if (id in oldUndetermined) {
            delete oldUndetermined[id];
        }
    };

    $rootScope.$on('mon_deterministic_changed', onDeterministicChange);

    function prepareNotify(item){
        var selected = item[7]
        var notify = {
            id: item[0],
            label: item[1] +' ('+ item[2] +')',
            name: item[1],
            type: item[2],
            address: item[3],
            alarm: item[4],
            ok: item[5],
            undetermined: item[6]
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

    function onDeterministicChange(event, isDeterministic) {

        if (isDeterministic === vm.isDeterministic) {
            return;
        }

        vm.isDeterministic = isDeterministic;

        angular.forEach(vm.list, function(item) {
            if(!(item.id in oldUndetermined)){
                oldUndetermined[item.id] = [];
            }
            if (isDeterministic) {
                oldUndetermined[item.id] = item.undetermined;
                item.undetermined = !isDeterministic;
            } else {
                item.undetermined = oldUndetermined[item.id];
                delete oldUndetermined[item.id];
            }
        });
    }
}
