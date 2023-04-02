import random

import pytest

from DataMocker.data_mocker import *
from DataMocker.data_mocker import DataMocker

a = Int()


def test():
    c = Dict(
        {
            "a": UInt(),
            "b": Timestamp(Timestamp.D_TIMEE3),
            "C": List(
                [
                    Datetime(Datetime.D_FORMAT_YMD_T),
                    Float()
                ]
            )
        }
    )
    print(c.mock())


@pytest.mark.parametrize("t", a.name_map.values())
def test2(t):
    t_instance = t()
    print(t_instance.mock())
    assert t_instance.mock()


def test3():
    c = Int()
    b = Float()
    print(c.fake == b.fake)
    print(a.name_map == b.name_map)


def test_dict():
    c = Dict({})
    assert not c.mock()
    b = Dict()
    assert b.mock()


def test4():
    d = DataMocker()
    assert d.models
    assert not d.mock()


def test_data_mocker():
    class PositionMocker(DataMocker):
        symbol: Str
        update_at: Timestamp = Timestamp(Timestamp.D_TIMEE3)

    data = PositionMocker().mock()
    print(data)
    assert data["symbol"]
    assert data["update_at"]


models = {
    'a': {'1': 'Datetime_%Y-%m-%dT%H:%M:%S', '2': 'StrFloat_2_10', '3': 'Float_2_10', '4': 'Int'},
    'b': 'Timestamp_0', 'c': 'Timestamp_3', 'd': 'Str',
    'e': ['StrTimestamp_6', 'Str', {'f': 'Int', "g": "StrInt"}]
}


def test_str_timestamp():
    assert StrTimestamp.match("1680441525000") == 3


def test_read_model_from_dicts():
    data = {
        "a": {
            "1": "2022-01-01T00:00:00",
            "2": "20.22",
            "3": 20.22,
            "4": 100,
        },
        "b": 1680441525,
        "c": 1680441525000,
        "d": "i am strong",
        "e": ["1680441525000000", "2022-01-01T00:00:001",
              {
                  "f": 1000,
                  "g": "10000"
              }]
    }
    data_mocker = DataMocker.read_models_from_dicts(data)
    assert data_mocker.to_str() == models


def test_load_dicts():
    m = DataMocker.load_models_from_dict(models)
    assert DataMocker.read_models_from_dicts(m.mock()).to_str() == models


def test_add_provider():
    from faker.providers import BaseProvider

    class MyProvider(BaseProvider):

        def symbols(self):
            return random.choice(["BTC", "ETH"])

    DataMocker.add_provider(MyProvider)
    assert Int.fake.symbols()
