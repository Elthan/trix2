import json
from django import http
from django.conf import settings
from django.shortcuts import render
from django.views.generic import ListView
from django.utils.translation import ugettext_lazy as _
from functools import reduce
from urllib import parse

from trix.trix_core import models
from trix.utils import experience as exp


class AssignmentListViewBase(ListView):
    paginate_by = 100
    context_object_name = 'assignment_list'
    already_selected_tags = []

    def get(self, request, **kwargs):
        self.selected_tags = self._get_selected_tags()
        self.selectable_tags = self._get_selectable_tags()
        self.non_removeable_tags = self.get_nonremoveable_tags()
        if self.request.GET.get('progressjson'):
            return self._progressjson()
        elif self.request.GET.get('updatelist'):
            return self._updateList()
        else:
            return super(AssignmentListViewBase, self).get(request, **kwargs)

    def get_queryset(self):
        assignments = self.get_all_available_assignments()
        if self.selected_tags:
            exclude_list = [tag.lstrip('-') for tag in self.selected_tags if tag.startswith('-')]
            filter_list = [tag for tag in self.selected_tags if not tag.startswith('-')]
            if filter_list:
                # Get only assignments which match exactly the tags in the list
                assignments = reduce(lambda qs, pk: qs.filter(tags__tag=pk),
                                     filter_list, assignments)
            if exclude_list:
                # Exclude any assignment that has an excluded tag
                assignments = assignments.exclude(tags__tag__in=exclude_list)
        # Exclude hidden tasks from those that are not admin
        if not self._get_user_is_admin():
            assignments = assignments.exclude(hidden=True)
        assignments = assignments.order_by('difficulty', 'title')
        return assignments

    def _get_progress(self):
        """
        Gets the progress a user has made.
        """
        assignments = self.get_queryset()
        how_solved = (models.HowSolved.objects.filter(assignment__in=assignments)
                      .filter(user=self.request.user.id))
        num_solved = how_solved.count()
        num_total = assignments.count()
        # Get all subject tags
        experience = exp.get_experience(assignments, self.request.user)
        # Calculate level based on tags
        lvl = exp.get_level(experience)
        lvl_progress = exp.get_level_progress(experience, lvl)
        lvl_up = False
        if num_total == 0:
            percent = 0
        else:
            percent = round(num_solved / float(num_total) * 100, 0)
        return {
            'num_total': num_total,
            'num_solved': num_solved,
            'percent': percent,
            'experience': experience,
            'level': lvl,
            'level_progress': lvl_progress,
            'lvl_up': lvl_up
        }

    def _progressjson(self):
        return http.HttpResponse(
            json.dumps(self._get_progress()),
            content_type='application/json'
        )

    def _updateListContext(self):
        filter = self.request.GET.get('no_filter', None)
        return {
            'user_is_admin': self._get_user_is_admin(),
            'assignment_list': self._filter_assignments(filter),
            'authenticated': self.request.user.is_authenticated()
        }

    def _updateList(self):
        context = self._updateListContext()
        template = 'trix_student/include/assignment_list.django.html'
        response = render(self.request, template, context)
        if not context['assignment_list']:
            response['Hide-Progress'] = 'true'
        return response

    def _get_selectable_tags(self):
        already_selected_tags = self.get_already_selected_tags() + self.selected_tags
        tags = (models.Tag.objects
                .filter(assignment__in=self.get_queryset())
                .exclude(tag__in=already_selected_tags)
                .order_by('tag')
                .distinct()
                .values_list('tag', flat=True))
        return tags

    def _get_selected_tags(self):
        tags_string = self.request.GET.get('tags', None)
        tags = []
        if tags_string:
            tags = tags_string.split(',')
            tags.sort()
        return tags

    def get_context_data(self, **kwargs):
        context = super(AssignmentListViewBase, self).get_context_data(**kwargs)
        context['non_removeable_tags'] = self.non_removeable_tags
        context['selected_tags'] = self.selected_tags
        context['selectable_tags'] = self.selectable_tags
        context['authenticated'] = self.request.user.is_authenticated()
        context['urlencoded_success_url'] = parse.urlencode({
            'success_url': self.request.get_full_path()})
        context['user_is_admin'] = self._get_user_is_admin()
        context['progresstext'] = _(
            'You have completed {{ solvedPercentage }} percent of assignments matching the '
            'currently selected tags.')

        context['level_explanation_header'] = _('Levels and experience')
        context['level_explanation_text'] = _('Experience is calculated based on tasks with tags'
                                              'you have solved. When solving a task you will get '
                                              'experience on each of the tags that assignment '
                                              'has.')
        return context

    def _get_assignmentlist_with_howsolved(self, assignment_list):
        """
        Expand the given list of Assignment objects with information
        about how ``request.user`` solved the assignment.

        Returns:
            A list with ``(assignment, howsolved)`` tuples where ``howsolved``
            is one of the valid values for the ``howsolved`` field in
            :class:`trix.trix_core.models.HowSolved``, or empty string if there is no
            HowSolved object for ``request.user`` for the assignment.
        """
        howsolvedmap = {}  # Map of assignment ID to HowSolved.howsolved for request.user
        if self.request.user.is_authenticated() and assignment_list:
            howsolvedquery = (models.HowSolved.objects
                              .filter(user=self.request.user, assignment__in=assignment_list))
            howsolvedmap = dict(howsolvedquery.values_list('assignment_id', 'howsolved'))
        return [(assignment, howsolvedmap.get(assignment.id, ''))
                for assignment in assignment_list]

    def _filter_assignments(self, no_filter=None):
        """Returns the assignments with howsolved, doing a filtering on difficulties.

        Filtering is done by iterating the assignments and removing assignments that do not match
        the users experience in the tags for that assignment. I.E. the user has enough experience
        in a subject tag to be shown the medium difficulty assignments, it will filter out all
        assignments that are easy for those tags.
        """
        assignments = self.get_queryset()
        if no_filter is None:
            for assignment in assignments:
                difficulty = exp.get_difficulty(assignment, self.request.user)
                if assignment.difficulty != difficulty:
                    assignments = assignments.exclude(id=assignment.id)
        return self._get_assignmentlist_with_howsolved(assignments)

    def _get_user_is_admin(self):
        raise NotImplementedError()

    def get_all_available_assignments(self):
        raise NotImplementedError()

    def get_nonremoveable_tags(self):
        raise NotImplementedError()

    def get_already_selected_tags(self):
        raise NotImplementedError()
