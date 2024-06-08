
# import html

# Utility function for stripping whitespace
def strip_whitespace(form, field):
    """
    Utility function for stripping leading and trailing whitespace from a form field's data.
    (Used when entering new words and prhases!)
    Args:
        form (Form): The form containing the field.
        field (Field): The field whose data will be stripped of whitespace.

    Returns:
        None
    """
    if field.data:
        field.data = field.data.strip()
        
"""
def process_form_data(form_data):
    if form_data:
        return [html.escape(item) for item in form_data]
    else:
        return []
"""