import re
import sys
from abc import ABCMeta,abstractmethod

class SchemaBaseModel(object):
    pass

class Field():
    name = None
    default = None
    required = False
    enums = []
    __metaclass__ = ABCMeta
    def get_name(self):
        return self.name
    
    def get_default(self):
        return self.default
    
    def required_missing(self, name):
        raise ValueError("{} should be required".format(name))

    def get_required(self):
        return self.required
    
    def checkin_enums(self, name, value):
        if self.enums:
            if value not in self.enums:
                raise ValueError("{} should be in {}".format(name, self.enums))
    
    @abstractmethod
    def validate(self, name, value):
        return value

class AnyField(Field):
    def __init__(self, name=None, description="", default=None, required=False):
        self.default = default
        self.name = name
        self.required = required
        self.description = description
    
    def validate(self, name, value):
        return super().validate(name, value)

class IntField(Field):
    def __init__(self, name=None, description="", default=0, required=False, min_value=None, max_value=None, format="", enums=[]):
        self.default = default
        self.name = name
        self.required = required
        self.min_value = min_value
        self.max_value = max_value
        self.description = description
        self.enums = enums
        self.format = format

    def validate(self, name, value):
        if type(value) != int:
            raise ValueError("{} should be integer type".format(name))
        
        if self.min_value is not None and self.min_value > value:
            raise ValueError("{} should be larger than {}".format(name, self.min_value))
        
        if self.max_value is not None and self.max_value < value:
            raise ValueError("{} should be smaller than {}".format(name, self.max_value))
        
        self.checkin_enums(name, value)
        
        return value
    
class FloatField(Field):
    def __init__(self,name=None, description="", default=0.0,required=False,min_value=None,max_value=None, enums=[]):
        self.default = default
        self.name = name
        self.required = required
        self.min_value = min_value
        self.max_value = max_value
        self.description = description
        self.enums = enums

    def validate(self, name, value):
        if sys.version_info.major == 2:
            condition = type(value) != float and type(value) != int and type(value) != long
        else:
            condition = type(value) != float and type(value) != int 

        if condition:
            raise ValueError("{} should be float type".format(name))
        
        if self.min_value is not None and self.min_value > value:
            raise ValueError("{} should be larger than {}".format(name, self.min_value))
        
        if self.max_value is not None and self.max_value < value:
            raise ValueError("{} should be smaller than {}".format(name, self.max_value))
        
        self.checkin_enums(name, value)
        return value
    
class BoolField(Field):
    def __init__(self,name=None, description="", default=False, required=False):
        self.default = default
        self.name = name
        self.required = required
        self.description = description

    def validate(self, name, value):
        if type(value) != bool:
            raise ValueError("{} should be bool type".format(name))
        return value
    
class StringField(Field):
    def __init__(self,name=None, description="", default='',required=False,min_length=None,max_length=None, regex=None, format="", enums=[]):
        self.default = default
        self.name = name
        self.required = required
        self.min_length = min_length
        self.max_length = max_length
        self.regex = regex
        self.description = description
        self.enums = enums
        self.format = format

    def validate(self, name, value):
        if sys.version_info.major == 2:
            if not type(value) in (str,unicode):
                raise ValueError("{} should be string type".format(name))
        else:
            if type(value) != str:
                    raise ValueError("{} should be string type".format(name))
        
        length = len(value)
        if self.min_length is not None and self.min_length > length:
            raise ValueError("{} should be at least {} characters long".format(name, self.min_length))
        
        if self.max_length is not None and self.max_length < length:
            raise ValueError("{} maximum length should not exceed {} characters".format(name, self.max_length))
        
        if self.regex is not None:
            try:
                m = re.match(self.regex, value)
                if m is None or m.end() < len(value):
                    raise ValueError('{}: {} is NOT fully matched regex.'.format(name, self.regex))
            except re.error:
                raise ValueError('{}: {} is NOT a valid regex.'.format(name, self.regex))
            
        self.checkin_enums(name, value)

        return value
    
class ListField(Field):
    def __init__(self,item_field,name=None, description="", default=[],required=False,min_items=None,max_items=None):
        self.default = default
        self.name = name
        self.required = required
        self.min_items = min_items
        self.max_items = max_items
        self.item_field = item_field
        self.description = description

    def validate(self, name, value):
        if type(value) != list:
            raise ValueError("{} should be list type".format(name))
        
        if self.min_items is not None and len(value) < self.min_items:
            raise ValueError('{} should be at least {} items.'.format(name, self.min_items))

        if self.max_items is not None and len(value) > self.max_items:
            raise ValueError('{}\'s maximum length should not exceed {} characters.'.format(name, self.max_items))

        values = []
        for v in value:
            try:
                if isinstance(self.item_field, Field):
                    values.append(self.item_field.validate(name,v))
                elif issubclass(self.item_field, SchemaBaseModel):
                    if isinstance(v, SchemaBaseModel):
                        values.append(v)
                    else:
                        values.append(self.item_field(**v))
                elif issubclass(self.item_field, Field):
                    values.append(self.item_field().validate(name, v))
                else:
                    raise ValueError("is {} unspport type.".format(name, type(v)))
            except ValueError as e:
                raise ValueError("The {} list {}".format(name, e))
        
        return values

class ObjectField(Field):
    def __init__(self,classobj, name=None, description="", default={},required=False):
        self.default = default
        self.name = name
        self.required = required
        self.classobj = classobj
        self.description = description

    def validate(self, name, value):
        if issubclass(self.classobj, SchemaBaseModel):
            if isinstance(value, SchemaBaseModel):
                return value
            return self.classobj(**value)
        else:
            raise ValueError("{} should be <SchemaModel> type".format(name))
        