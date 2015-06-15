"""
This module provides some existential types

@author: Matt Pryor <mkjpryor@gmail.com>
"""

import collections
from types import MappingProxyType, MethodType
from inspect import signature, Signature as S, Parameter as P

from ..types import TypeMeta


class TupleMeta(TypeMeta):
    """
    Metaclass for the Tuple type
    """
    
    def __getitem__(self, types):
        if self.__tupletypes__:
            raise TypeError('Cannot re-parameterise an existing tuple')
        if not isinstance(types, tuple):
            types = (types, )
        tupletypes = []
        strict = True
        for t in types:
            if not strict:
                raise SyntaxError('If an ellipsis is used, it must be the last argument')
            if t is Ellipsis:
                strict = False
                continue
            if t is None:
                t = type(None)
            if not isinstance(t, type):
                raise TypeError('Cannot parameterise tuple with non-type argument')
            tupletypes.append(t)
        if not tupletypes:
            raise TypeError('Cannot create an unparameterised tuple')
        cls = self.__class__(self.__name__, self.__bases__, dict(self.__dict__))
        cls.__tupletypes__ = tuple(tupletypes)
        cls.__strict__ = strict
        return cls
    
    def __eq__(self, other):
        if not isinstance(other, TupleMeta):
            return NotImplemented
        return self.__strict__ == other.__strict__ and self.__tupletypes__ == other.__tupletypes__
    
    def __hash__(self):
        return hash(self.__strict__) ^ hash(self.__tupletypes__)
    
    def __instancecheck__(self, instance):
        if not isinstance(instance, tuple):
            return False
        if not self.__tupletypes__:
            return True
        # Whether strict or non-strict, we must have enough positions to fulfil the expected types
        if len(instance) < len(self.__tupletypes__):
            return False
        if self.__strict__ and len(instance) != len(self.__tupletypes__):
            return False
        return all(isinstance(v, t) for v, t in zip(instance, self.__tupletypes__))
    
    def __subclasscheck__(self, cls):
        # A native tuple is a special case
        if issubclass(cls, tuple):
            return True
        # We only do further checks for other tuples
        if not isinstance(cls, TupleMeta):
            return super().__subclasscheck__(cls)
        # Check each position in cls is a subclass of the corresponding position in self
        if not self.__tupletypes__:
            return True
        if not cls.__tupletypes__:
            return False
        # Whether strict or non-strict, we must have enough positions to fulfil the expected types
        if len(cls.__tupletypes__) < len(self.__tupletypes__):
            return False
        if self.__strict__:
            if not cls.__strict__ or len(self.__tupletypes__) != len(cls.__tupletypes__):
                return False
        return all(issubclass(t1, t2) for t1, t2 in zip(cls.__tupletypes__, self.__tupletypes__))
    
    def __repr__(self):
        def types():
            for t in (self.__tupletypes__ or ()):
                yield t.__name__
            if not self.__strict__:
                yield "..." 
        return 'Tuple[%s]' % ', '.join(types())


class Tuple(metaclass = TupleMeta):
    """
    Parameterisable type for tuples, e.g. Tuple[int, str] means a tuple whose first element is an
    int and whose second element is a string
    """
    __tupletypes__ = None
    __strict__     = True
    
    
