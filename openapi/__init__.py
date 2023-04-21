import yaml
import inspect
from functools import wraps
from openapi.schema.field import (
    IntField,
    BoolField,
    FloatField,
    ListField,
    ObjectField,
    StringField,
    SchemaBaseModel,
)

OPEN_API_VERSION = "3.0.0"
SWAGGER_DOC_SEPARATOR = "---"


class _Swagger(object):
    paths = {}
    models = {}
    parameters = {}
    global_tags = []


def swagger_setup(
    title="", servers=[], version="", description="", term="", contact={}, tags=[]
):
    """
    openapi: 3.0
    """
    _Swagger.global_tags.extend(tags)
    return {
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
            "parameters": _Swagger.parameters,
        },
        "tags": _Swagger.global_tags,
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

    if isinstance(model, SchemaBaseModel) or issubclass(model, SchemaBaseModel):
        items = model.get_validate_func_map().items()
    else:
        items = vars(model).items()
    for field_name, field_type in items:
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
    parameters = {}
    if isinstance(model, SchemaBaseModel) or issubclass(model, SchemaBaseModel):
        items = model.get_validate_func_map().items()
    else:
        items = vars(model).items()
    for field_name, field_type in items:
        if not field_name.startswith("__"):
            default = {
                "in": in_pos,
                "description": field_type.description,
                "required": field_type.required,
            }

            alisa_name = field_type.name
            if alisa_name:
                default["name"] = alisa_name
            else:
                default["name"] = field_name
            default["schema"] = _parser_parameter(field_type)
            parameters[default["name"]] = default
    return parameters


def register_swagger_query_parameter(model):
    """Register parameter definition in swagger"""
    _Swagger.parameters = gen_parameter_doc(model, "query")
    return model


def register_swagger_header_parameter(model):
    """Register parameter definition in swagger"""
    _Swagger.parameters = gen_parameter_doc(model, "header")
    return model


def register_swagger_cookie_parameter(model):
    """Register parameter definition in swagger"""
    _Swagger.parameters = gen_parameter_doc(model, "cookie")
    return model


def register_swagger_path_parameter(model):
    """Register parameter definition in swagger"""
    _Swagger.parameters = gen_parameter_doc(model, "path")
    return model


def swagger_api(
    path="",
    method="",
    parameters={},
    request_body=None,
    response=None,
    tags=[],
    summary="",
    description="",
    security=[],
):
    if type(path) == str and path != "":
        if _Swagger.paths.get(path, None):
            raise ValueError("Path is existed.")

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
    if response:
        default[method]["responses"] = response

    if parameters:
        for p in parameters:
            default[method]["parameters"].append(parameters[p])

    if request_body:
        default[method]["requestBody"] = request_body

    def bind(func):
        doc = inspect.getdoc(func)
        if doc:
            api = build_swagger_docs(doc)
            if type(api) == dict:
                if security:
                    api["security"] = security
                if tags:
                    api["tags"] = tags
                if parameters:
                    for p in parameters:
                        api.get("parameters", []).append(parameters[p])
                if request_body:
                    api["requestBody"] = request_body
                if response:
                    api["responses"] = response
                _Swagger.paths[path] = {method: api}
            else:
                _Swagger.paths[path] = default
        else:
            _Swagger.paths[path] = default

        @wraps(func)
        def api_wraps(*argc, **kwags):
            return func(*argc, **kwags)

        return api_wraps

    return bind
