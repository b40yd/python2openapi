import re
import sys
import json
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
            
    def check_attr(self, cls, attr):
        flag = False
        if type(attr) == dict:
            for key in attr.keys():
                flag = hasattr(cls, key)

        elif type(attr) in (list, tuple):
            for v in attr:
                flag = self.check_attr(cls, v)
            
        return flag
    
    def get_value_from_str(self, value):
        if sys.version_info.major == 2:
            if type(value) in (str, unicode):
                value = json.loads(value)
        else:
            if type(value) == str:
                value = json.loads(value)
        return value
    
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
        if value is None:
            if self.required:
                raise ValueError('"{}" is missing.'.format(name))
            else:
                return self.default
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
        if value is None:
            if self.required:
                raise ValueError('"{}" is missing.'.format(name))
            else:
                return self.default
        try:
            value = int(value)
        except ValueError:
            raise ValueError("{} should be integer type".format(name))
            
        if self.min_value is not None and self.min_value > value:
            raise ValueError("{} should be larger than {}".format(name, self.min_value))
        
        if self.max_value is not None and self.max_value < value:
            raise ValueError("{} should be smaller than {}".format(name, self.max_value))
        
        self.checkin_enums(name, value)
        
        return value
    
class FloatField(Field):
    def __init__(self,name=None, description="", default=0.0, required=False, min_value=None, max_value=None, format="", enums=[]):
        self.default = default
        self.name = name
        self.required = required
        self.min_value = min_value
        self.max_value = max_value
        self.description = description
        self.enums = enums
        self.format = format

    def validate(self, name, value):
        if value is None:
            if self.required:
                raise ValueError('"{}" is missing.'.format(name))
            else:
                return self.default
            
        try:
            value = float(value)
        except ValueError:
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
        valueBool = {
            "true": True,
            "false": False
        }
        if value is None:
            if self.required:
                raise ValueError('"{}" is missing.'.format(name))
            else:
                return self.default
        try:
            if sys.version_info.major == 2:
                if type(value) in (str, unicode):
                    value = valueBool[value.lower()]
            else:
                if type(value) == str:
                    value = valueBool[value.lower()]
        except:
            raise ValueError("{} should be bool type".format(name))
        
        if type(value) != bool:
            raise ValueError("{} should be bool type".format(name))
        return value
    
class StringField(Field):
    def __init__(self,name=None, description="", default='',required=False,min_length=None,max_length=None, pattern=None, format="", enums=[]):
        self.default = default
        self.name = name
        self.required = required
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = pattern
        self.description = description
        self.enums = enums
        self.format = format

    def validate(self, name, value):
        if value is None:
            if self.required:
                raise ValueError('"{}" is missing.'.format(name))
            else:
                return self.default
            
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
        
        if self.pattern is not None:
            try:
                m = re.match(self.pattern, value)
                if m is None or m.end() < len(value):
                    raise ValueError('{}: {} is NOT fully matched pattern.'.format(name, self.pattern))
            except re.error:
                raise ValueError('{}: {} is NOT a valid pattern.'.format(name, self.pattern))
            
        self.checkin_enums(name, value)

        return value
    
class ListField(Field):
    def __init__(self,item_field,name=None, description="", default=[],required=False,min_items=None,max_items=None, is_to_dict=False):
        self.default = default
        self.name = name
        self.required = required
        self.min_items = min_items
        self.max_items = max_items
        self.item_field = item_field
        self.description = description
        self.is_to_dict = is_to_dict

    def validate(self, name, value):
        if value is None:
            if self.required:
                raise ValueError('"{}" is missing.'.format(name))
            else:
                return self.default

        try:
            value = self.get_value_from_str(value)
        except Exception as e:
            raise ValueError("{} should be list type: {}".format(name, e))

        if type(value) != list:
            raise ValueError("{} should be list type: {}".format(name, type(value)))
        
        if self.min_items is not None and len(value) < self.min_items:
            raise ValueError('{} should be at least {} items.'.format(name, self.min_items))

        if self.max_items is not None and len(value) > self.max_items:
            raise ValueError('{}\'s maximum length should not exceed {} characters.'.format(name, self.max_items))

        values = []
        for v in value:
            if isinstance(self.item_field, Field):
                values.append(self.item_field.validate(name,v))
            elif issubclass(self.item_field, SchemaBaseModel):
                if isinstance(v, self.item_field):
                    values.append(v.to_dict() if self.is_to_dict else v)
                else:
                    values.append(self.item_field(**v).to_dict() if self.is_to_dict else self.item_field(**v))
            elif issubclass(self.item_field, Field):
                values.append(self.item_field().validate(name, v))
            else:
                raise ValueError("The {} should be <{}> type.".format(name, self.item_field))
        return values

