(function() {
  angular.module('trixStudent', ['ngCookies', 'ngRoute', 'ngSanitize', 'ui.bootstrap', 'trixStudent.directives', 'trixStudent.assignments.controllers']).config([
    '$httpProvider',
    function($httpProvider) {
      $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
      return $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    }
  ]).run([
    '$http',
    '$cookies',
    function($http,
    $cookies) {
      return $http.defaults.headers.common['X-CSRFToken'] = $cookies.csrftoken;
    }
  ]);

}).call(this);

(function() {
  angular.module('trixStudent.assignments.controllers', ['ngRoute', 'ngSanitize', 'ngAnimate']).controller('AddTagCtrl', [
    '$scope',
    '$window',
    function($scope,
    $window) {
      $scope.tagToAdd = '';
      $scope.negative = false;
      $scope.addTag = function() {
        var currentUrl,
    tags;
        currentUrl = new Url();
        tags = currentUrl.query.tags;
        if ($scope.negative) {
          $scope.tagToAdd = '-' + $scope.tagToAdd;
        }
        if ((tags != null) && tags !== '') {
          tags = tags + ',' + $scope.tagToAdd;
        } else {
          tags = $scope.tagToAdd;
        }
        currentUrl.query.tags = tags;
        delete currentUrl.query['page'];
        return $window.location.href = currentUrl.toString();
      };
    }
  ]).controller('RemoveTagCtrl', [
    '$scope',
    '$window',
    function($scope,
    $window) {
      return $scope.removeTag = function(tagToRemove) {
        var currentUrl,
    index,
    tags,
    tagsArray;
        currentUrl = new Url();
        tags = currentUrl.query.tags;
        tagsArray = tags.split(',');
        index = tagsArray.indexOf(tagToRemove);
        tagsArray.splice(index,
    1);
        tags = tagsArray.join(',');
        currentUrl.query.tags = tags;
        delete currentUrl.query['page'];
        return $window.location.href = currentUrl.toString();
      };
    }
  ]).controller('SolutionCtrl', [
    '$scope',
    function($scope) {
      return $scope.isVisible = false;
    }
  ]).controller('AssignmentCtrl', [
    '$scope',
    '$http',
    '$rootScope',
    function($scope,
    $http,
    $rootScope) {
      $scope.howsolved = null;
      $scope.saving = false;
      $scope.buttonClass = 'btn-default';
      $scope.boxClass = '';
      $scope.$watch('howsolved',
    function(newValue) {
        if (newValue === 'bymyself') {
          $scope.buttonClass = 'btn-success';
          $scope.boxClass = 'trix-assignment-solvedbymyself';
        } else if (newValue === 'withhelp') {
          $scope.buttonClass = 'btn-warning';
          $scope.boxClass = 'trix-assignment-solvedwithhelp';
        } else {
          $scope.buttonClass = 'btn-default';
          $scope.boxClass = 'trix-assignment-notsolved';
        }
        // Tell AssignmentListProgressController to reload
        $rootScope.$emit('assignments.progressChanged');
      });
      $scope._getApiUrl = function() {
        return '/assignment/howsolved/' + $scope.assignment_id;
      };
      $scope._showError = function(message) {
        // TODO: Use bootstrap modal and a scope variable
        $scope.saving = false;
        return alert(message);
      };
      $scope._updateHowSolved = function(howsolved) {
        var data;
        $scope.saving = true;
        data = {
          howsolved: howsolved
        };
        return $http.post($scope._getApiUrl(),
    data).then(function(response) {
          $scope.saving = false;
          return $scope.howsolved = response.data.howsolved;
        }).catch(function(response) {
          console.log(response);
          return $scope._showError('An error occurred!');
        });
      };
      $scope.solvedOnMyOwn = function() {
        return $scope._updateHowSolved('bymyself');
      };
      $scope.solvedWithHelp = function() {
        return $scope._updateHowSolved('withhelp');
      };
      return $scope.notSolved = function() {
        $scope.saving = true;
        return $http.delete($scope._getApiUrl()).then(function(response) {
          $scope.saving = false;
          return $scope.howsolved = null;
        }).catch(function(response) {
          if (response.status === 404) { // Handle 404 just like 200
            $scope.saving = false;
            return $scope.howsolved = null;
          } else {
            return $scope._showError('An error occurred!');
          }
        });
      };
    }
  ]).controller('AssignmentListProgressController', [
    '$scope',
    '$http',
    '$rootScope',
    '$timeout',
    function($scope,
    $http,
    $rootScope,
    $timeout) {
      var apiUrl,
    unbindProgressChanged,
    unbindProgressHide,
    unbindProgressShow;
      $scope.loading = true;
      $scope.hideProgress = false;
      apiUrl = new Url();
      apiUrl.query.progressjson = '1';
      $scope.levelUpAlert = false;
      $scope.levelDownAlert = false;
      $scope._loadProgress = function() {
        $scope.loading = true;
        return $http.get(apiUrl.toString()).then(function(response) {
          $scope.loading = false;
          $scope.solvedPercentage = response.data.percent;
          $scope.experience = response.data.experience;
          // Call for reloading assignments if user leveled up or down
          if (response.data.level !== $scope.level && ($scope.level != null)) {
            $rootScope.$emit('assignmentList.updateList');
            if (response.data.level > $scope.level) {
              $scope.levelUpAlert = true;
              $timeout(function() {
                return $scope.levelUpAlert = false;
              },
    3000);
            } else {
              $scope.levelDownAlert = true;
              $timeout(function() {
                return $scope.levelDownAlert = false;
              },
    3000);
            }
          }
          $scope.level = response.data.level;
          $scope.level_progress = response.data.level_progress;
          if ($scope.solvedPercentage > 1 && $scope.solvedPercentage < 20) {
            return $scope.progressBarClass = 'progress-bar-danger';
          } else if ($scope.solvedPercentage < 45) {
            return $scope.progressBarClass = 'progress-bar-warning';
          } else if ($scope.solvedPercentage === 100) {
            return $scope.progressBarClass = 'progress-bar-success';
          } else {
            return $scope.progressBarClass = '';
          }
        }).catch(function(response) {
          return console.error('Failed to load progress:',
    response.statusText);
        });
      };
      unbindProgressChanged = $rootScope.$on('assignments.progressChanged',
    function() {
        return $scope._loadProgress();
      });
      $scope.$on('$destroy',
    unbindProgressChanged);
      unbindProgressHide = $rootScope.$on('assignments.hideProgress',
    function() {
        return $scope.hideProgress = true;
      });
      $scope.$on('$destroy',
    unbindProgressHide);
      unbindProgressShow = $rootScope.$on('assignments.showProgress',
    function() {
        return $scope.hideProgress = false;
      });
      return $scope.$on('$destroy',
    unbindProgressShow);
    }
  ]).controller('AssignmentListController', [
    '$scope',
    '$http',
    '$rootScope',
    function($scope,
    $http,
    $rootScope) {
      var apiUrl,
    unbindAssignmentListChanged;
      apiUrl = new Url();
      $scope._reloadAssignmentList = function() {
        return $scope.updateAssignmentList = {};
      };
      unbindAssignmentListChanged = $rootScope.$on('assignmentList.updateList',
    function() {
        return $scope._reloadAssignmentList();
      });
      return $scope.$on('$destroy',
    unbindAssignmentListChanged);
    }
  ]);

}).call(this);

