# encoding: utf-8
from openapi.schema import schema_model, SchemaBaseModel
from openapi.schema.field import IntField, StringField, ListField,ObjectField,FloatField,AnyOfField, AllOfField
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

    def test(self):
        return self.__class__.__name__
    
@schema_model
class Demo(object):
    age = IntField(default=0, required=True, min_value=10, max_value=20)
    name = StringField(default="test123")
    foos = ObjectField(Foo)

@schema_model
class DemoList(object):
    ids = ListField(item_field=IntField)

    servers = ListField(item_field=StringField)

@schema_model
class DemoListObject(object):
    hello = StringField()
    servers = ListField(item_field=Demo)
    response = AnyOfField([Demo, DemoList])

@schema_model
class DemoObject(object):
    age = IntField(name="year",default=0, required=True, min_value=10, max_value=20)
    server = ObjectField(classobj=Demo)

@schema_model
class BarFoo(Foo):
    pass

def test_foo():
    foo = Foo(double = 1.0)
    # print(foo.test)
    assert foo.test() == 'Foo'

    bar = BarFoo(foo="foo")
    assert bar.test() == 'BarFoo'


def test_validate():
    # foo = Foo(double = "11")
    data = Demo(age=11,foos=Foo(double = 1))
    assert(data.to_dict(is_default=False) ==  {'age': 11, 'foos': {'double': 1}})
    # print(data.age, data.name)
    # jdata = json.dumps(data,default=lambda obj: obj.__json__())
    # print(jdata)
    # assert data.age >= 10 and data.age <= 20
    # assert data.name == "test"

def test_list_validate():
    data = DemoList(is_default=False)
    assert(data.to_dict(is_default=False) == {})
    # assert data.ids == None
    data = DemoList(ids=[1,2,3])
    assert(data.to_dict() ==  {'ids': [1, 2, 3]})
    assert data.ids == [1,2,3]

def test_list_object_validate():
    # data = DemoListObject(default=False,servers=[{"age":20}])
    # print(data.to_dict())
    # all =data.to_dict(remove=["servers"])
    # print(all)
    data = DemoListObject(servers=[Demo(age=10,foos=Foo(double = 2.0))], response=Demo(age=10,foos=Foo(double = 2.0)))
    # all =data.to_dict(remove=["servers"])
    assert(data.to_dict(is_default=False) == {'response': {'age': 10, 'foos': {'double': 2.0}}, 'servers': [{'age': 10, 'foos': {'double': 2.0}}]})
    # for d in all['servers']:
    #     if hasattr(d, 'to_dict'):
    #         print(d.to_dict(),"......")
        # print("=====",d,"=====")

def test_object_validate():
    data = DemoObject(year=20,server={"age":20, "name": "demo"})
    # print(data.server.age)
    assert(data.to_dict(only=[], remove=[]) == {'server': {'age': 20, 'name': 'demo'}, 'year': 20})


@schema_model
class Server(object):

    host = StringField(name="host", default="example.com", min_length=2, max_length=255)
    port = IntField(name="port", default=80, min_value=2, max_value=65535)
    protocol = StringField(name="protocol", default="http", min_length=1, max_length=255)


def test_list_server():
    server = Server()
    assert(server.to_dict() == {})
    data = ListField(Server, is_to_dict=True).validate('Server',[{"host":"127.0.0.1"}])
    assert(data == [{'host': '127.0.0.1'}])
    objdata = ObjectField(Server).validate('object', {"port":8080})
    assert(objdata.to_dict() == {'port': 8080})

def test_any_obj():
    any_obj_data = AnyOfField(fields=[Server, Bar]).validate('AnyOfField', {"bar":"https"})
    assert(any_obj_data.to_dict() == {"bar":"https"})
    assert(isinstance(any_obj_data, Bar))

    any_obj_data = AnyOfField(fields=[Server, Bar]).validate('AnyOfField', Server({"protocol":"https"}))
    assert(any_obj_data.to_dict() == {"protocol":"https"})
    assert(isinstance(any_obj_data, Server))

def test_all_obj():
    all_obj = AllOfField(fields=[Server, Bar], is_to_dict=True).validate('AllOfField', [Server({"protocol":"https"}), Bar({"bar":"bar"})])
    assert(all_obj == [{'protocol': 'https'}, {'bar': 'bar'}])

    all_obj = AllOfField(fields=[Server, Bar], is_to_dict=True).validate('AllOfField', [{"protocol":"https"}, {"bar":"bar"}])
    assert(all_obj == [{'protocol': 'https'}, {'bar': 'bar'}])


if __name__ == '__main__':
    test_validate()
    test_list_validate()
    test_list_object_validate()
    test_object_validate()


   