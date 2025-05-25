import pytest
from ai import PAIASingleton

class SingletonTestClass(metaclass=PAIASingleton):
    def __init__(self, value = int | None):
        self.value = value
        

def test_singleton_behavior(setup):
    instance1 = SingletonTestClass(value=1)
    instance2 = SingletonTestClass(value=2)
    assert instance1 is instance2, "Instances should be the same"
    assert instance1.value == 1, "Value should not change"