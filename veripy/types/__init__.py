"""
This module provides useful some useful types

Some of these types are a bit different to what a Python programmer is used to thinking
of as a type, such as dependent types and existential types

@author: Matt Pryor <mkjpryor@gmail.com>
"""


class TypeMeta(type):
    """
    Base class for typing metaclasses providing common functionality
    """
    
    def __init__(self, *args, **kwargs):
        pass


class UnionMeta(TypeMeta):
    """
    Metaclass for the Union type
    """
    
    def __getitem__(self, types):
        if self.__uniontypes__:
            raise TypeError('Cannot re-parameterise an existing union')
        if not isinstance(types, tuple):
            types = (types, )
        if not types:
            raise TypeError('Cannot create a union of no types')
        # Reduce the given types to the minimum inclusive set
        uniontypes = set()
        # Expand any union types in types as we go
        # This means we know we only have a single level of unions
        def expand_unions():
            for t in types:
                if isinstance(t, UnionMeta):
                    if not t.__uniontypes__:
                        raise TypeError('Cannot use unparameterised union')
                    yield from t.__uniontypes__
                else:
                    yield t
        # Check if each type in the expanded set is OK
        for t1 in expand_unions():
            # We allow None instead of NoneType
            if t1 is None: t1 = type(None)
            # Apart from None, type arguments have to be types
            if not isinstance(t1, type):
                raise TypeError('Cannot parameterise union with non-type argument')
            # Check it against the types we already have
            for t2 in set(uniontypes):
                # If the new type is a subclass of a type we already have, we can skip it
                if issubclass(t1, t2):
                    break
                # If the new type is a parent of a type we already have, throw that type away
                if issubclass(t2, t1):
                    uniontypes.discard(t2)
            else:
                # This only gets run if the loop exits normally (i.e. not via break)
                uniontypes.add(t1)
        # If there is only one type left, that is not a union
        if len(uniontypes) == 1:
            return next(iter(uniontypes))
        name = '%s[%s]' % (self.__name__, ', '.join(t.__name__ for t in uniontypes))
        cls = self.__class__(name, self.__bases__, dict(self.__dict__))
        cls.__uniontypes__ = frozenset(uniontypes)
        return cls
    
    def __eq__(self, other):
        if not isinstance(other, UnionMeta):
            return NotImplemented
        return self.__uniontypes__ == other.__uniontypes__
    
    def __hash__(self):
        return hash(self.__uniontypes__)
    
    def __instancecheck__(self, instance):
        if not self.__uniontypes__:
            raise TypeError('Cannot use unparameterised union')
        # An object is an instance of a union if it is an instance of any of the types in the union
        return any(isinstance(instance, t) for t in self.__uniontypes__)
    
    def __subclasscheck__(self, cls):
        if not self.__uniontypes__:
            raise TypeError('Cannot use unparameterised union')
        if isinstance(cls, UnionMeta):
            # If cls is another union, then it is a subclass of this union if each of the types
            # in cls also belong in this union
            if not cls.__uniontypes__:
                raise TypeError('Cannot use unparameterised union')
            return all(issubclass(t, self) for t in cls.__uniontypes__)
        else:
            # If cls is not another union, then it is a subclass of this union if it is a subclass
            # of one of our union types
            return any(issubclass(cls, t) for t in self.__uniontypes__)


class Union(metaclass = UnionMeta):
    """
    Parameterisable type for union (or sum) types
    """

    __uniontypes__ = None
    
    
class IntersectionMeta(TypeMeta):
    """
    Metaclass for the Intersection type
    """
    
    def __getitem__(self, types):
        if self.__intersecttypes__:
            raise TypeError('Cannot re-parameterise an existing intersection')
        if not isinstance(types, tuple):
            types = (types, )
        if not types:
            raise TypeError('Cannot create an intersection of no types')
        # Reduce the given types to the minimum inclusive set
        intersecttypes = set()
        # Expand any intersection types in types as we go
        # This means we know we only have a single level of intersections
        def expand_intersections():
            for t in types:
                if isinstance(t, IntersectionMeta):
                    if not t.__intersecttypes__:
                        raise TypeError('Cannot use unparameterised intersection')
                    yield from t.__intersecttypes__
                else:
                    yield t
        # Check if each type in the expanded set is OK
        for t1 in expand_intersections():
            # We allow None instead of NoneType
            if t1 is None: t1 = type(None)
            # Apart from None, type arguments have to be types
            if not isinstance(t1, type):
                raise TypeError('Cannot parameterise intersection with non-type argument')
            # Check it against the types we already have
            for t2 in set(intersecttypes):
                # If we already have a more specific type, skip the new type
                if issubclass(t2, t1):
                    break
                # Discard any types that are more general than the new type
                if issubclass(t1, t2):
                    intersecttypes.discard(t2)
            else:
                # This only gets run if the loop exits normally (i.e. not via break)
                intersecttypes.add(t1)
        # If there is only one type left, that is not a intersection
        if len(intersecttypes) == 1:
            return next(iter(intersecttypes))
        name = '%s[%s]' % (self.__name__, ', '.join(t.__name__ for t in intersecttypes))
        cls = self.__class__(name, self.__bases__, dict(self.__dict__))
        cls.__intersecttypes__ = frozenset(intersecttypes)
        return cls
    
    def __eq__(self, other):
        if not isinstance(other, IntersectionMeta):
            return NotImplemented
        return self.__intersecttypes__ == other.__intersecttypes__
    
    def __hash__(self):
        return hash(self.__intersecttypes__)
    
    def __instancecheck__(self, instance):
        if not self.__intersecttypes__:
            raise TypeError('Cannot use unparameterised intersection')
        # An object is an instance of an intersection if it is an instance of all of
        # the types in the intersection
        return all(isinstance(instance, t) for t in self.__intersecttypes__)
    
    def __subclasscheck__(self, cls):
        if not self.__intersecttypes__:
            raise TypeError('Cannot use unparameterised intersection')
        if isinstance(cls, IntersectionMeta):
            # If cls is another intersection, then it is a subclass of self if each of
            # the types in self has a subclass in cls
            if not cls.__intersecttypes__:
                raise TypeError('Cannot use unparameterised intersection')
            for t1 in self.__intersecttypes__:
                if all(not issubclass(t2, t1) for t2 in cls.__intersecttypes__):
                    return False
            return True
        else:
            # If cls is not another intersection, then it is a subclass of this intersection
            # if it is a subclass of all of our intersection types
            return all(issubclass(cls, t) for t in self.__intersecttypes__)


class Intersection(metaclass = IntersectionMeta):
    """
    Parameterisable type for intersection types
    """

    __intersecttypes__ = None
    