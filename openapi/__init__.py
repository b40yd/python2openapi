import yaml
import inspect
import re
from functools import wraps
import logging
from openapi.schema.field import (
    Field,
    IntField,
    BoolField,
    FloatField,
    ListField,
    ObjectField,
    StringField,
    AnyOfField,
    SchemaBaseModel,
)
from django.conf.urls import url
from django.http import HttpRequest, HttpResponse

OPEN_API_VERSION = "3.0.0"
SWAGGER_DOC_SEPARATOR = "---"


class _Swagger(object):
    paths = {}
    models = {}
    parameters = []
    global_tags = []
    handlers = {}

    @staticmethod
    def gen_django_urls():
        return [url(r"^%s$" % api_url.lstrip('/'), route_hander(api_url)) for api_url, _ in _Swagger.handlers.items()]


def swagger_setup(
    title="", servers=[], version="", description="", term="", contact={}, tags=[], securitySchemes={}
):
    """
    openapi: 3.0
    """
    _Swagger.global_tags.extend(tags)
    return {
        "django_urls": _Swagger.gen_django_urls(),
        "swagger_doc": {
            "openapi": OPEN_API_VERSION,
            "info": {
                "title": title,
                "version": version,
                "description": description,
                "termsOfService": term,
                "contact": contact,
            },
            "servers": servers,
            "paths": _Swagger.paths,
            "components": {
                "schemas": _Swagger.models,
                "parameters": {param['name']: param for param in _Swagger.parameters},
                "securitySchemes": securitySchemes
            },
            "tags": _Swagger.global_tags,
        }
    }


def _extract_swagger_definition(endpoint_doc):
    """Extract swagger definition after SWAGGER_DOC_SEPARATOR"""
    endpoint_doc = endpoint_doc.splitlines()

    for i, doc_line in enumerate(endpoint_doc):
        if SWAGGER_DOC_SEPARATOR in doc_line:
            end_point_swagger_start = i + 1
            endpoint_doc = endpoint_doc[end_point_swagger_start:]
            break
    return "\n".join(endpoint_doc)


def build_swagger_docs(endpoint_doc):
    """Build swagger doc based on endpoint docstring"""
    endpoint_doc = _extract_swagger_definition(endpoint_doc)
    try:
        endpoint_doc = endpoint_doc.replace("\t", "    ")  # fix windows tabs bug
        if endpoint_doc.strip() == "":
            return {
                "tags": [],
                "summary": "",
                "description": "",
                "responses": {"200": {"description": "OK"}},
                "parameters": [],
                "security": [],
            }
        end_point_swagger_doc = yaml.safe_load(endpoint_doc)
        if not isinstance(end_point_swagger_doc, dict):
            raise yaml.YAMLError()
        return end_point_swagger_doc
    except yaml.YAMLError:
        return {
            "description": "Swagger document could not be loaded from docstring",
            "tags": ["Invalid Swagger"],
        }


def _parser_parameter(field):
    schema = {}
    if isinstance(field, ListField):
        schema["type"] = "array"
        schema["items"] = _parser_parameter(field.item_field)
        return schema

    if isinstance(field, ObjectField):
        if isinstance(field.classobj, SchemaBaseModel):
            gen_model_doc(field.classobj)
        schema["$ref"] = "#/components/schemas/{}".format(field.classobj.__name__)
        return schema

    if isinstance(field, IntField):
        schema["type"] = "integer"
    elif isinstance(field, FloatField):
        schema["type"] = "integer"
    elif isinstance(field, BoolField):
        schema["type"] = "boolean"
    elif isinstance(field, SchemaBaseModel):
        gen_model_doc(field)
        schema["$ref"] = "#/components/schemas/{}".format(field.__name__)
        return schema
    elif isinstance(field, StringField):
        schema["type"] = "string"
        if field.min_length:
            schema["minLength"] = field.min_length
        if field.max_length:
            schema["maxLength"] = field.max_length
    elif isinstance(field, AnyOfField):
        schema["type"] = "anyOf"
        for f in field.fields:
            schema["items"] = _parser_parameter(f)
        return schema
    else:
        if issubclass(field, SchemaBaseModel):
            gen_model_doc(field)
            schema["$ref"] = "#/components/schemas/{}".format(field.__name__)
            return schema

    if field.default:
        schema["default"] = field.default

    if isinstance(field, (IntField, FloatField)):
        if field.min_value:
            schema["minimum"] = field.min_value
        if field.max_value:
            schema["maximum"] = field.max_value

    if isinstance(field, (IntField, StringField, FloatField)):
        if field.format:
            schema["format"] = field.format
        if field.enums:
            schema["enum"] = field.enums

        return schema
    return schema


