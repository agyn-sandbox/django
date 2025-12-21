import asyncio

from django.core.exceptions import MiddlewareNotUsed
from django.http import Http404, HttpResponse
from django.template import engines
from django.template.response import TemplateResponse
from django.utils.decorators import (
    async_only_middleware, sync_and_async_middleware, sync_only_middleware,
)

log = []


def _is_async_callable(callback):
    if asyncio.iscoroutinefunction(callback):
        return True
    call = getattr(callback, '__call__', None)
    return asyncio.iscoroutinefunction(call)


class BaseMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)


class ProcessExceptionMiddleware(BaseMiddleware):
    def process_exception(self, request, exception):
        return HttpResponse('Exception caught')


@async_only_middleware
class AsyncProcessExceptionMiddleware(BaseMiddleware):
    async def process_exception(self, request, exception):
        return HttpResponse('Exception caught')


class ProcessExceptionLogMiddleware(BaseMiddleware):
    def process_exception(self, request, exception):
        log.append('process-exception')


class ProcessExceptionExcMiddleware(BaseMiddleware):
    def process_exception(self, request, exception):
        raise Exception('from process-exception')


class ProcessViewMiddleware(BaseMiddleware):
    def process_view(self, request, view_func, view_args, view_kwargs):
        return HttpResponse('Processed view %s' % view_func.__name__)


@async_only_middleware
class AsyncProcessViewMiddleware(BaseMiddleware):
    async def process_view(self, request, view_func, view_args, view_kwargs):
        return HttpResponse('Processed view %s' % view_func.__name__)


class ProcessViewNoneMiddleware(BaseMiddleware):
    def process_view(self, request, view_func, view_args, view_kwargs):
        log.append('processed view %s' % view_func.__name__)
        return None


class ProcessViewTemplateResponseMiddleware(BaseMiddleware):
    def process_view(self, request, view_func, view_args, view_kwargs):
        template = engines['django'].from_string('Processed view {{ view }}{% for m in mw %}\n{{ m }}{% endfor %}')
        return TemplateResponse(request, template, {'mw': [self.__class__.__name__], 'view': view_func.__name__})


class TemplateResponseMiddleware(BaseMiddleware):
    def process_template_response(self, request, response):
        response.context_data['mw'].append(self.__class__.__name__)
        return response


@async_only_middleware
class AsyncTemplateResponseMiddleware(BaseMiddleware):
    async def process_template_response(self, request, response):
        response.context_data['mw'].append(self.__class__.__name__)
        return response


class LogMiddleware(BaseMiddleware):
    def __call__(self, request):
        response = self.get_response(request)
        log.append((response.status_code, response.content))
        return response


class NoTemplateResponseMiddleware(BaseMiddleware):
    def process_template_response(self, request, response):
        return None


@async_only_middleware
class AsyncNoTemplateResponseMiddleware(BaseMiddleware):
    async def process_template_response(self, request, response):
        return None


class NotFoundMiddleware(BaseMiddleware):
    def __call__(self, request):
        raise Http404('not found')


class PaymentMiddleware(BaseMiddleware):
    def __call__(self, request):
        response = self.get_response(request)
        response.status_code = 402
        return response


@async_only_middleware
def async_payment_middleware(get_response):
    async def middleware(request):
        response = await get_response(request)
        response.status_code = 402
        return response

    return middleware


@sync_and_async_middleware
class SyncAndAsyncMiddleware(BaseMiddleware):
    pass


@sync_only_middleware
class DecoratedPaymentMiddleware(PaymentMiddleware):
    pass


class NotSyncOrAsyncMiddleware(BaseMiddleware):
    """Middleware that is deliberately neither sync or async."""
    sync_capable = False
    async_capable = False

    def __call__(self, request):
        return self.get_response(request)


@sync_only_middleware
class NotUsedSyncMiddleware:

    def __init__(self, get_response):
        raise MiddlewareNotUsed


@async_only_middleware
class AsyncProbeMiddleware(BaseMiddleware):

    init_is_async = None

    def __init__(self, get_response):
        super().__init__(get_response)
        is_async = _is_async_callable(get_response)
        self.init_is_async = is_async
        AsyncProbeMiddleware.init_is_async = is_async

    async def __call__(self, request):
        response = await self.get_response(request)
        return response


@sync_only_middleware
class ToolbarSyncMiddleware(BaseMiddleware):

    init_is_async = None

    def __init__(self, get_response):
        super().__init__(get_response)
        is_async = _is_async_callable(get_response)
        self.init_is_async = is_async
        ToolbarSyncMiddleware.init_is_async = is_async
