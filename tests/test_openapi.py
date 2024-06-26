# encoding: utf-8
import os
import sys
current_dir = os.getcwd()
print(current_dir, sys.path)
import json 
from openapi import swagger_setup,swagger_api, register_swagger_query_parameter,register_swagger_object_model, gen_parameter_doc,gen_request_body,gen_response

@swagger_api(path="/", method="get")
def index():
  pass

@swagger_api(path="/hello", method="get")
def hello():
  """
  """
  pass

@swagger_api(path="/user/createWithList", method="post")
def create_white_list():
  """
      tags:
        - user
      summary: Creates list of users with given input array
      description: Creates list of users with given input array
      operationId: createUsersWithListInput
      requestBody:
        content:
          application/json:
            schema:
              type: array
              items:
                type: integer
      responses:
        '200':
          description: Successful operation
        default:
          description: successful operation
  """

from openapi.schema import schema_model, SchemaBaseModel
from openapi.schema.field import IntField, StringField, ListField,ObjectField,Field
# import simplejson as json
import json

@register_swagger_object_model
@register_swagger_query_parameter
@schema_model
class Bar(object):
    bar = StringField(default="bar")

@register_swagger_object_model
@schema_model
class Foo(object):
    bar = ObjectField(classobj=Bar)

@register_swagger_object_model
@schema_model
class Demo(object):
    newbar = ListField(item_field=Foo)

@register_swagger_object_model
class Apple(object):
   size = IntField(min_value=1, max_value=10)

@schema_model
class Query(object):
   start = IntField()
   end = IntField(max_value=100)

@swagger_api(path="/user/foo", method="post", parameters=gen_parameter_doc(Query, "query"), 
             request_body=gen_request_body(ListField(item_field=Query)),
             response=gen_response(ListField(item_field=Query)))
def foo():
   pass
   
def test_swagger_doc():
  swagger_doc = swagger_setup(title="test demo", servers=[{"url": "http://localhost:3000"}], version="1.0.0")
  assert(json.dumps(swagger_doc) == '{"info": {"termsOfService": "", "version": "1.0.0", "contact": {}, "description": "", "title": "test demo"}, "paths": {"/user/createWithList": {"post": {"requestBody": {"content": {"application/json": {"schema": {"items": {"type": "integer"}, "type": "array"}}}}, "responses": {"default": {"description": "successful operation"}, "200": {"description": "Successful operation"}}, "tags": ["user"], "operationId": "createUsersWithListInput", "summary": "Creates list of users with given input array", "description": "Creates list of users with given input array"}}, "/user/foo": {"post": {"responses": {"200": {"content": {"application/json": {"schema": {"items": {"type": "object", "properties": {"start": {"type": "integer"}, "end": {"type": "integer", "maximum": 100}}}, "type": "array"}}}, "description": ""}}, "parameters": [{"schema": {"type": "integer"}, "required": false, "description": "", "name": "start", "in": "query"}, {"schema": {"type": "integer", "maximum": 100}, "required": false, "description": "", "name": "end", "in": "query"}], "summary": "post foo", "requestBody": {"content": {"application/json": {"schema": {"items": {"type": "object", "properties": {"start": {"type": "integer"}, "end": {"type": "integer", "maximum": 100}}}, "type": "array"}}}, "description": ""}, "security": [], "description": ""}}, "/": {"get": {"responses": {"200": {"description": "OK"}}, "security": [], "description": "", "parameters": [], "summary": "get "}}, "/hello": {"get": {"responses": {"200": {"description": "OK"}}, "parameters": [], "tags": [], "summary": "", "security": [], "description": ""}}}, "tags": [], "servers": [{"url": "http://localhost:3000"}], "components": {"parameters": {"bar": {"schema": {"default": "bar", "type": "string"}, "required": false, "description": "", "name": "bar", "in": "query"}}, "schemas": {"Demo": {"type": "object", "properties": {"newbar": {"items": {"$ref": "#/components/schemas/Foo"}, "type": "array"}}}, "Foo": {"type": "object", "properties": {"bar": {"$ref": "#/components/schemas/Bar"}}}, "Bar": {"type": "object", "properties": {"bar": {"default": "bar", "type": "string"}}}, "Apple": {"type": "object", "properties": {"size": {"minimum": 1, "type": "integer", "maximum": 10}}}}}, "openapi": "3.0.0"}')