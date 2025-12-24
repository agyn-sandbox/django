import traceback
from django.db.backends.mysql.base import DatabaseWrapper


settings_dict = {
    'NAME': 'testdb',
    'USER': 'testuser',
    'PASSWORD': 'testpass',
    'HOST': '127.0.0.1',
    'PORT': '3306',
    'OPTIONS': {},
    'AUTOCOMMIT': True,
    'ATOMIC_REQUESTS': False,
    'CONN_MAX_AGE': 0,
    'ENGINE': 'django.db.backends.mysql',
    'TIME_ZONE': 'UTC',
    'DISABLE_SERVER_SIDE_CURSORS': False,
}


wrapper = DatabaseWrapper(settings_dict)
params = wrapper.get_connection_params()
print("Connection params:", params)
assert 'database' in params, "Expected 'database' key (canonical), but got legacy keys: %r" % params
assert 'password' in params, "Expected 'password' key (canonical), but got legacy keys: %r" % params
try:
    wrapper.get_new_connection(params)
except Exception:
    traceback.print_exc()