def _gen_model_doc(model):
    default = {"type": "object", "properties": {}}
    items = dict()

    if isinstance(model, ObjectField):
        if inspect.isclass(model.classobj):
            return _parser_parameter(model.classobj)
    elif isinstance(model, Field):
        items = vars(model).items()
    elif isinstance(model, SchemaBaseModel) or issubclass(model, SchemaBaseModel):
        items = model.get_validate_func_map().items()
    else:
        items = vars(model).items()
    for field_name, field_type in items:
        if not isinstance(field_type, Field):
            continue
        if not field_name.startswith("__"):
            alisa_name = field_type.name
            if alisa_name:
                field_name = alisa_name

            if model.__doc__:
                default["description"] = model.__doc__
            default["properties"][field_name] = _parser_parameter(field_type)
    return default


def gen_model_doc(model):
    default = {"type": "array"}
    if isinstance(model, ListField):
        default["items"] = _gen_model_doc(model.item_field)
    else:
        default = _gen_model_doc(model)
    return default


def gen_request_body(model, content_type="application/json"):
    return {
        "description": model.__doc__ if model.__doc__ else "",
        "content": {content_type: {"schema": gen_model_doc(model)}},
    }


def gen_response(model, status=200, content_type="application/json"):
    return {
        str(status): {
            "description": model.__doc__ if model.__doc__ else "",
            "content": {content_type: {"schema": gen_model_doc(model)}},
        }
    }


def register_swagger_object_model(model):
    """Register model definition in swagger"""
    _Swagger.models[model.__name__] = gen_model_doc(model)
    return model


def gen_parameter_doc(model, in_pos):
    items = dict()
    parameters = []
    if isinstance(model, Field):
        default = {
            "in": in_pos,
            "description": model.description,
            "required": True if in_pos.lower() == 'path' else model.required,
        }
        default["name"] = model.name
        default["schema"] = _parser_parameter(model)
        
        parameters.append(default)
        return parameters
    elif isinstance(model, SchemaBaseModel) or issubclass(model, SchemaBaseModel):
        items = model.get_validate_func_map().items()
    else:
        items = vars(model).items()
    for field_name, field_type in items:
        if not field_name.startswith("__"):
            default = {
                "in": in_pos,
                "description": field_type.description,
                "required": True if in_pos.lower() == 'path' else field_type.required,
            }

            alisa_name = field_type.name
            if alisa_name:
                default["name"] = alisa_name
            else:
                default["name"] = field_name
            default["schema"] = _parser_parameter(field_type)
            parameters.append(default)
    return parameters


def register_swagger_query_parameter(model):
    """Register parameter definition in swagger"""
    _Swagger.parameters.extend(gen_parameter_doc(model, "query"))
    return model


def register_swagger_header_parameter(model):
    """Register parameter definition in swagger"""
    _Swagger.parameters.extend(gen_parameter_doc(model, "header"))
    return model


def register_swagger_cookie_parameter(model):
    """Register parameter definition in swagger"""
    _Swagger.parameters.extend(gen_parameter_doc(model, "cookie"))
    return model


def register_swagger_path_parameter(model):
    """Register parameter definition in swagger"""
    _Swagger.parameters.extend(gen_parameter_doc(model, "path"))
    return model


