# python2openapi
这个是重复造的轮子，主要使用场景，在python2环境上，旧项目之上做RESTful API开发，让代码自动生成openapi文档。

# 这个项目的诞生
一言难尽。 就是在无法对基础技术升级的情况下，让旧的系统提供api，并且使用openapi作为文档，让代码自动生成openapi，避免额外的文档维护工作。

# 建议
如果，能用python3就用python3吧，别折腾这个了，如果你面临和我同样的问题，可以尝试用这个代码来解决，api文档维护的问题。

# 特性
- 支持schema数据模型校验
- 支持openapi3.0
- 支持schema生成文档数据模型
- 支持注释生成文档（仅需要用yaml风格写openapi请求参数响应注释等）
- 支持python2

# Example:

```python
from openapi import swagger_setup, swagger_api,gen_request_body,gen_response,gen_parameter_doc
from openapi.schema import schema_model
from openapi.schema.field import IntField

@schema_model
class Query(object):
   start = IntField()
   end = IntField(max_value=100)

@swagger_api(path="/user/foo", method="post", parameters=gen_parameter_doc(Query, "query"), 
             request_body=gen_request_body(ListField(item_field=Query)),
             response=gen_response(ListField(item_field=Query)))
def foo():
   pass

@swagger_api(path="/hello", method="get")
def hello():
    """
    tags:
        - pet
      summary: Finds Pets by status
      description: Multiple status values can be provided with comma separated strings
      operationId: findPetsByStatus
      parameters:
        - name: status
          in: query
          description: Status values that need to be considered for filter
          required: false
          explode: true
          schema:
            type: string
            default: available
            enum:
              - available
              - pending
              - sold
      responses:
        '200':
          description: successful operation
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Pet'
            application/xml:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Pet'
    """

if __name__ == '__main__':
    swagger_doc = swagger_setup(title="test demo", servers=[{"url": "http://localhost:3000"}], version="1.0.0")
    print(swagger_doc)
```