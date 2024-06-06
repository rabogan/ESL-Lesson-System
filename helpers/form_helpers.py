import json
import html


# Utility function for stripping whitespace
def strip_whitespace(form, field):
    if field.data:
        field.data = field.data.strip()
        

def is_valid_json(json_data):
    try:
        json.loads(json_data)
    except ValueError:
        return False
    return True


def process_form_data(form_data):
    if is_valid_json(form_data):
        return [html.escape(item) for item in json.loads(form_data)]
    elif form_data:
        return [html.escape(item) for item in form_data.split(',')]
    else:
        return []