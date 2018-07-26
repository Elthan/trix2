from cradmin_legacy.acemarkdown.widgets import AceMarkdownWidget
import json


class TrixMarkdownWidget(AceMarkdownWidget):
    def get_context(self, name, value, attrs):
        context = {}
        attrs['textarea cradmin-legacy-acemarkdown-textarea'] = ''
        if 'required' in attrs:
            attrs['required'] = False
        context['widget'] = {
            'name': name,
            'is_hidden': self.is_hidden,
            'required': self.is_required,
            'value': self.format_value(value),
            'attrs': self.build_attrs(self.attrs, attrs),
            'template_name': self.template_name
        }
        context['directiveconfig'] = json.dumps(self.directiveconfig)
        return context
