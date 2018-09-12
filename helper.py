""":mod:`helper` --- Helpers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Provides various utilities.

"""
import asyncio
import functools

from flask import current_app, request, abort

from util import async_response


__all__ = ['async', 'websocket', 'has_websocket', 'wrap_wsgi_middleware']


def async(fn):

    fn = asyncio.coroutine(fn)

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        coroutine = functools.partial(fn, *args, **kwargs)
        return async_response(coroutine(), current_app, request)
    return wrapper


def websocket(fn=None, *, failure_status_code: int=400):
    if fn is not None:
        return websocket(failure_status_code=400)(fn)

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not has_websocket():
                # Accept only websocket request
                abort(failure_status_code)
            else:
                yield from func(*args, **kwargs)
                return 'Done', 200
        return async(wrapper)
    return decorator


def has_websocket() -> bool:
    return request.environ.get('wsgi.websocket', None) is not None


def wrap_wsgi_middleware(middleware, *args):
    def wrapper(wsgi):
        _signal = object()
        @functools.wraps(wsgi)
        def wsgi_wrapper(environ, start_response):
            rv = yield from wsgi(environ, start_response)
            yield _signal
            yield rv
        concrete_middleware = middleware(wsgi_wrapper, *args)
        @functools.wraps(concrete_middleware)
        @asyncio.coroutine
        def wrapped(environ, start_response):
            iterator = iter(concrete_middleware(environ, start_response))
            while True:
                item = next(iterator)
                if item is not _signal:
                    yield item
                else:
                    break
            rv = next(iterator)
            return rv
        return wrapped
    return wrapper
