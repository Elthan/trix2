from django.core.exceptions import PermissionDenied
from django.views.generic import DeleteView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse

from trix.trix_core.models import Course, User


class RemoveCourseAdminView(DeleteView):
    model = Course
    template_name = "trix_course/remove_course_admin.django.html"
    user_id = None

    def get(self, request, **kwargs):
        self.user_id = kwargs['user_id']
        if request.user.is_authenticated:
            course = get_object_or_404(Course, id=kwargs['pk'])
            if request.user.is_course_owner(course):
                return super(RemoveCourseAdminView, self).get(request, **kwargs)
            else:
                raise PermissionDenied
        else:
            return redirect('trix_login')

    def get_context_data(self, **kwargs):
        context = super(RemoveCourseAdminView, self).get_context_data(**kwargs)
        context['admin_user'] = User.objects.filter(id=self.user_id).get()
        return context

    def delete(self, request, *args, **kwargs):
        '''
        Removes a single given admin from the course.
        '''
        course_id = kwargs['pk']
        user_id = kwargs['user_id']
        course = Course.objects.filter(id=course_id).get()
        admin_user = course.admins.filter(id=user_id).get()
        course.admins.remove(admin_user)

        return redirect('trix_course_admin', course_id=course_id)
