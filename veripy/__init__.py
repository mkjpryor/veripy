"""
This package provides contracts for Python functions

Contracts are defined purely in terms of types, so this package also defines some
useful types, such as unions, intersections, dependent and existential types

@author: Matt Pryor <mkjpryor@gmail.com>
"""

import functools, inspect
from inspect import Parameter as P, Signature as S


# Set this to False to disable type verification
enabled = True


def verify(f):
    """
    Decorator that enforces contracts defined in function annotations
    
    If a parameter has no annotation, or the annotation is not a type, no verification is
    performed for that parameter
    Similarly, if no return annotation is given, or the annotation is not a type, no verification
    is performed on the return value
    The only non-type annotation that is interpreted is None, which is taken to mean NoneType  
    """
    # Get the valid parameter and returns annotations
    s = inspect.signature(f)
    # Parameter types are stored as a map of name => type
    argtypes = {}
    for k, a in ((k, p.annotation) for k, p in s.parameters.items() if p.annotation is not P.empty):
        if a is None:
            a = type(None)
        if not isinstance(a, type):
            continue
        argtypes[k] = a
    # See if there is a return type
    returntype = None
    if s.return_annotation is not S.empty:
        returntype = s.return_annotation
        if returntype is None:
            returntype = type(None)
        if not isinstance(returntype, type):
            returntype = None
    
    # Return a function that verifies the types before and after the call
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        # If verification is off, do nothing
        if not enabled: return f(*args, **kwargs)
        # Otherwise, we need to check our constraints
        # First, bind the given args to the args of f
        bound = s.bind(*args, **kwargs)
        # Verify that the given args match the specified types
        for k, v in bound.arguments.items():
            if k in argtypes and not isinstance(v, argtypes[k]):
                raise TypeError("Incorrect type for %s - "
                                "expected %s ; got: %s" % (k, repr(argtypes[k]), repr(type(v))))
        # Check the return value against the return type
        result = f(*args, **kwargs)
        if returntype is None or isinstance(result, returntype):
            return result
        else:
            raise TypeError("Incorrect return type - "
                            "expected %s ; got: %s" % (repr(returntype), repr(type(result))))
    return wrapper
