import copy
import datetime
import random
from abc import abstractmethod
from faker import Faker


class _MetaField(type):
    name_map = {}
    fake = Faker()

    def __new__(mcs, clsname, bases, clsdict):
        clsdict["name_map"] = mcs.name_map
        clsdict["fake"] = mcs.fake
        if bases:
            defined_list = copy.copy(bases[0].defined_list)
        else:
            defined_list = []
        for key, value in clsdict.items():
            if key.startswith('D_'):
                defined_list.append(value)
        clsdict["defined_list"] = defined_list
        new_cls = type.__new__(mcs, clsname, bases, clsdict)
        mcs.name_map[clsname] = new_cls
        return new_cls


class _BaseField(metaclass=_MetaField):
    name_map: dict
    fake: Faker
    defined_list: list

    @abstractmethod
    def mock(self):
        return "base"

    def to_str(self):
        return type(self).__name__


class Int(_BaseField):

    def __init__(self, byte_nums=64, unsigned=False):
        if unsigned:  # 无符号
            min_num = 0
            max_num = 2 ** byte_nums - 1
        else:  # 有符号
            min_num = -2 ** (byte_nums - 1)
            max_num = 2 ** (byte_nums - 1) - 1
        self.args = [min_num, max_num]

    def mock(self):
        return random.randint(*self.args)


class UInt(Int):
    def __init__(self):
        super().__init__(64, True)


class UInt8(Int):
    def __init__(self):
        super().__init__(8, True)


class Int8(Int):
    def __init__(self):
        super().__init__(8, False)


class UInt16(Int):
    def __init__(self):
        super().__init__(16, True)


class Int16(Int):
    def __init__(self):
        super().__init__(16, False)


class UInt32(Int):
    def __init__(self):
        super().__init__(32, True)


class Int32(Int):
    def __init__(self):
        super().__init__(32, False)


class Float(_BaseField):
    def __init__(self, left=2, right=10):
        self.left = int(left)
        self.right = int(right)

    def mock(self):
        return self.fake.pyfloat(self.left, self.right)

    def to_str(self):
        return "_".join([type(self).__name__, str(self.left), str(self.right)])


class Str(_BaseField):

    def mock(self):
        return self.fake.word()

    @classmethod
    def match(cls, value: str):
        if value.isdigit():
            return StrInt()
        else:
            try:
                float(value)
                return StrFloat()
            except ValueError:
                return Str()


class StrInt(Int):

    def mock(self):
        return str(super().mock())


class StrFloat(Float):

    def mock(self):
        return str(super().mock())


class Datetime(_BaseField):
    D_FORMAT_YMD = "%Y-%m-%d %H:%M:%S"
    D_FORMAT_YMD_T = "%Y-%m-%dT%H:%M:%S"

    def __init__(self, date_format=D_FORMAT_YMD, **kwargs):
        self.start = datetime.datetime.now()
        self.date_format = date_format
        if not kwargs:
            self.kwargs = {"milliseconds": 1}
        else:
            self.kwargs = kwargs

    def mock(self):
        self.start += datetime.timedelta(**self.kwargs)
        return self.start.strftime(self.date_format)

    @classmethod
    def match(cls, value):
        for date_format in cls.defined_list:
            try:
                datetime.datetime.strptime(value, date_format)
                return date_format
            except ValueError:
                continue

    def to_str(self):
        return "_".join([type(self).__name__, str(self.date_format)])


class Timestamp(_BaseField):
    D_TIMEE9 = 9
    D_TIMEE6 = 6
    D_TIMEE3 = 3
    D_TIMEE0 = 0

    def __init__(self, times: int or str = D_TIMEE9, **kwargs):
        self.start = datetime.datetime.now()
        self.times = int(times)
        if not kwargs:
            self.kwargs = {"milliseconds": 1}
        else:
            self.kwargs = kwargs

    def mock(self):
        self.start += datetime.timedelta(**self.kwargs)
        return int(self.start.timestamp() * (10 ** self.times))

    @classmethod
    def match(cls, value):
        now = datetime.datetime.now()
        start = now - datetime.timedelta(weeks=100)
        end = now + datetime.timedelta(weeks=100)
        for times in cls.defined_list:
            try:
                timestamp = value / (10 ** times)
                if timestamp > 1:
                    date = datetime.datetime.fromtimestamp(timestamp)
                    if start < date < end:
                        return times

            except (ValueError, OSError):
                pass

    def to_str(self):
        return "_".join([type(self).__name__, str(self.times)])