class ObjectField(Field):
    def __init__(self,classobj, name=None, description="", default={}, required=False, is_to_dict=False):
        self.default = default
        self.name = name
        self.required = required
        self.classobj = classobj
        self.description = description
        self.is_to_dict = is_to_dict

    def validate(self, name, value):
        if value is None:
            if self.required:
                raise ValueError('"{}" is missing.'.format(name))
            else:
                return self.default
            
        try:
            value = self.get_value_from_str(value)
        except:
            raise ValueError("{} should be object type".format(name))
            
        if issubclass(self.classobj, SchemaBaseModel):
            if isinstance(value, SchemaBaseModel):
                return value.to_dict if self.is_to_dict else value
            obj = self.classobj(**value)
            return obj.to_dict() if self.is_to_dict else obj
        else:
            raise ValueError("{} should be <SchemaModel> type".format(name))
        
class AnyOfField(Field):
    def __init__(self, fields, name=None, description="", default=[], required=False, is_to_dict=False):
        if not isinstance(fields, list):
            raise ValueError("{} should be List type.".format(name))
        self.default = default
        self.name = name
        self.required = required
        self.fields = fields
        self.description = description
        self.is_to_dict = is_to_dict

    def validate(self, name, value):
        if value is None:
            if self.required:
                raise ValueError('"{}" is missing.'.format(name))
            else:
                return self.default
            
        for field in self.fields:
            if isinstance(field, Field):
                return field.validate(name, value)
            elif issubclass(field, SchemaBaseModel):
                value = self.get_value_from_str(value)
                if isinstance(value,field):
                    return value.to_dict if self.is_to_dict else value
                else:
                    if self.check_attr(field, value):
                        return field(**value).to_dict() if self.is_to_dict else field(**value)
            else:
                raise ValueError("{} should be any of <SchemaModel> or <Field> type.".format(name))
            
        raise ValueError("{} should be any of {} type.".format(name, ' or '.join([field.__name__ for field in self.fields])))
            
class AllOfField(Field):
    def __init__(self, fields, name=None, description="", default=[], required=False, is_to_dict=False):
        if fields is None:
            if self.required:
                raise ValueError('"{}" is missing.'.format(name))
            else:
                return self.default
            
        if not isinstance(fields, list):
            raise ValueError("{} should be List type.".format(name))
        self.default = default
        self.name = name
        self.required = required
        self.fields = fields
        self.description = description
        self.is_to_dict = is_to_dict

    def validate(self, name, values):
        validations = []
        if value is None:
            if self.required:
                raise ValueError('"{}" is missing.'.format(name))
            else:
                return self.default
        for field in self.fields:
            for value in values:
                if isinstance(field, Field):
                    validations.append(field.validate(name, value))
                elif issubclass(field, SchemaBaseModel):
                    value = self.get_value_from_str(value)
                    if isinstance(value,field):
                        validations.append(value.to_dict() if self.is_to_dict else value)
                    else:
                        if self.check_attr(field, value):
                            validations.append(field(**value).to_dict() if self.is_to_dict else field(**value))
                else:
                    raise ValueError("{} should be all of <SchemaModel> or <Field> type.".format(name))
        if len(self.fields) != len(validations):
            raise ValueError("{} should be all of {} type.".format(name, ', '.join([field.__name__ for field in self.fields])))
        return validations