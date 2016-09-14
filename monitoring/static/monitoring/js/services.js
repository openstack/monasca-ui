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
    .module('monitoring.services', [])
    .factory('monExpressionBuilder', expressionBuilder);

function expressionBuilder() {

    return {
        asString: subExpressionToString
    };


    function subExpressionToString(subExpressions, withOp) {
        var tmp = [],
            exprAsStr;

        angular.forEach(subExpressions, function(expr) {
            exprAsStr = [
                withOp ? renderOp(expr) : '',
                expr.fun || '',
                expr.fun && '(',
                expr.metric ? expr.metric.name : '', renderDimensions(expr),
                (expr.deterministic ? ',deterministic': ''),
                expr.fun && ')',
                expr.cmp || '',
                expr.threshold === 0 ? 0 : expr.threshold || ''
            ].join('');
            tmp.push(exprAsStr);
        });

        return tmp.join('');
    }

    function renderDimensions(expr) {
        var tmp = [];

        if (angular.isUndefined(expr.dimensions) || !expr.dimensions.length){
            return tmp.join('');
        }

        tmp.push('{');
        tmp.push(expr.dimensions.join(','));
        tmp.push('}');

        return tmp.join('');
    }

    function renderOp(expr) {
        var tmp = [];
        if ('op' in expr) {
            tmp.push(' ');
            tmp.push(expr['op']);
            tmp.push(' ');
        }
        return tmp.join('');
    }
}
