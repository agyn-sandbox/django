from unittest.mock import patch

from django.conf import settings
from django.test import SimpleTestCase
from django.urls import clear_url_caches, get_resolver, get_urlconf, set_urlconf
from django.urls.resolvers import URLResolver


class ResolverCacheNormalizationTests(SimpleTestCase):
    def setUp(self):
        super().setUp()
        clear_url_caches()
        set_urlconf(None)
        self.addCleanup(clear_url_caches)
        self.addCleanup(set_urlconf, None)

    def test_get_resolver_none_and_root_share_instance(self):
        clear_url_caches()
        resolver_none = get_resolver(None)
        resolver_root = get_resolver(settings.ROOT_URLCONF)
        self.assertIs(resolver_none, resolver_root)

    def test_populate_runs_once_for_default_and_explicit(self):
        counter = {'calls': 0}
        original_populate = URLResolver._populate

        def counting_populate(self):
            counter['calls'] += 1
            return original_populate(self)

        with patch.object(URLResolver, '_populate', counting_populate):
            resolver_none = get_resolver(None)
            _ = resolver_none.reverse_dict
            set_urlconf(settings.ROOT_URLCONF)
            resolver_root = get_resolver(get_urlconf())
            _ = resolver_root.reverse_dict

        self.assertEqual(counter['calls'], 1)

    def test_custom_urlconf_still_caches_separately(self):
        resolver_none = get_resolver(None)
        resolver_custom = get_resolver('urlpatterns_reverse.named_urls')
        self.assertIsNot(resolver_none, resolver_custom)
