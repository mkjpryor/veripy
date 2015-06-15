"""
This module provides some comparison types, i.e. types that are able to verify a comparison as
an instance check

@author: Matt Pryor <mkjpryor@gmail.com>
"""

import operator

from ..types import TypeMeta


class ComparisonMeta(TypeMeta):
    """
    Metaclass for comparison types
    """
    
    def __new__(cls, name, bases, ns, operator = None):
        self = super().__new__(cls, name, bases, ns)
        self.__operator__ = operator
        return self

    def __getitem__(self, val):
        if self.__hasvalue__:
            raise TypeError('Cannot re-parameterise an existing comparison type')
        name = '%s[%s]' % (self.__name__, val)
        cls = self.__class__(name, self.__bases__, dict(self.__dict__), self.__operator__)
        cls.__hasvalue__ = True
        cls.__value__ = val
        return cls
    
    def __eq__(self, other):
        if not isinstance(other, ComparisonMeta):
            return NotImplemented
        return self.__class__ == other.__class__ and \
               self.__hasvalue__ == other.__hasvalue__ and \
               self.__value__ == other.__value__
    
    def __hash__(self):
        return hash(self.__hasvalue__) ^ hash(self.__value__)
    
    def __instancecheck__(self, instance):
        if not self.__hasvalue__:
            raise TypeError('Cannot use unparameterised comparison type')
        return self.__operator__(instance, self.__value__)
    
    def __subclasscheck__(self, cls):
        raise TypeError('Cannot use comparison types for subclass checking')


class Eq(metaclass = ComparisonMeta, operator = operator.eq):
    """
    Parameterisable type for equality testing, i.e. isinstance(x, Eq[10]) is equivalent to x == 10
    """
    __hasvalue__ = False
    __value__    = None


class Ge(metaclass = ComparisonMeta, operator = operator.ge):
    """
    Parameterisable type that tests if an object is >= another, i.e. isinstance(x, Ge[10])
    is equivalent to x >= 10
    """
    __hasvalue__ = False
    __value__    = None
    
    
class Gt(metaclass = ComparisonMeta, operator = operator.gt):
    """
    Parameterisable type that tests if an object is > another, i.e. isinstance(x, Gt[10])
    is equivalent to x > 10
    """
    __hasvalue__ = False
    __value__    = None
    
    
class Le(metaclass = ComparisonMeta, operator = operator.le):
    """
    Parameterisable type that tests if an object is <= another, i.e. isinstance(x, Le[10])
    is equivalent to x <= 10
    """
    __hasvalue__ = False
    __value__    = None
    
    
class Lt(metaclass = ComparisonMeta, operator = operator.lt):
    """
    Parameterisable type that tests if an object is < another, i.e. isinstance(x, Lt[10])
    is equivalent to x < 10
    """
    __hasvalue__ = False
    __value__    = None