class RecordMeta(TypeMeta):
    """
    Metaclass for the Record type
    """
    
    def __getitem__(self, types):
        if self.__recordtypes__:
            raise TypeError('Cannot re-parameterise an existing record')
        if not isinstance(types, tuple):
            types = (types, )
        # Change a tuple of slices into a mapping of keys to types
        recordtypes = collections.OrderedDict()
        strict = True
        for s in types:
            if not strict:
                raise SyntaxError('If an ellipsis is used, it must be the last argument')
            if s is Ellipsis:
                strict = False
                continue
            if not isinstance(s, slice):
                raise SyntaxError('Error in record type specification')
            k = s.start
            t = s.stop
            if t is None:
                t = type(None)
            if not isinstance(t, type):
                raise TypeError('Cannot parameterise record with non-type argument')
            recordtypes[k] = t
        if not recordtypes:
            raise TypeError('Cannot create an unparameterised record')
        cls = self.__class__(self.__name__, self.__bases__, dict(self.__dict__))
        cls.__recordtypes__ = MappingProxyType(recordtypes)
        cls.__strict__ = strict
        return cls
    
    def __eq__(self, other):
        if not isinstance(other, RecordMeta):
            return NotImplemented
        return self.__strict__ == other.__strict and self.__recordtypes__ == other.__recordtypes__
    
    def __hash__(self):
        return hash(self.__strict__) ^ hash(frozenset(self.__recordtypes__.items()))
    
    def __instancecheck__(self, instance):
        if not isinstance(instance, collections.Mapping):
            return False
        if not self.__recordtypes__:
            return True
        # Whether strict or non-strict, we must have enough positions to fulfil the expected types
        if len(instance) < len(self.__recordtypes__):
            return False
        if self.__strict__ and len(instance) != len(self.__recordtypes__):
            return False
        try:
            return all(isinstance(instance[k], t) for k, t in self.__recordtypes__.items())
        except LookupError:
            return False
    
    def __subclasscheck__(self, cls):
        # A Mapping is a special case
        if issubclass(cls, collections.Mapping):
            return True
        # We only do further checks for other record types
        if not isinstance(cls, RecordMeta):
            return super().__subclasscheck__(cls)
        # Check each key in cls is a subclass of the corresponding key in self
        if not self.__recordtypes__:
            return True
        if not cls.__recordtypes__:
            return False
        # Whether strict or non-strict, we must have enough positions to fulfil the expected types
        if len(cls.__recordtypes__) < len(self.__recordtypes__):
            return False
        if self.__strict__:
            if not cls.__strict__ or len(self.__recordtypes__) != len(cls.__recordtypes__):
                return False
        try:
            return all(issubclass(cls.__recordtypes__[k], t) for k, t in self.__recordtypes__.items())
        except LookupError:
            return False
    
    def __repr__(self):
        def types():
            for k, t in (self.__recordtypes__ or {}).items():
                yield "%s: %s" % (k, t.__name__ )
            if not self.__strict__:
                yield "..." 
        return 'Record[%s]' % ', '.join(types())


class Record(metaclass = RecordMeta):
    """
    Parameterisable type for records, e.g. Record['x': int, 'y': str] means a mapping type where
    key 'x' is an int and key 'y' is a string
    
    If an ellipsis (...) is given as the last type argument, that means other keys can be present
    but are not type checked
    """
    __recordtypes__ = None
    __strict__      = True
    
    
class HasAttrsMeta(TypeMeta):
    """
    Metaclass for the HasAttr type
    """
    
    def __getitem__(self, types):
        if self.__attrtypes__:
            raise TypeError('Cannot re-parameterise an existing structural type')
        if not isinstance(types, tuple):
            types = (types, )
        # Change a tuple of slices into a mapping of keys to types
        attrtypes = collections.OrderedDict()
        for s in types:
            if not isinstance(s, slice):
                raise SyntaxError('Error in record type specification')
            k = s.start
            t = s.stop
            if t is None:
                t = type(None)
            if not isinstance(t, type):
                raise TypeError('Cannot parameterise structural type with non-type argument')
            attrtypes[k] = t
        if not attrtypes:
            raise TypeError('Cannot create an unparameterised structural type')
        cls = self.__class__(self.__name__, self.__bases__, dict(self.__dict__))
        cls.__attrtypes__ = MappingProxyType(attrtypes)
        return cls
    
    def __eq__(self, other):
        if not isinstance(other, HasAttrsMeta):
            return NotImplemented
        return self.__attrtypes__ == other.__attrtypes__
    
    def __hash__(self):
        return hash(frozenset(self.__attrtypes__.items()))
    
    def __instancecheck__(self, instance):
        if not self.__attrtypes__:
            return True
        try:
            return all(isinstance(getattr(instance, k), t) for k, t in self.__attrtypes__.items())
        except AttributeError:
            return False
    
    def __subclasscheck__(self, cls):
        # We only do checks for other structural types
        if not isinstance(cls, HasAttrsMeta):
            return super().__subclasscheck__(cls)
        # Check each key in cls is a subclass of the corresponding key in self
        if not self.__attrtypes__:
            return True
        if not cls.__attrtypes__:
            return False
        try:
            return all(issubclass(cls.__attrtypes__[k], t) for k, t in self.__attrtypes__.items())
        except LookupError:
            return False
    
    def __repr__(self):
        return 'HasAttrs[%s]' % ', '.join(
            "%s: %s" % (k, t.__name__ ) for k, t in (self.__attrtypes__ or {}).items()
        )


class HasAttrs(metaclass = HasAttrsMeta):
    """
    Parameterisable type for structural typing, e.g. HasAttrs['x': int, 'y': str] means an object
    that has an attribute x that is an int and an attribute y that is a string
    """
    __attrtypes__ = None
    
    
