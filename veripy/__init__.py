"""
This package provides contracts for Python functions

Contracts are defined purely in terms of types, so this package also defines some
useful types, such as unions, intersections, dependent and existential types

@author: Matt Pryor <mkjpryor@gmail.com>
"""

import functools, inspect
from inspect import Parameter as P, Signature as S


# Set this to False to disable verification
verify = True


def from_annotations(f):
    """
    Decorator that enforces contracts defined in function annotations
    """
    # Deduce arguments to expects from the function annotations
    s = inspect.signature(f)
    # Build a map of parameter name to type
    arguments = { k : p.annotation for k, p in s.parameters.items() if p.annotation is not P.empty }
    returns = s.return_annotation if s.return_annotation is not S.empty else object
    return expects(arguments, returns)(f)


def expects(arguments = {}, returns = object):
    """
    Returns a decorator that enforces the given contracts for the decorated function
    
    arguments is a mapping (e.g. dict) of argument name to type
    returns is the expected return type
    """
    # We allow None to be specified instead of NoneType, so convert them
    # Other than that, types must be supplied
    for k in arguments.keys():
        if arguments[k] is None:
            arguments[k] = type(None)
        if not isinstance(arguments[k], type):
            raise TypeError('Argument expectations must be type or None')
    returns = returns if returns is not None else type(None)
    if not isinstance(returns, type):
        raise TypeError('Return expectation must be type or None')
    
    def decorator(f):
        sig = inspect.signature(f)
        
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            # If verification is off, do nothing
            if not verify: return f(*args, **kwargs)
            # Otherwise, we need to check our constraints
            # First, bind the given arguments to the arguments of f
            bound = sig.bind(*args, **kwargs)
            # Verify that the given arguments match the specified types
            for k, v in bound.arguments.items():
                if k in arguments and not isinstance(v, arguments[k]):
                    raise TypeError("Incorrect type for %s - "
                                    "expected %s ; got: %s" % (k, repr(arguments[k]), repr(type(v))))
            # Check the return value against the return type
            result = f(*args, **kwargs)
            if isinstance(result, returns):
                return result
            else:
                raise TypeError("Incorrect return type - "
                                "expected %s ; got: %s" % (repr(returns), repr(type(result))))
        return wrapper
    return decorator
