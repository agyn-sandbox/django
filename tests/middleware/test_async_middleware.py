import asyncio
from unittest.mock import patch

from asgiref.testing import ApplicationCommunicator

from django.conf import settings
from django.core.asgi import get_asgi_application
from django.core.cache import caches
from django.http import HttpResponse
from django.http.response import HttpResponseBase
from django.middleware.cache import CacheMiddleware, UpdateCacheMiddleware
from django.middleware.security import SecurityMiddleware
from django.test import AsyncRequestFactory, SimpleTestCase, override_settings
from django.urls import path


async def async_ok_view(request):
    return HttpResponse('ok')


urlpatterns = [
    path('', async_ok_view),
]


class AsyncMiddlewareProcessResponseTests(SimpleTestCase):
    async_request_factory = AsyncRequestFactory()

    async def _communicate_via_asgi(self):
        application = get_asgi_application()
        scope = self.async_request_factory._base_scope(path='/')
        communicator = ApplicationCommunicator(application, scope)
        await communicator.send_input({'type': 'http.request'})
        response_start = await communicator.receive_output()
        self.assertEqual(response_start['type'], 'http.response.start')
        self.assertEqual(response_start['status'], 200)
        response_body = await communicator.receive_output()
        self.assertEqual(response_body['type'], 'http.response.body')
        self.assertEqual(response_body['body'], b'ok')
        await communicator.wait()

    async def _assert_process_response_receives_http_response(self, middleware, middleware_class):
        caches[settings.CACHE_MIDDLEWARE_ALIAS].clear()
        original = middleware_class.process_response

        def assert_wrapper(middleware_self, request, response):
            self.assertIsInstance(response, HttpResponseBase)
            self.assertFalse(asyncio.iscoroutine(response))
            result = original(middleware_self, request, response)
            stream = getattr(request, '_stream', None)
            if stream is not None:
                stream.close()
            return result

        with override_settings(MIDDLEWARE=middleware, ROOT_URLCONF='tests.middleware.test_async_middleware'):
            with patch.object(
                middleware_class,
                'process_response',
                autospec=True,
                side_effect=assert_wrapper,
            ) as mocked:
                await self._communicate_via_asgi()
                self.assertEqual(mocked.call_count, 1)

    async def test_security_middleware_process_response_receives_http_response(self):
        await self._assert_process_response_receives_http_response(
            ['django.middleware.security.SecurityMiddleware'],
            SecurityMiddleware,
        )

    async def test_update_cache_middleware_process_response_receives_http_response(self):
        await self._assert_process_response_receives_http_response(
            [
                'django.middleware.cache.UpdateCacheMiddleware',
                'django.middleware.common.CommonMiddleware',
                'django.middleware.cache.FetchFromCacheMiddleware',
            ],
            UpdateCacheMiddleware,
        )

    async def test_cache_middleware_process_response_receives_http_response(self):
        await self._assert_process_response_receives_http_response(
            ['django.middleware.cache.CacheMiddleware'],
            CacheMiddleware,
        )