class CallableMeta(TypeMeta):
    """
    Metaclass for the Callable type
    """

    def __getitem__(self, types):
        if self.__argtypes__ is not None:
            raise TypeError('Cannot re-parameterise an existing callable')
        if not isinstance(types, tuple):
            types = (types, )
        # There must be at least one type
        if len(types) < 1:
            raise TypeError('Callable requires at least one type to be specified')
        argtypes = []
        *types, returntype = types
        # Check the argument types
        for t in types:
            if t is None:
                t = type(None)
            if not isinstance(t, type):
                raise TypeError('Cannot parameterise callable with non-type argument')
            argtypes.append(t)
        # Check the return type
        if returntype is None:
            returntype = type(None)
        if not isinstance(returntype, type):
            raise TypeError('Cannot parameterise callable with non-type argument') 
        cls = self.__class__(self.__name__, self.__bases__, dict(self.__dict__))
        cls.__argtypes__ = tuple(argtypes)
        cls.__returntype__ = returntype
        return cls
    
    def __eq__(self, other):
        if not isinstance(other, CallableMeta):
            return NotImplemented
        return self.__argtypes__ == other.__argtypes__ and \
               self.__returntype__ == other.__returntype__
    
    def __hash__(self):
        return hash(self.__argtypes__) ^ hash(self.__returntype__)
    
    def __instancecheck__(self, instance):
        if not isinstance(instance, collections.Callable):
            return False
        # If we are unparameterised, any callable fits
        if self.__argtypes__ is None:
            return True
        sig = signature(instance)
        # NOTE: If no annotation is present, or the annotation is not None or a type, then
        #       it is not verified
        # Check the return annotation
        # If present, the return type must be covariant with (e.g. at least as restrictive as) self
        if sig.return_annotation is not S.empty:
            returntype = sig.return_annotation
            if returntype is None:
                returntype = type(None)
            if isinstance(returntype, type) and not issubclass(returntype, self.__returntype__):
                return False            
        # Get the positional parameters of the function
        positional = [p for p in sig.parameters.values() \
                          if p.kind is P.POSITIONAL_ONLY or p.kind is P.POSITIONAL_OR_KEYWORD]
        # For each expected type, there must be a parameter
        # If the parameter has a type annotation, it must be contravariant with (e.g. less
        # restrictive than) the corresponding type from self
        for t in self.__argtypes__:
            try:
                a = positional.pop(0).annotation
                if a is P.empty:
                    continue
                if a is None:
                    a = type(None)
                if isinstance(a, type) and not issubclass(t, a):
                    return False
            except IndexError:
                return False
        # Any remaining positional parameters must have default values
        if any(p.default is P.empty for p in positional):
            return False
        # If we get here, we have a match
        return True
    
    def __subclasscheck__(self, cls):
        # Callables are a special case
        if issubclass(cls, collections.Callable):
            return True
        # We only do further checks for other callables
        if not isinstance(cls, CallableMeta):
            return super().__subclasscheck__(cls)
        # If self is unparameterised, anything is a subclass
        if self.__argtypes__ is None:
            return True
        # If cls is unparameterised, it is not a subclass
        if cls.__argtypes__ is None:
            return False
        # Return type must be covariant (e.g. at least as restrictive) with self
        if not issubclass(cls.__returntype__, self.__returntype__):
            return False
        # There must be the same number of types
        if len(cls.__argtypes__) != len(self.__argtypes__):
            return False
        # Each argument type must be contravariant (e.g. less restrictive) with the corresponding
        # type from self
        return all(issubclass(t1, t2) for t1, t2 in zip(self.__argtypes__, cls.__argtypes__))
    
    def __repr__(self):
        def types():
            for t in (self.__argtypes__ or ()):
                yield t.__name__
            if self.__returntype__ is None or self.__returntype__ is type(None):
                yield "None"
            else:
                yield self.__returntype__.__name__
        return 'Callable[%s]' % ', '.join(types())


class Callable(metaclass = CallableMeta):
    """
    Parameterisable type for callables
    
    By convention, the last type signifies the return type, and all other types are for
    positional arguments
    
    Instance testing is done by inspecting the annotations of the given callable
    If a parameter has no annotation or the annotation is not a type, it is assumed to satisfy
    the requirement
    A callable is an instance if:
      1. It has at least N positional arguments
      2. The first N positional arguments satisfy the given requirements
      3. All other positional arguments are optional (i.e. have a default value)
    """
    __argtypes__   = None
    __returntype__ = None
