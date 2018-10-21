angular.module('trixStudent.directives', [])

.directive 'trixAriaChecked', ->
  return {
    restrict: 'A'
    scope: {
      'checked': '=trixAriaChecked'
    }
    controller: ($scope) ->

    link: (scope, element, attrs) ->
      updateAriaChecked = ->
        if scope.checked
          element.attr('aria-checked', 'true')
        else
          element.attr('aria-checked', 'false')

      updateAriaChecked()
      scope.$watch attrs.trixAriaChecked, (newValue, oldValue) ->
        updateAriaChecked()

      return
  }

.directive 'trixAssignmentList', ($http, $rootScope, $compile) ->
  return {
    restrict: 'E'
    replace: true

    link: (scope, element, attrs) ->
      updateAssignments = () ->
        url = new Url()
        url.query.updatelist = 1
        if scope.no_filter?
          url.query.no_filter = 1
        $http.get(url.toString())
          .then (response) ->
            if response.headers('hide-progress')
              $rootScope.$emit('assignments.hideProgress')
            else
              $rootScope.$emit('assignments.showProgress')
            compiled = $compile(response.data)(scope)
            element.empty()
            element.append(compiled)
          .catch (response) ->
            console.error('Failed to get list.')
      scope.$watch 'updateAssignmentList', () ->
        updateAssignments()
      return
  }