class StrTimestamp(Timestamp):

    def mock(self):
        return str(super().mock())

    @classmethod
    def match(cls, value: str):
        if value.isdigit():
            result = super().match(int(value))
            return result


class Dict(_BaseField):

    def __init__(self, dict_fields: dict = None):
        if dict_fields is None:
            self.dict_fields = {"a": Int(), "b": Str(), "c": Timestamp()}
        else:
            self.dict_fields = dict_fields
        # self.mock()

    def mock(self):
        return {key: value.mock() for key, value in self.dict_fields.items()}

    def to_str(self):
        return {key: value.to_str() for key, value in self.dict_fields.items()}


class List(_BaseField):
    def __init__(self, list_fields: list = None):
        if list_fields is None:
            self.list_fields = [Str(), Int(), Float()]
        else:
            self.list_fields = list_fields
        # self.mock()

    def mock(self):
        return [i.mock() for i in self.list_fields]

    def to_str(self):
        return [value.to_str() for value in self.list_fields]


class _MetaMocker(type):
    order = {}

    def __new__(mcs, clsname, bases, clsdict):
        order = {key: value for key, value in clsdict.get("__annotations__", {}).items() if
                 issubclass(value, _BaseField) and key not in clsdict.keys()}
        models = {
            key: value() for key, value in order.items()
        }  # 只声明的
        for key, value in clsdict.items():
            if isinstance(value, _BaseField):
                models[key] = value  # 实例化的
        clsdict["models"] = Dict(models)
        new_cls = type.__new__(mcs, clsname, bases, clsdict)
        return new_cls


class DataMocker(metaclass=_MetaMocker):
    models: Dict or List = None

    def __init__(self, models=None):
        if models:
            self.models = models

    @classmethod
    def read_value(cls, value):
        if isinstance(value, int):
            result = Timestamp.match(value)
            if result is not None:
                return Timestamp(result)
            else:
                return Int()
        elif isinstance(value, float):
            return Float()
        elif isinstance(value, str):
            if Datetime.match(value) is not None:
                return Datetime(Datetime.match(value))
            elif StrTimestamp.match(value) is not None:
                return StrTimestamp(StrTimestamp.match(value))
            else:
                return Str.match(value)
        elif isinstance(value, dict):
            return cls.read_models_from_dicts(value)
        elif isinstance(value, list):
            return cls.read_models_from_dicts(value)

    @classmethod
    def read_models_from_dicts(cls, data: dict or list):  # 支持从dict中读取生成模型
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                result[key] = cls.read_value(value)
            return Dict(result)
        elif isinstance(data, list):
            result = []
            for value in data:
                result.append(cls.read_value(value))
            return List(result)
        else:
            raise ValueError(f"不支持的类型{data} {type(data)}")

    @classmethod
    def load_value(cls, value):
        if isinstance(value, dict):
            return cls.load_models_from_dict(value)
        elif isinstance(value, list):
            return cls.load_models_from_dict(value)
        else:
            class_name, *args = value.split("_")
            return Int.name_map[class_name](*args)

    @classmethod
    def load_models_from_dict(cls, data: dict or list) -> Dict or List:  # 支持从标准dict加载模型
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                result[key] = cls.load_value(value)
            return Dict(result)
        elif isinstance(data, list):
            result = []
            for value in data:
                result.append(cls.load_value(value))
            return List(result)
        else:
            raise ValueError(f"不支持的类型{data} {type(data)}")

    def to_str(self):  # 支持输出标准dict
        return self.models.to_str()

    def mock(self):
        return self.models.mock()

    @classmethod
    def add_provider(cls, provider):
        _BaseField.fake.add_provider(provider)
