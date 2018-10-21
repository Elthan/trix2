import json
from django.views.generic import View
from django import http, forms
from django.shortcuts import get_object_or_404

from trix.trix_core import models


class HowSolvedForm(forms.ModelForm):
    class Meta:
        model = models.HowSolved
        fields = ['howsolved']


class HowsolvedView(View):
    """
    View of how the assignment was solved.
    """
    http_method_names = ['post', 'delete']

    def _bad_request_response(self, data):
        return http.HttpResponseBadRequest(json.dumps(data), content_type='application/json')

    def _not_found_response(self, data):
        return http.HttpResponseNotFound(json.dumps(data), content_type='application/json')

    def _200_response(self, data):
        return http.HttpResponse(json.dumps(data), content_type='application/json')

    def _get_assignment(self):
        return get_object_or_404(models.Assignment, id=self.kwargs['assignment_id'])

    def _get_howsolved(self, assignment_id):
        return (models.HowSolved.objects
                .filter(assignment_id=assignment_id, user=self.request.user)
                .get())

    def _get_tagexperience(self, tag_id):
        return (models.TagExperience.objects
                .filter(tag_id=tag_id, user=self.request.user)
                .get())

    def post(self, request, **kwargs):
        try:
            data = json.loads(request.body)
        except ValueError:
            return self._bad_request_response({
                'error': 'Invalid JSON data.'
            })

        form = HowSolvedForm(data)
        if form.is_valid():
            howsolved = form.cleaned_data['howsolved']
            assignment = self._get_assignment()

            try:
                howsolvedobject = self._get_howsolved(assignment.id)
            except models.HowSolved.DoesNotExist:
                # Create a new HowSolved object
                howsolvedobject = models.HowSolved.objects.create(
                    howsolved=howsolved,
                    assignment=assignment,
                    user=request.user)
                # The assignment has not been solved, add experience to tags
                tags = assignment.tags.filter(category='s')
                for tag in tags:
                    try:
                        tagexpobject = self._get_tagexperience(tag.id)
                    except models.TagExperience.DoesNotExist:
                        tagexpobject = models.TagExperience.objects.create(
                            tag=tag,
                            user=request.user,
                            experience=assignment.base_points
                        )
                        tagexpobject.save()
                    else:
                        tagexpobject.experience += assignment.base_points
                        tagexpobject.save()
            else:
                howsolvedobject.howsolved = howsolved
                howsolvedobject.save()

            return self._200_response({'howsolved': howsolvedobject.howsolved})
        else:
            return self._bad_request_response({
                'error': form.errors.as_text()
            })

    def delete(self, request, **kwargs):
        try:
            howsolved = self._get_howsolved(self.kwargs['assignment_id'])
        except models.HowSolved.DoesNotExist:
            return self._not_found_response({
                'message': 'No HowSolved for this user and assignment.'
            })
        else:
            howsolved.delete()
            assignment = self._get_assignment()
            tags = assignment.tags.filter(category='s')
            for tag in tags:
                try:
                    tagexp = self._get_tagexperience(tag.id)
                except models.TagExperience.DoesNotExist:
                    continue
                else:
                    tagexp.experience -= assignment.base_points
                    if tagexp.experience <= 0:
                        tagexp.delete()
                    else:
                        tagexp.save()
            return self._200_response({'success': True})
