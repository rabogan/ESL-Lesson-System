import html


# Utility function for stripping whitespace
def strip_whitespace(form, field):
    if field.data:
        field.data = field.data.strip()
        

def process_form_data(form_data):
    if form_data:
        return [html.escape(item) for item in form_data]
    else:
        return []