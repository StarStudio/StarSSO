import json
from flask import request

def get_request_params():
    '''
        Get request param dict.
    '''
    post_data = request.get_data(as_text = True)
    post_json = None
    try:
        post_json = json.loads(post_data)
    except json.JSONDecodeError as e:
        pass

    if post_json:
        return post_json

    #if '' != request.get_data(as_text = True, parse_form_data = True):
    #    return None

    return request.form.copy()
