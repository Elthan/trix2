import json
from django import http
from django.conf import settings
from django.views.generic import ListView
from django.utils.translation import ugettext_lazy as _
from functools import reduce
from urllib import parse

from trix.trix_core import models


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
        assignments = assignments.order_by('title')
        return assignments

    def _get_progress(self):
        """
        Gets the progress a user has made. Hidden tasks are not counted unless user is an admin.
        """
        assignments = self.get_queryset()
        if (not self.request.user.is_admin):
            assignments = assignments.exclude(hidden=True)
        how_solved = (models.HowSolved.objects.filter(assignment__in=assignments)
                      .filter(user=self.request.user.id))
        num_solved = how_solved.count()
        num_total = assignments.count()
        # Get all subject tags
        tags = []
        for assignment in assignments:
            tag_query = assignment.tags.filter(category='s')
            tags.append(list(tag_query))
        # Flatten list
        tags = [tag for sublist in tags for tag in sublist]
        tagexp = (models.TagExperience.objects
                  .filter(user=self.request.user)
                  .filter(tag__in=tags))
        exp = self._get_experience(tagexp)
        # Calculate level based on tags
        lvl = self._calculate_level(tagexp, exp)
        lvl_progress = self._level_progress(exp, lvl)
        if num_total == 0:
            percent = 0
        else:
            percent = round(num_solved / float(num_total) * 100, 0)
        return {
            'num_total': num_total,
            'num_solved': num_solved,
            'percent': percent,
            'experience': exp,
            'level': lvl,
            'level_progress': lvl_progress
        }

    def _progressjson(self):
        return http.HttpResponse(
            json.dumps(self._get_progress()),
            content_type='application/json'
        )

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
        return [
            (assignment, howsolvedmap.get(assignment.id, ''))
            for assignment in assignment_list]

    def get_context_data(self, **kwargs):
        context = super(AssignmentListViewBase, self).get_context_data(**kwargs)
        context['non_removeable_tags'] = self.non_removeable_tags
        context['selected_tags'] = self.selected_tags
        context['selectable_tags'] = self.selectable_tags
        context['user_is_admin'] = self._get_user_is_admin()
        context['urlencoded_success_url'] = parse.urlencode({
            'success_url': self.request.get_full_path()})

        context['assignmentlist_with_howsolved'] = self._get_assignmentlist_with_howsolved(
            context['assignment_list'])

        context['progresstext'] = _(
            'You have completed {{ solvedPercentage }} percent of assignments matching the '
            'currently selected tags.')

        context['level_explanation_header'] = _('Levels and experience')
        context['level_explanation_text'] = _('Experience is calculated based on tasks with tags'
                                              'you have solved. When solving a task you will get '
                                              'experience on each of the tags that assignment '
                                              'has.')
        return context

    def _get_experience(self, tags):
        exp = 0
        for tag in tags:
            exp += tag.experience
        return exp

    def _calculate_level(self, tags, exp):
        """
        Calculates the level based on the given TagExperience objects.
        """
        level_caps = settings.LEVEL_CAPS
        for idx in reversed(range(len(level_caps))):
            if exp >= level_caps[idx]:
                return idx + 1

    def _current_level_exp(self, level):
        """
        Returns the experience required for the given level.
        """
        level_caps = settings.LEVEL_CAPS
        if level - 1 < 0:
            return level_caps[0]
        return level_caps[level - 1]

    def _next_level_exp(self, level):
        """
        Returns the experience required for the next level.
        """
        level_caps = settings.LEVEL_CAPS
        if level >= len(level_caps) - 1:
            return level_caps[len(level_caps) - 1]
        elif level < 0:
            return level_caps[0]
        return level_caps[level]

    def _level_progress(self, xp, level):
        """
        Returns percentage progress towards next level as int at maximum 100.
        """
        base_lvl_xp = self._current_level_exp(level)  # XP needed to reach the current level
        next_lvl_xp = float(self._next_level_exp(level) -
                            self._current_level_exp(level))  # XP needed to reach the next level
        progress_lvl = xp - base_lvl_xp  # XP progress towards next level from current level
        percentage = round((progress_lvl / next_lvl_xp) * 100)  # Get the percentage and round it
        return min(int(percentage), 100)  # Return as it and at maximum 100 percent

    def _get_user_is_admin(self):
        raise NotImplementedError()

    def get_all_available_assignments(self):
        raise NotImplementedError()

    def get_nonremoveable_tags(self):
        raise NotImplementedError()

    def get_already_selected_tags(self):
        raise NotImplementedError()
