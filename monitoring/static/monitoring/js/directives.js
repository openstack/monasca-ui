/*
 * Copyright 2016 FUJITSU LIMITED
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except
 * in compliance with the License. You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software distributed under the License
 * is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
 * or implied. See the License for the specific language governing permissions and limitations under
 * the License.
 */

'use strict';

angular
    .module('monitoring.directives', [
        'horizon.framework.widgets',
        'monitoring.filters',
        'monitoring.services',
        'gettext'
    ])
    .directive('monAlarmExpression',
        ['monitoringApp.staticPath', monAlarmExpressionsDirective]
    )
    .directive('monAlarmSubExpression',
        ['monitoringApp.staticPath', monAlarmSubExpressionDirective]
    );

function monAlarmExpressionsDirective(staticPath){

    return {
        restrict: 'E',
        scope: {
            metrics: '=metrics',
            functions: '=functions',
            operators: '=operators',
            comparators: '=comparators',
            connectable: '=connectable'
        },
        templateUrl: staticPath + 'expression/expression.tpl.html',
        controller: ['$q', '$scope', 'monExpressionBuilder', AlarmExpressionController],
        controllerAs: 'vm',
        bindToController: true
    };

    function AlarmExpressionController($q, $scope, monExpressionBuilder) {
        // private
        var vm = this,
            deterministic = false,
            matchBy = undefined;

        // scope
        vm.expression = '';
        vm.subExpressions = undefined;
        vm.expressionValid = true;

        // api
        vm.touch = touch;
        vm.addExpression = addExpression;
        vm.removeExpression = removeExpression;
        vm.reorderExpression = reorderExpression;

        // listen
        $scope.$on('$destroy', destroy);

        // init
        $scope.$applyAsync(init);

        function addExpression($event, $index) {
            if ($event) {
                $event.preventDefault();
            }

            vm.subExpressions.splice($index, 0, {});
            if ($index >= 1 && vm.subExpressions[$index - 1].$valid) {
                // hide previous expression
                // if it is valid
                vm.subExpressions[$index -1]['preview'] = true;
            }

            applyConnectable();

            return true;
        }

        function removeExpression($event, index) {
            if ($event) {
                $event.preventDefault();
            }
            vm.subExpressions.splice(index, 1);

            applyConnectable();
            touch();

            return true;
        }

        function reorderExpression($event, which, where) {
            $event.preventDefault();
            vm.subExpressions[where]['op'] = [
                vm.subExpressions[which]['op'],
                vm.subExpressions[which]['op'] = vm.subExpressions[where]['op']
            ][0];
            vm.subExpressions[where] = vm.subExpressions.splice(which, 1, vm.subExpressions[where])[0];

            applyConnectable();

            return true;
        }

        function touch() {
            var hasInvalid = false;
                expression = undefined;

            matchBy = [];
            deterministic = true;

            angular.forEach(vm.subExpressions, subExpressionIt);

            if (hasInvalid) {
                expression = undefined;
            } else {
                $scope.$emit('mon_match_by_changed', matchBy.sort());
                $scope.$emit('mon_deterministic_changed', deterministic);

                expression = monExpressionBuilder.asString(vm.subExpressions, true);

                // change preview only if valid
                vm.expression = expression;
            }

            // update that always, regardless if it's valid or not
            // for invalid case that will reset input's value to empty
            // disallowing form to be accepted by django
            $('#expression').val(expression);
            vm.expressionValid = !hasInvalid;

            return true;

            function subExpressionIt(expr){
                if (!expr.$valid) {
                    return !(hasInvalid = true);
                }

                angular.forEach(expr.matchBy || [], function it(mb){
                    if(matchBy.indexOf(mb) < 0){
                        matchBy.push(mb);
                    }
                });
                deterministic = deterministic && (expr.deterministic || false);

                return true;
            }
        }

        function init() {
            if(vm.metrics.length) {
                vm.subExpressions = [];
                vm.matchBy = [];

                addExpression(undefined, 0);
            }
        }

        function destroy() {
            delete vm.metrics;
            delete vm.expression;
            delete vm.subExpressions;
            delete vm.deterministic;
        }

        function applyConnectable() {
            var count = vm.subExpressions.length;

            switch(count) {
                case 1:
                    vm.subExpressions[0]['connectable'] = false;
                    break;
                default: {
                    angular.forEach(vm.subExpressions, function(expr, index) {
                        expr.connectable = index >= 1 && index < vm.subExpressions.length;
                        if (!expr.connectable) {
                            delete expr['op'];
                        }
                    });
                }
            }

        }
    }

}

