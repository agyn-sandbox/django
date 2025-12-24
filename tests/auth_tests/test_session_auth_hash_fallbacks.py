from unittest import mock

from django.contrib.auth import HASH_SESSION_KEY, SESSION_KEY, get_user_model
from django.test import TestCase, override_settings
from django.utils.crypto import salted_hmac


@override_settings(ROOT_URLCONF="auth_tests.urls")
class SessionAuthHashFallbackTests(TestCase):
    password = "passw0rd!"

    def create_user(self, username):
        return get_user_model().objects.create_user(
            username=username,
            password=self.password,
        )

    def login_with_secret(self, user, secret):
        with override_settings(SECRET_KEY=secret, SECRET_KEY_FALLBACKS=[]):
            logged_in = self.client.login(
                username=user.get_username(),
                password=self.password,
            )
            self.assertTrue(logged_in)
            session = self.client.session
            return session.session_key, session.get(HASH_SESSION_KEY)

    def test_session_auth_hash_validated_against_fallbacks_and_upgraded(self):
        user = self.create_user("fallback-upgrade")
        original_session_key, original_hash = self.login_with_secret(user, "oldsecret")

        with override_settings(
            SECRET_KEY="newsecret",
            SECRET_KEY_FALLBACKS=["oldsecret"],
        ):
            response = self.client.get("/auth_processor_user/")
            self.assertTrue(response.wsgi_request.user.is_authenticated)
            upgraded_session = self.client.session
            self.assertNotEqual(upgraded_session.session_key, original_session_key)
            self.assertEqual(
                upgraded_session[HASH_SESSION_KEY],
                user.get_session_auth_hash(),
            )
            self.assertNotEqual(upgraded_session[HASH_SESSION_KEY], original_hash)

    def test_session_auth_hash_mismatch_flushes_session(self):
        user = self.create_user("fallback-mismatch")
        original_session_key, _ = self.login_with_secret(user, "oldsecret")

        session = self.client.session
        session[HASH_SESSION_KEY] = "invalid"
        session.save()

        with override_settings(
            SECRET_KEY="newsecret",
            SECRET_KEY_FALLBACKS=["oldsecret"],
        ):
            response = self.client.get("/auth_processor_user/")
            self.assertFalse(response.wsgi_request.user.is_authenticated)
            flushed_session = self.client.session
            self.assertNotIn(SESSION_KEY, flushed_session)
            self.assertNotIn(HASH_SESSION_KEY, flushed_session)

    def test_no_fallbacks_configured_behaves_as_before(self):
        user = self.create_user("fallback-disabled")
        original_session_key, _ = self.login_with_secret(user, "oldsecret")

        with override_settings(SECRET_KEY="newsecret", SECRET_KEY_FALLBACKS=[]):
            response = self.client.get("/auth_processor_user/")
            self.assertFalse(response.wsgi_request.user.is_authenticated)
            flushed_session = self.client.session
            self.assertNotIn(SESSION_KEY, flushed_session)
            self.assertNotIn(HASH_SESSION_KEY, flushed_session)

    def test_custom_get_session_auth_hash_is_respected(self):
        user = self.create_user("fallback-custom")

        def custom_get_session_auth_hash(self):
            return salted_hmac(
                "tests.auth_tests.custom_session_auth_hash_salt",
                self.password,
                algorithm="sha256",
            ).hexdigest()

        with mock.patch.object(
            user.__class__,
            "get_session_auth_hash",
            custom_get_session_auth_hash,
        ):
            original_session_key, _ = self.login_with_secret(user, "oldsecret")

            with override_settings(
                SECRET_KEY="newsecret",
                SECRET_KEY_FALLBACKS=["oldsecret"],
            ):
                response = self.client.get("/auth_processor_user/")
                self.assertFalse(response.wsgi_request.user.is_authenticated)
                flushed_session = self.client.session
                self.assertNotIn(SESSION_KEY, flushed_session)
                self.assertNotIn(HASH_SESSION_KEY, flushed_session)
