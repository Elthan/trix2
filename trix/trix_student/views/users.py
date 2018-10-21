from django.views.generic import ListView, DeleteView
from django.core.exceptions import FieldError
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.translation import ugettext_lazy as _
from django.http import Http404
from django.urls import reverse_lazy

from trix.trix_core import models
from trix.utils import experience as exp
from trix.trix_core import models


class ProfilePageView(LoginRequiredMixin, ListView):
    template_name = 'trix_student/users.django.html'
    model = models.HowSolved
    paginate_by = 20

    def get(self, request, *args, **kwargs):
        self.tags = self.get_tags()
        self.sort_list = self.get_sort_list()
        return super(ProfilePageView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super(ProfilePageView, self).get_queryset()
        for tagstring in self.tags:
            queryset = (queryset.filter(assignment__tags__tag=tagstring))
        # howsolved = models.HowSolved.objects.filter(user=self.request.user)
        queryset = queryset.filter(user=self.request.user)
        queryset = queryset.distinct()
        return queryset

    def get_context_data(self):
        context = super(ProfilePageView, self).get_context_data()
        solved_assignments = self.get_queryset()
        context['user_role'] = self.get_user_role()
        context['solved_assignments'] = solved_assignments
        context['bymyself_assignments'] = solved_assignments.filter(howsolved='bymyself')
        context['withhelp_assignments'] = solved_assignments.filter(howsolved='withhelp')
        context['selected_tags_list'] = self.tags
        context['selected_tags_string'] = ','.join(self.tags)
        context['selectable_tags_list'] = self._get_selectable_tags()
        context['sort_list'] = ','.join(self.sort_list)
        # Set experience, level, and level_progress context
        assignments = []
        for howsolved in solved_assignments:
            assignments.append(howsolved.assignment)
        experience = exp.get_experience(assignments, self.request.user)
        level = exp.get_level(experience)
        context['experience'] = experience
        context['level'] = level
        context['level_progress'] = exp.get_level_progress(experience, level)
        context['selectable_sort_list'] = [(_('Title'), 'assignment__title'),
                                           (_('ID'), 'assignment__id'),
                                           (_('Points'), 'assignment__points'),
                                           (_('Solved time'), 'solved_datetime'),
                                           (_('How solved'), 'howsolved')]
        return context

    def get_user_role(self):
        if self.request.user.is_superuser:
            return _('Superuser')
        elif self.request.user.is_admin_on_anything():
            courses = models.Course.objects.filter(admins__id=self.request.user.id)
            courses_string = ', '.join([str(course) for course in courses])
            return _('Administrator for ') + courses_string
        else:
            return _('Student')

    def get_tags(self, course_tag=None):
        tags_string = self.request.GET.get('tags')
        if tags_string:
            tags = []
            for tag in tags_string.split(','):
                tag = tag.strip()
                if tag:
                    tags.append(tag)
        else:
            tags = []
        if course_tag is not None and course_tag not in tags:
            tags.append(course_tag)
        return tags

    def get_sort_list(self):
        order_list = self.request.GET.get('ordering')
        if order_list:
            sort_list = []
            for order in order_list.split(','):
                order = order.strip()
                sort_list.append(order)
        else:
            sort_list = []
        return sort_list

    def _get_selectable_tags(self):
        assignments = models.Assignment.objects.filter(howsolved__in=self.get_queryset())
        tags = (models.Tag.objects
                .filter(assignment__in=assignments)
                .exclude(tag__in=self.tags)
                .order_by('tag')
                .distinct()
                .values_list('tag', flat=True))
        return tags

    def get_ordering(self):
        ordering = self.request.GET.get('ordering', None)
        if ordering is not None:
            ordering = ordering.split(',')
            for order in ordering:
                try:
                    # str to apply sort immediately
                    str(self.model.objects.order_by(order))
                except FieldError:
                    return None
        return ordering


class UserDeleteView(LoginRequiredMixin, DeleteView):
    template_name = 'trix_student/user_delete.django.html'
    model = models.User
    success_url = reverse_lazy('trix_student_dashboard')

    def get_object(self, queryset=None):
        user = super(UserDeleteView, self).get_object()
        if not user.id == self.request.user.id:
            raise Http404
        return user
