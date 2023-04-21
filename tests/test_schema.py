# encoding: utf-8
from openapi.schema import schema_model, SchemaBaseModel
from openapi.schema.field import IntField, StringField, ListField,ObjectField,FloatField
# import simplejson as json
import json

@schema_model
class Bar(object):
    bar = StringField(default="bar")
@schema_model
class Foo(object):
    foo = StringField(default="foo")
    bars = ObjectField(classobj=Bar,default="foo")
    double= FloatField(default=1.0)

@schema_model
class Demo(object):
    age = IntField(default=0, required=True, min_value=10, max_value=20)
    name = StringField(default="test")
    foos = ObjectField(Foo)

@schema_model
class DemoList(object):
    ids = ListField(item_field=IntField)

    servers = ListField(item_field=StringField)

@schema_model
class DemoListObject(object):
    hello = StringField()
    servers = ListField(item_field=Demo)

@schema_model
class DemoObject(object):
    age = IntField(name="year",default=0, required=True, min_value=10, max_value=20)
    server = ObjectField(classobj=Demo)

def test_validate():
    # foo = Foo(double = "11")
    data = Demo(enable_default=True,age=11,foos=Foo(enable_default=True,double = 1))
    # print(data.age, data.name)
    jdata = json.dumps(data,default=lambda obj: obj.__json__())
    print(jdata, "111")
    assert data.age >= 10 and data.age <= 20
    # assert data.name == "test"

def test_list_validate():
    data = DemoList()
    print(data)
    # assert data.ids == None
    data = DemoList(ids=[1,2,3])
    print(data.to_dict())
    assert data.ids == [1,2,3]

def test_list_object_validate():
    data = DemoListObject(default=False,servers=[{"age":20, "name": "d11111111emo"}])
    print(data.to_dict())
    all =data.to_dict(remove=["servers"])
    print(all)
    data = DemoListObject(servers=[Demo(age=10, name="lisan",foos=Foo(double = 2.0))])
    # all =data.to_dict(remove=["servers"])
    print(data.to_dict())
    # for d in all['servers']:
    #     if hasattr(d, 'to_dict'):
    #         print(d.to_dict(),"......")
        # print("=====",d,"=====")

def test_object_validate():
    data = DemoObject(year=20,server={"age":20, "name": "demo"})
    # print(data.server.age)
    print(data.to_dict(only=[], remove=[]))


@schema_model
class Server(object):

    host = StringField(name="host", default="example.com", min_length=2, max_length=255)
    port = IntField(name="port", default=80, min_value=2, max_value=65535)
    protocol = StringField(name="protocol", default="http", min_length=1, max_length=255)


if __name__ == '__main__':
    test_validate()
    test_list_validate()
    test_list_object_validate()
    test_object_validate()


   