function monAlarmSubExpressionDirective(staticPath) {
    return {
        restrict: 'E',
        require: '^monAlarmExpression',
        scope: {
            metrics: '=metrics',
            functions: '=functions',
            comparators: '=comparators',
            operators: '=operators',
            model: '=subExpression',
            connectable: '=connectable',
            preview: '=preview'
        },
        templateUrl: staticPath + 'expression/sub-expression.tpl.html',
        link: linkFn,
        controller: ['$q', '$scope', 'monExpressionBuilder', AlarmSubExpressionController],
        controllerAs: 'vm',
        bindToController: true
    };

    function linkFn(scope, el, attrs, monAlarmExpressions) {
        el.on('$destroy', (function(){

            var watcher = scope.$watch('vm.model', function(expr, oldExpr) {
                if (expr !== oldExpr) {
                    monAlarmExpressions.touch();
                }
            }, true);

            return function destroyer() {
                watcher();
            };

        }()));
    }

    function AlarmSubExpressionController($q, $scope, monExpressionBuilder) {
        var vm = this;

        vm.tags = [];
        vm.matchingMetrics = [];

        // api
        vm.possibleDimensions = possibleDimensions;
        vm.onMetricChanged = onMetricChanged;
        vm.onDimensionsUpdated = onDimensionsUpdated;

        vm.updateExpression = updateExpression;
        vm.resetExpression = resetExpression;
        vm.updateExpression = updateExpression;

        // init
        $scope.$on('$destroy', destroyerFactory());

        function opRemoverListener(nval) {
            if (vm.model && 'op' in vm.model && !nval) {
                delete vm.model['op'];
            }
        }

        function destroyerFactory() {

            var watcher = $scope.$watch('vm.model.connectable', opRemoverListener, true);

            return function destroyer() {
                watcher();

                delete vm.tags;
                delete vm.matchingMetrics;
                delete vm.model;
            }

        }

        function updateExpression() {
            var dim = [],
                formController = $scope.$$childHead.subExpressionForm;

            vm.model.$valid = !formController.$invalid;

            if (vm.model.$valid) {

                if (vm.tags.length > 0) {
                    angular.forEach(vm.tags, function(value, key) {
                        dim.push(value['text']);
                    });
                    vm.model.dimensions = dim;
                } else {
                    vm.model.dimensions = [];
                }

            }

        }

        function resetExpression() {
            vm.matchingMetrics = [];
            vm.tags = [];
        }

        function possibleDimensions(query) {
            return $q(function(resolve) {
                var dim = {},
                    dimList = [];

                angular.forEach(vm.matchingMetrics, function(value, name) {
                    for (var key in value.dimensions) {
                        if (value.dimensions.hasOwnProperty(key)) {
                            var dimStr = key + "=" + value.dimensions[key];
                            if (dimStr.indexOf(query) === 0) {
                                dim[dimStr] = dimStr;
                            }
                        }
                    }
                });

                angular.forEach(dim, function(value, name) {
                    dimList.push(value);
                });

                resolve(dimList);
            });
        }

        function onDimensionsUpdated() {
            onMetricChanged(vm.model.metric);
        }

        function onMetricChanged(metric) {
            handleMetricChanged(metric);
            updateExpression();
        }

        function handleMetricChanged(metric) {
            var mm = [],
                matchBy = [],
                tags = vm.tags || [];

            angular.forEach(vm.metrics, function(value, key) {
                if (value.name === metric.name) {
                    var match = true;
                    for (var i = 0; i < tags.length; i++) {
                        var vals = tags[i]['text'].split('=');
                        if (value.dimensions[vals[0]] !== vals[1]) {
                            match = false;
                            break;
                        }

                    }
                    if (match) {
                        mm.push(value);
                    }
                }
            });

            angular.forEach(mm, function(value, key){
                angular.forEach(value.dimensions, function(value, key){
                    if(matchBy.indexOf(key) < 0){
                        matchBy.push(key);
                    }
                });
            });

            vm.matchingMetrics = mm;
            vm.model.matchBy = matchBy.sort();

        }

    }

}
