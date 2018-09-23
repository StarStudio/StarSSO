from functools import wraps
from flask import Response
import logging
import uuid

#def collect_post_data_from_form_and_queries(_view_function):
#    @wraps(_view_function)
#    def check_wrapper(*args, **kwargs):
#        if getattr(request, 'api_post_data', None) is None:
#            request.api_post_data = {}
#        for key, value in zip(request.args.keys(), request.args.values()):
#            if key not in request.api_post_data:
#                request.api_post_data[key] = [value]
#            else:
#                request.api_post_data[key].append(value)
#        for key, value in zip(request.form.keys(), request.form.values()):
#            if key not in request.api_post_data:
#                request.api_post_data[key] = [value]
#            else:
#                request.api_post_data[key].extent(value)
#        return _view_function(*args, **kwargs)
#    return check_wrapper

def post_data_type_checker(**_types):
    for name, _type in zip(_types.keys(), _types.values()):
        if not isinstance(_type, type) \
            and not isinstance(_type, tuple) \
            and not isinstance(_type, list):\
            raise ValueError('%s should be a type object or a list of types', name)

    def type_checker(post_data):
        for name, types in zip(_types.keys(), _types.values()):
            if not name in post_data:
                continue

            values = post_data[name]
            for i in range(0, len(values)):
                # Check whether current type is acceptable.
                accepted = None
                if isinstance(types, type):
                    if types is values[i].__class__:
                        accepted = types
                else:
                    for _type in types:
                        if _type is values[i].__class__:
                            accepted = _type

                # If current type is unacceptable, try to convert it.
                if accepted is None:
                    converted = None 
                    try:
                        if isinstance(types, type):
                            converted = types(values[i])
                        else:
                            for _type in types:
                                converted = _type(values[i])
                    except Exception as e:
                        continue

                    if converted is not None:
                        #values[i] = converted
                        #post_data[name] = values
                        post_data[name] = converted
                        break
                    else:
                        # If value cannot be converted, deny this request.
                        #return jsonify({'code':1422, 'msg' : '%s is invalid' % name, data : ''})                   
                        return False, "%s has invalid type." % name
        return True, ""        
    return type_checker
         
def post_data_key_checker(*keys):
    for key in keys:
        if isinstance(key, str):
            continue
        if isinstance(key, (tuple, list)):
            for alternate in key:
                if not isinstance(alternate, str):
                    raise ValueError('Invalid type.')
        else:
            raise ValueError('Invalid type.')

    def key_checker(post_data):
        for name in keys:
            found = None
            if isinstance(name, (tuple, list)): # More then one alternate
                for alternate in name:
                    if alternate in post_data:
                        found = alternate
                        break
            else:
                if name in post_data:
                    found = name
            if found is None:
                return False, "Arg %s missing." % str(name)
                #return jsonify({'code':1422, 'msg' : 'need arg %s' % name, 'data':''})
        if len(keys) != len(post_data):
            #return jsonify({'code':1422, 'msg' : 'Too many args', 'data' : ''})
            return False, "Too many arguments."
        return True, ""
    return key_checker
            
def starstuio_secret_header(_view_function):
    @wraps(_view_function)
    def secret_checker(*arg, **kwarg):
        secret = request.headers.get('StarStudio-Application')
        if secret is None or secret != app.config['STAR_SECRET']:
            app.log_access('   Access denied. Invailed StarStudio-Application Header: %s' % secret)
            abort(400)
        return _view_function(*arg, **kwarg)
    return secret_checker