def swagger_api(
    path="",
    method="get",
    parameters=[],
    request_body=None,
    request_content_type="application/json",
    responses=[],
    tags=[],
    summary="",
    description="",
    security=[],
):
    """
    @schema_model
    class Query(object):
        start = IntField()

        end = IntField(max_value=100)

    path="/demo/{name}",

    parameters=[(String(name="name"), "path"), (String(name="age"), "query")],

    request_body=ListField(item_field=Query),

    response=[{"response": response, "content_type": "application/json", "status": 200}]

    tags=["demo"]

    summary="",

    description="",

    security=[]
    """
    paths = {}
    method = method.lower()
    if not method in ('get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace'):
        raise ValueError("method is must be (get, post, put, patch, delete, head, options, trace)")
    
    if type(path) == str and path != "":
        paths = _Swagger.paths.get(path, {})

    if not summary:
        summary = path.split("/")[-1]

    default = {
        method: {
            "summary": "{} {}".format(method, summary),
            "description": description,
            "responses": {"200": {"description": "OK"}},
            "parameters": [],
            "security": security,
        }
    }
    if tags:
        default[method]["tags"] = tags

    for model, pos in parameters:
        default[method]["parameters"].extend(gen_parameter_doc(model=model, in_pos=pos))
        
    if request_body and (isinstance(request_body, (Field, SchemaBaseModel)) or issubclass(request_body, SchemaBaseModel)):
        default[method]["requestBody"] = gen_request_body(request_body, request_content_type)
    
    for response in responses:
        if type(response) == dict and (isinstance(response['response'], (Field, SchemaBaseModel)) or issubclass(response['response'], SchemaBaseModel)):
            default[method]["responses"].update(gen_response(response['response'], 
                                                             response.get('status', 200), 
                                                             response.get('content_type', 'application/json')))

    def bind(func):
        validators = {}
        for model, pos in parameters:
            if not type(pos) in (str, unicode) or not pos.upper() in ('PATH', 'QUERY'):
                raise ValueError("Only use 'PATH or 'QUERY")
            
            path_query = validators.get(pos.upper(), [])
            path_query.append(model)
            validators[pos.upper()] = path_query
        
        doc = inspect.getdoc(func)
        if doc:
            api = build_swagger_docs(doc)
            if type(api) == dict:
                if security:
                    api["security"] = security
                if tags:
                    api["tags"] = tags
                
                for model, pos in parameters:
                    api.get("parameters", []).extend(gen_parameter_doc(model=model, in_pos=pos))

                if request_body and (isinstance(request_body, (Field, SchemaBaseModel)) or issubclass(request_body, SchemaBaseModel)):
                    api["requestBody"] = gen_request_body(request_body, request_content_type)
                for response in responses:
                    if type(response) == dict and \
                        (isinstance(response['response'], (Field, SchemaBaseModel)) or issubclass(response['response'], SchemaBaseModel)):
                        api["responses"].update(gen_response(response['response'], 
                                                             response.get('status', 200), 
                                                             response.get('content_type', 'application/json')))

                paths.update({method: api})
            else:
                paths.update(default)
        else:
            paths.update(default)
        _Swagger.paths[path] = paths

        @wraps(func)
        def api_wraps(*argc, **kwags):
            request = argc[0]
            new_args = [request]
            new_kwags = {}
            # validator in path
            for (arg, validator) in zip(argc[1:], validators.get('PATH', [])):
                if isinstance(validator, (StringField, IntField, FloatField, BoolField)):
                    new_args.append(validator.validate(validator.name, arg))
                else:
                    raise Exception("Data type error.")
                
            # validator in query
            new_kwags.update(query_validator(request, validators))

            # validator in request body
            if request_body:
                new_kwags.update(request_body_validator(request, request_body))
            return func(*new_args, **new_kwags)
        url_path = re.sub(r'\{\w+\}', r'([^/]+)', path)
        handers = _Swagger.handlers.get(url_path, {})
        handers[method] = api_wraps
        _Swagger.handlers[url_path] = handers
        return api_wraps

    return bind

def route_hander(url_path):
    def hander(*argc, **kwags):
        request = argc[0]
        if not isinstance(request, HttpRequest): 
            raise HttpResponse(status=404)
        _hander_map = _Swagger.handlers.get(url_path, {})
        _hander = _hander_map.get(str(request.method).lower(), None)
        if callable(_hander):
            return _hander(*argc, **kwags)
        return HttpResponse(status=405)
    return hander

def request_body_validator(request, validate_model):
    params = {}
    if not isinstance(request, HttpRequest): 
        raise Exception("request is bad.")
    
    body = request.body if request.body else None
    if isinstance(validate_model, (ListField, ObjectField)):
        validate_model.is_to_dict = True
        obj = validate_model.validate(validate_model.name or validate_model.__class__.__name__, body)
        if validate_model.name:
            params[validate_model.name] = obj
    elif issubclass(validate_model, SchemaBaseModel):
        params.update(validate_model(body).to_dict())
    else:
        raise Exception("Bind query parameters failed.")
    return params

def query_validator(request, validators={}):
    params = {}
    if not isinstance(request, HttpRequest): 
        raise Exception("request is bad.")
    
    get_params = request.GET.copy()
    post_params = request.POST.copy()
    all_params = get_params.copy()
    all_params.update(post_params)

    for validator in validators.get('QUERY', []):
        if isinstance(validator, (StringField, IntField, FloatField, BoolField)):
            for key, value in all_params.items():
                if key == validator.name:
                    params[key] = validator.validate(validator.name, value)

        elif isinstance(validator, ListField):
            for k, v in all_params.items():
                if k == validator.name and type(v) == list:
                    validator.is_to_dict = True
                    lst = validator.validate(validator.name, v)
                    params[k] = lst
        elif isinstance(validator, ObjectField):
            validator.is_to_dict = True
            _all_params = {}
            for key, values in all_params.items():
                if len(values) > 1:
                    _all_params[key] = values
                else:
                    _all_params[key] = all_params.get(key)
            params[validator.name] = validator.validate(validator.name, _all_params)
        elif issubclass(validator, SchemaBaseModel):
            _params = {key: value for key, value in all_params.items()}
            params.update(validator(**_params).to_dict())
        else:
            raise Exception("Bind query parameters failed.")
    return params
