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
    .module('monitoring.filters', [
        'monitoring.services'
    ])
    .filter('monUniqueMetric', uniqueMetricFilterFactory)
    .filter('monExpression', ['monExpressionBuilder', monExpressionFilterFactory]);

function monExpressionFilterFactory(monExpressionBuilder) {

    return function monExpressionFilter(value, withOp) {
        return monExpressionBuilder.asString([value], withOp);
    };

}

function uniqueMetricFilterFactory() {

    return function uniqueMetricFilter(arr) {
        return uniqueNames(arr, 'name');
    };

    function uniqueNames(input, key) {
        var unique = {};
        var uniqueList = [];
        for(var i = 0; i < input.length; i++){
            if(typeof unique[input[i][key]] === 'undefined'){
                unique[input[i][key]] = '';
                uniqueList.push(input[i]);
            }
        }
        return uniqueList;
    }
}