(function() {
  angular.module('trixStudent.directives', []).directive('trixAriaChecked', function() {
    return {
      restrict: 'A',
      scope: {
        'checked': '=trixAriaChecked'
      },
      controller: function($scope) {},
      link: function(scope, element, attrs) {
        var updateAriaChecked;
        updateAriaChecked = function() {
          if (scope.checked) {
            return element.attr('aria-checked', 'true');
          } else {
            return element.attr('aria-checked', 'false');
          }
        };
        updateAriaChecked();
        scope.$watch(attrs.trixAriaChecked, function(newValue, oldValue) {
          return updateAriaChecked();
        });
      }
    };
  }).directive('trixAssignmentList', function($http, $rootScope, $compile) {
    return {
      restrict: 'E',
      replace: true,
      link: function(scope, element, attrs) {
        var updateAssignments;
        updateAssignments = function() {
          var url;
          url = new Url();
          url.query.updatelist = 1;
          if (scope.no_filter != null) {
            url.query.no_filter = 1;
          }
          return $http.get(url.toString()).then(function(response) {
            var compiled;
            if (response.headers('hide-progress')) {
              $rootScope.$emit('assignments.hideProgress');
            } else {
              $rootScope.$emit('assignments.showProgress');
            }
            compiled = $compile(response.data)(scope);
            element.empty();
            return element.append(compiled);
          }).catch(function(response) {
            return console.error('Failed to get list.');
          });
        };
        scope.$watch('updateAssignmentList', function() {
          return updateAssignments();
        });
      }
    };
  });

}).call(this);
