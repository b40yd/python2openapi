from .field import SchemaBaseModel, Field

def schema_model(cls):
    if not isinstance(cls, type):
        raise ValueError("{} is not object.".format(cls.__name__))

    validate_props = {}
    required_props = {}
    for field_name in dir(cls):
        if not field_name.startswith('__'):
            field_type = getattr(cls, field_name)
            if isinstance(field_type, Field):
                alisa_name =  field_type.get_name()
                if alisa_name:
                    field_name = alisa_name
                if field_type.get_required():
                    required_props[field_name] = field_type.get_required()
            if not callable(field_type):
                validate_props[field_name] = field_type
    
    class SchemaModel(cls, SchemaBaseModel):
        __doc__ = cls.__doc__
        __name__ = cls.__name__
        __module__ = cls.__module__
        __validate_props = validate_props
        def __init__(self, params={}, is_default=False, **kwags):
            required_diff = []
            if params and type(params) != dict:
                raise ValueError("params should be <class 'dict'>.")
            for field_name, field_type in validate_props.items():
                value = kwags.get(field_name, None)
                _value = params.get(field_name, None)
                value = _value if value is None else value
                if isinstance(field_type, Field):
                    if value is not None:
                        if field_name in required_props:
                            required_diff.append(field_name)
                        self.__dict__[field_name] = field_type.validate("<{}.{}>".format(cls.__name__,field_name),value)
                    else:
                        if is_default:
                            self.__dict__[field_name] = field_type.get_default()
                else:
                    self.__dict__[field_name] = field_type
                    
            for field_name in set(required_props.keys()).difference(set(required_diff)):
                if isinstance(field_type, Field):
                    validate_props[field_name].required_missing(field_name)
         
        @classmethod
        def get_validate_func_map(self):
            return validate_props

        def __getattr__(self, item):
            if item in self.__dict__:
                return self.__dict__[item]
            else:
                raise AttributeError("No such attribute: {}".format(item))
            
        def __setattr__(self, name, value):
            if not name in self.__dict__:
                raise AttributeError("No such attribute: {}".format(name))
            validator = validate_props.get(name, None)
            if validator:
                self.__dict__[name] = validator.validate(name, value)
        
        def __getitem__(self, item):
            if item in self.__dict__:
                return self.__dict__[item]
        
        def __str__(self):
            return self.__name__
        
        def __repr__(self):
            return "<{}.{}>".format(__name__,self.__name__)
        
        def __json__(self):
            return self.to_dict()
        
        def __list_to_dict__(self, lst, is_default=True, only=[], remove=[]):
            rst = []
            for value in lst:
                if type(value) == list:
                    rst.append([self.__to_dict__(v) for v in value])
                elif isinstance(value, SchemaBaseModel):
                    rst.append(value.to_dict(is_default=is_default,only=only, remove=remove))
                else:
                    rst.append(value)
            return rst

        def to_dict(self, is_default=False, only=[], remove=[]):
            _dict = {}
            last_only = set(only).difference(set(remove))
            last_remove = set(remove).difference(set(only))
            for attr in self.__dict__:
                if (last_only and not attr in last_only) or attr in last_remove:
                    continue
                if not attr.startswith('_'):
                    value = getattr(self, attr)
                    if type(value) == list:
                        value = self.__list_to_dict__(value,is_default=is_default,only=only, remove=remove)
                    elif isinstance(value, SchemaBaseModel):
                        value = value.to_dict(is_default=is_default,only=only, remove=remove)
                    elif value is None:
                        default_field = validate_props.get(attr, None)
                        if isinstance(default_field, Field) and is_default:
                            value = default_field.get_default()
                    _dict[attr] = value
            return _dict
        
    SchemaModel.__name__ = cls.__name__
    return SchemaModel
