from django import forms
from django.utils.translation import ugettext_lazy as _
from crispy_forms.layout import Submit
from crispy_forms.helper import FormHelper


class SelectableInputWidget(forms.TextInput):

    def __init__(self, data_list, name, *args, **kwargs):
        super(SelectableInputWidget, self).__init__(*args, **kwargs)
        self._name = name
        self._list = data_list
        self.attrs.update({'list': 'list__{}'.format(self._name)})
        self.helper = FormHelper()
        self.helper.add_input(Submit('filter_submit', _('Filter')))

    def render(self, name, value, attrs=None):
        super(SelectableInputWidget, self).render(name, value, attrs=attrs)
        data_list = '<datalist id="#list__{}">'.format(self._name)
        for item in self._list:
            data_list += '<option value={tag}>{tag}</option>'.format(tag=item)
        data_list += '</datalist>'

        return data_list


class TagSearchForm(forms.Form):
    char_field_list = forms.CharField(required=True)

    def __init__(self, *args, **kwargs):
        _tag_list = kwargs.pop('tag_list', None)
        super(TagSearchForm, self).__init__(*args, **kwargs)

        self.fields['char_field_list'].widget = SelectableInputWidget(data_list=_tag_list,
                                                                      name='tag-list')
