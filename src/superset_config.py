from dateutil import tz
from flask_appbuilder.security.manager import AUTH_DB, AUTH_LDAP, AUTH_OID, AUTH_REMOTE_USER
from os import environ, path

DRUID_TIMEZONES = {
    "utc": tz.tzutc(),
    "local": tz.tzlocal()
}

AUTH_TYPES = {
    "oid": AUTH_OID,
    "db": AUTH_DB,
    "ldap": AUTH_LDAP,
    "remote_user": AUTH_REMOTE_USER
}


def get_cache_config(env_var_prefix):
    def set_config(config_dict, config_key, default=None):
        value = get_env("{}_{}".format(env_var_prefix, config_key), default)

        if value:
            config_dict[config_key] = value

    cache_config = {}

    set_config(cache_config, "CACHE_TYPE", "null")
    set_config(cache_config, "CACHE_NO_NULL_WARNING")
    set_config(cache_config, "CACHE_DEFAULT_TIMEOUT")
    set_config(cache_config, "CACHE_THRESHOLD")
    set_config(cache_config, "CACHE_KEY_PREFIX")
    set_config(cache_config, "CACHE_MEMCACHED_SERVERS")
    set_config(cache_config, "CACHE_MEMCACHED_USERNAME")
    set_config(cache_config, "CACHE_MEMCACHED_PASSWORD")
    set_config(cache_config, "CACHE_REDIS_HOST")
    set_config(cache_config, "CACHE_REDIS_PORT")
    set_config(cache_config, "CACHE_REDIS_PASSWORD")
    set_config(cache_config, "CACHE_REDIS_DB")
    set_config(cache_config, "CACHE_DIR")
    set_config(cache_config, "CACHE_REDIS_URL")

    return cache_config


def get_env(env_var, default, result_type: type = str):
    value = environ.get(env_var, default)

    if result_type == int:
        return int(value) if value else value
    elif result_type == bool:
        return str(value).lower() == "true" if value else value
    elif result_type == list:
        return value.split(",") if isinstance(value, str) else value
    else:
        return value


# ----------------------------
SUPERSET_LOG_VIEW = get_env("SUPERSET_LOG_VIEW", True, bool)
ROW_LIMIT = get_env("ROW_LIMIT", 50000, int)
VIZ_ROW_LIMIT = get_env("VIZ_ROW_LIMIT", 10000, int)
FILTER_SELECT_ROW_LIMIT = get_env("FILTER_SELECT_ROW_LIMIT", 10000, int)
SUPERSET_WEBSERVER_PROTOCOL = get_env("SUPERSET_WEBSERVER_PROTOCOL", "http")
SUPERSET_WEBSERVER_ADDRESS = get_env("SUPERSET_WEBSERVER_ADDRESS", "0.0.0.0")
SUPERSET_WEBSERVER_PORT = get_env("SUPERSET_WEBSERVER_PORT", 8088, int)
SUPERSET_WEBSERVER_TIMEOUT = get_env("SUPERSET_WEBSERVER_TIMEOUT", 60, int)
SUPERSET_DASHBOARD_POSITION_DATA_LIMIT = get_env("SUPERSET_DASHBOARD_POSITION_DATA_LIMIT", 65535, int)
CUSTOM_SECURITY_MANAGER = get_env("CUSTOM_SECURITY_MANAGER", None)
SQLALCHEMY_TRACK_MODIFICATIONS = get_env("SQLALCHEMY_TRACK_MODIFICATIONS", False, bool)
SECRET_KEY = get_env("SECRET_KEY", "\1\2thisismysecretkey\1\2\e\y\y\h")
SQLALCHEMY_DATABASE_URI = get_env("SQLALCHEMY_DATABASE_URI",
                                  "sqlite:////{}".format(path.join(environ["SUPERSET_HOME"], "superset.db")))
QUERY_SEARCH_LIMIT = get_env("QUERY_SEARCH_LIMIT", 1000, int)
WTF_CSRF_ENABLED = get_env("WTF_CSRF_ENABLED", True, bool)
WTF_CSRF_EXEMPT_LIST = get_env("WTF_CSRF_EXEMPT_LIST", ["superset.views.core.log"], list)
DEBUG = get_env("DEBUG", False, bool)
FLASK_USE_RELOAD = get_env("FLASK_USE_RELOAD", True, bool)
SHOW_STACKTRACE = get_env("SHOW_STACKTRACE", True, bool)
ENABLE_PROXY_FIX = get_env("ENABLE_PROXY_FIX", False, bool)
PROXY_FIX_CONFIG = {
    "x_for": get_env("PROXY_FIX_CONFIG_X_FOR", 1, int),
    "x_proto": get_env("PROXY_FIX_CONFIG_X_PROTO", 1, int),
    "x_host": get_env("PROXY_FIX_CONFIG_X_HOST", 1, int),
    "x_prefix": get_env("PROXY_FIX_CONFIG_X_PREFIX", 1, int)
}
APP_NAME = get_env("APP_NAME", "Superset")
APP_ICON = get_env("APP_ICON", "/static/assets/images/superset-logo@2x.png")
APP_ICON_WIDTH = get_env("APP_ICON_WIDTH", 126, int)
LOGO_TARGET_PATH = get_env("LOGO_TARGET_PATH", None)
FAB_API_SWAGGER_UI = get_env("FAB_API_SWAGGER_UI", True, bool)
DRUID_TZ = DRUID_TIMEZONES.get(get_env("DRUID_TZ", "utc"), tz.gettz(get_env("DRUID_TZ", "utc")))
DRUID_ANALYSIS_TYPES = get_env("DRUID_ANALYSIS_TYPES", ["cardinality"], list)
DRUID_IS_ACTIVE = get_env("DRUID_IS_ACTIVE", False, bool)
DRUID_METADATA_LINKS_ENABLED = get_env("DRUID_METADATA_LINKS_ENABLED", True, bool)
AUTH_TYPE = AUTH_TYPES.get(get_env("AUTH_TYPE", "db"))
PUBLIC_ROLE_LIKE_GAMMA = get_env("PUBLIC_ROLE_LIKE_GAMMA", False, bool)
BABEL_DEFAULT_LOCALE = get_env("BABEL_DEFAULT_LOCALE", "en")
BABEL_DEFAULT_FOLDER = get_env("BABEL_DEFAULT_FOLDER", "superset/translations")
FEATURE_FLAGS = {
    "CLIENT_CACHE": get_env("FEATURE_FLAG_CLIENT_CACHE", False, bool),
    "ENABLE_EXPLORE_JSON_CSRF_PROTECTION": get_env("FEATURE_FLAG_ENABLE_EXPLORE_JSON_CSRF_PROTECTION", False, bool),
    "KV_STORE": get_env("FEATURE_FLAG_KV_STORE", False, bool),
    "PRESTO_EXPAND_DATA": get_env("FEATURE_FLAG_PRESTO_EXPAND_DATA", False, bool),
    "THUMBNAILS": get_env("FEATURE_FLAG_THUMBNAILS", False, bool),
    "REDUCE_DASHBOARD_BOOTSTRAP_PAYLOAD": get_env("FEATURE_FLAG_REDUCE_DASHBOARD_BOOTSTRAP_PAYLOAD", True, bool),
    "SHARE_QUERIES_VIA_KV_STORE": get_env("FEATURE_FLAG_SHARE_QUERIES_VIA_KV_STORE", False, bool),
    "SIP_38_VIZ_REARCHITECTURE": get_env("FEATURE_FLAG_SIP_38_VIZ_REARCHITECTURE", False, bool),
    "TAGGING_SYSTEM": get_env("FEATURE_FLAG_TAGGING_SYSTEM", False, bool),
    "SQLLAB_BACKEND_PERSISTENCE": get_env("FEATURE_FLAG_SQLLAB_BACKEND_PERSISTENCE", False, bool),
    "LIST_VIEWS_NEW_UI": get_env("FEATURE_FLAG_LIST_VIEWS_NEW_UI", False, bool)
}
THUMBNAIL_SELENIUM_USER = get_env("THUMBNAIL_SELENIUM_USER", "Admin")
THUMBNAIL_CACHE_CONFIG = get_cache_config("THUMBNAIL_CACHE_CONFIG")
UPLOAD_FOLDER = get_env("UPLOAD_FOLDER", "{}/app/static/uploads/".format(path.abspath(path.dirname(__file__))))
UPLOAD_CHUNK_SIZE = get_env("UPLOAD_CHUNK_SIZE", 4096, int)
IMG_UPLOAD_FOLDER = get_env("IMG_UPLOAD_FOLDER", "{}/app/static/uploads/".format(path.abspath(path.dirname(__file__))))
IMG_UPLOAD_URL = get_env("IMG_UPLOAD_URL", "/static/uploads/")
CACHE_DEFAULT_TIMEOUT = get_env("CACHE_DEFAULT_TIMEOUT", 60 * 60 * 24, int)
CACHE_CONFIG = get_cache_config("CACHE_CONFIG")
TABLE_NAMES_CACHE_CONFIG = get_cache_config("TABLE_NAMES_CACHE_CONFIG")
ENABLE_CORS = get_env("ENABLE_CORS", False, bool)
CORS_OPTIONS = {
    "origins": get_env("CORS_OPTIONS_ORIGINS", ["*"], list),
    "methods": get_env("CORS_OPTIONS_METHODS", ["GET", "HEAD", "POST", "OPTIONS", "PUT", "PATCH", "DELETE"], list),
    "expose_headers": get_env("CORS_OPTIONS_EXPOSE_HEADERS", None, list),
    "allow_headers": get_env("CORS_OPTIONS_ALLOW_HEADERS", ["*"], list),
    "send_wildcard": get_env("CORS_OPTIONS_SEND_WILDCARD", False, bool),
    "vary_header": get_env("CORS_OPTIONS_VARY_HEADER", True, bool)
}
VIZ_TYPE_BLACKLIST = get_env("VIZ_TYPE_BLACKLIST", "").split(",")
DRUID_DATA_SOURCE_BLACKLIST = get_env("DRUID_DATA_SOURCE_BLACKLIST", "").split(",")
LOG_FORMAT = get_env("LOG_FORMAT", "%(asctime)s:%(levelname)s:%(name)s:%(message)s")
LOG_LEVEL = get_env("LOG_LEVEL", "DEBUG")
ENABLE_TIME_ROTATE = get_env("ENABLE_TIME_ROTATE", False, bool)
TIME_ROTATE_LOG_LEVEL = get_env("TIME_ROTATE_LOG_LEVEL", "DEBUG")
ROLLOVER = get_env("ROLLOVER", "midnight")
INTERVAL = get_env("INTERVAL", 1, int)
BACKUP_COUNT = get_env("BACKUP_COUNT", 30, int)
MAPBOX_API_KEY = get_env("MAPBOX_API_KEY", "")
SQL_MAX_ROW = get_env("SQL_MAX_ROW", 100000, int)
DISPLAY_MAX_ROW = get_env("DISPLAY_MAX_ROW", 10000, int)
DEFAULT_SQLLAB_LIMIT = get_env("DEFAULT_SQLLAB_LIMIT", 1000, int)
MAX_TABLE_NAMES = get_env("MAX_TABLE_NAMES", 3000, int)
SQLLAB_SAVE_WARNING_MESSAGE = get_env("SQLLAB_SAVE_WARNING_MESSAGE", None)
SQLLAB_SCHEDULE_WARNING_MESSAGE = get_env("SQLLAB_SCHEDULE_WARNING_MESSAGE", None)
WARNING_MSG = get_env("WARNING_MSG", None)
DEFAULT_DB_ID = get_env("DEFAULT_DB_ID", None)
SQLLAB_TIMEOUT = get_env("SQLLAB_TIMEOUT", 30, int)
SQLLAB_VALIDATION_TIMEOUT = get_env("SQLLAB_VALIDATION_TIMEOUT", 10, int)
SQLLAB_DEFAULT_DBID = get_env("SQLLAB_DEFAULT_DBID", None)
SQLLAB_ASYNC_TIME_LIMIT_SEC = get_env("SQLLAB_ASYNC_TIME_LIMIT_SEC", 60 * 60 * 6, int)
SQLLAB_QUERY_COST_ESTIMATE_TIMEOUT = get_env("SQLLAB_QUERY_COST_ESTIMATE_TIMEOUT", 10, int)
SQLLAB_CTAS_NO_LIMIT = get_env("SQLLAB_CTAS_NO_LIMIT", False, bool)
CSV_TO_HIVE_UPLOAD_S3_BUCKET = get_env("CSV_TO_HIVE_UPLOAD_S3_BUCKET", None)
CSV_TO_HIVE_UPLOAD_DIRECTORY = get_env("CSV_TO_HIVE_UPLOAD_DIRECTORY", "EXTERNAL_HIVE_TABLES/")
ENABLE_ACCESS_REQUEST = get_env("ENABLE_ACCESS_REQUEST", False, bool)
EMAIL_NOTIFICATIONS = get_env("EMAIL_NOTIFICATIONS", False, bool)
SMTP_HOST = get_env("SMTP_HOST", "localhost")
SMTP_STARTTLS = get_env("SMTP_STARTTLS", True, bool)
SMTP_SSL = get_env("SMTP_SSL", False, bool)
SMTP_USER = get_env("SMTP_USER", "superset")
SMTP_PORT = get_env("SMTP_PORT", 25, int)
SMTP_PASSWORD = get_env("SMTP_PASSWORD", "superset")
SMTP_MAIL_FROM = get_env("SMTP_MAIL_FROM", "superset@superset.com")
ENABLE_CHUNK_ENCODING = get_env("ENABLE_CHUNK_ENCODING", False, bool)
SILENCE_FAB = get_env("SILENCE_FAB", True, bool)
FAB_ADD_SECURITY_VIEWS = get_env("FAB_ADD_SECURITY_VIEWS", True, bool)
FAB_ADD_SECURITY_PERMISSION_VIEW = get_env("FAB_ADD_SECURITY_PERMISSION_VIEW", False, bool)
FAB_ADD_SECURITY_VIEW_MENU_VIEW = get_env("FAB_ADD_SECURITY_VIEW_MENU_VIEW", False, bool)
FAB_ADD_SECURITY_PERMISSION_VIEWS_VIEW = get_env("FAB_ADD_SECURITY_PERMISSION_VIEWS_VIEW", False, bool)
TROUBLESHOOTING_LINK = get_env("TROUBLESHOOTING_LINK", "")
WTF_CSRF_TIME_LIMIT = get_env("WTF_CSRF_TIME_LIMIT", 60 * 60 * 24 * 7, int)
PERMISSION_INSTRUCTIONS_LINK = get_env("PERMISSION_INSTRUCTIONS_LINK", "")
HIVE_POLL_INTERVAL = get_env("HIVE_POLL_INTERVAL", 5, int)
ENABLE_JAVASCRIPT_CONTROLS = get_env("ENABLE_JAVASCRIPT_CONTROLS", False, bool)
DASHBOARD_TEMPLATE_ID = get_env("DASHBOARD_TEMPLATE_ID", None)
ENABLE_FLASK_COMPRESS = get_env("ENABLE_FLASK_COMPRESS", True, bool)
ENABLE_SCHEDULED_EMAIL_REPORTS = get_env("ENABLE_SCHEDULED_EMAIL_REPORTS", False, bool)
SCHEDULED_EMAIL_DEBUG_MODE = get_env("SCHEDULED_EMAIL_DEBUG_MODE", False, bool)
EMAIL_REPORTS_CRON_RESOLUTION = get_env("EMAIL_REPORTS_CRON_RESOLUTION", 15, int)
EMAIL_ASYNC_TIME_LIMIT_SEC = get_env("EMAIL_ASYNC_TIME_LIMIT_SEC", 300, int)
EMAIL_REPORT_FROM_ADDRESS = get_env("EMAIL_REPORT_FROM_ADDRESS", "reports@superset.org")
EMAIL_REPORT_BCC_ADDRESS = get_env("EMAIL_REPORT_BCC_ADDRESS", None)
EMAIL_REPORTS_USER = get_env("EMAIL_REPORTS_USER", "admin")
EMAIL_REPORTS_SUBJECT_PREFIX = get_env("EMAIL_REPORTS_SUBJECT_PREFIX", "[Report] ")
EMAIL_REPORTS_WEBDRIVER = get_env("EMAIL_REPORTS_WEBDRIVER", "firefox")
WEBDRIVER_WINDOW = {
    "dashboard": (
        get_env("WEBDRIVER_WINDOW_DASHBOARD_WIDTH", 1600, int),
        get_env("WEBDRIVER_WINDOW_DASHBOARD_HEIGHT", 2000, int)
    ),
    "slice": (
        get_env("WEBDRIVER_WINDOW_SLICE_WIDTH", 3000, int),
        get_env("WEBDRIVER_WINDOW_SLICE_HEIGHT", 1200, int)
    )
}
WEBDRIVER_BASEURL = get_env("WEBDRIVER_BASEURL", "http://0.0.0.0:8080/")
BUG_REPORT_URL = get_env("BUG_REPORT_URL", None)
DOCUMENTATION_URL = get_env("DOCUMENTATION_URL", None)
DOCUMENTATION_TEXT = get_env("DOCUMENTATION_TEXT", "Documentation")
DOCUMENTATION_ICON = get_env("DOCUMENTATION_ICON", None)
ENABLE_REACT_CRUD_VIEWS = get_env("ENABLE_REACT_CRUD_VIEWS", False, bool)
DEFAULT_RELATIVE_START_TIME = get_env("DEFAULT_RELATIVE_START_TIME", "today")
DEFAULT_RELATIVE_END_TIME = get_env("DEFAULT_RELATIVE_END_TIME", "today")
TALISMAN_ENABLED = get_env("TALISMAN_ENABLED", False, bool)
TALISMAN_CONFIG = {
    "content_security_policy": get_env("TALISMAN_CONFIG_CONTENT_SECURITY_POLICY", None),
    "force_https": get_env("TALISMAN_CONFIG_FORCE_HTTPS", True, bool),
    "force_https_perman ent": get_env("TALISMAN_CONFIG_FORCE_HTTPS_PERMANENT", False, bool)
}
ENABLE_ROW_LEVEL_SECURITY = get_env("ENABLE_ROW_LEVEL_SECURITY", False, bool)
SESSION_COOKIE_HTTPONLY = get_env("SESSION_COOKIE_HTTPONLY", True, bool)
SESSION_COOKIE_SECURE = get_env("SESSION_COOKIE_SECURE", False, bool)
SESSION_COOKIE_SAMESITE = get_env("SESSION_COOKIE_SAMESITE", "Lax")
SEND_FILE_MAX_AGE_DEFAULT = get_env("SEND_FILE_MAX_AGE_DEFAULT", 60 * 60 * 24 * 365, int)
SQLALCHEMY_EXAMPLES_URI = get_env("SQLALCHEMY_EXAMPLES_URI", None)
PREVENT_UNSAFE_DB_CONNECTIONS = get_env("PREVENT_UNSAFE_DB_CONNECTIONS", True, bool)
SSL_CERT_PATH = get_env("SSL_CERT_PATH", None)
SIP_15_ENABLED = get_env("SIP_15_ENABLED", True, bool)
SIP_15_GRACE_PERIOD_END = get_env("SIP_15_GRACE_PERIOD_END", None)
SIP_15_DEFAULT_TIME_RANGE_ENDPOINTS = get_env("SIP_15_DEFAULT_TIME_RANGE_ENDPOINTS", ["unknown", "inclusive"], list)


class CeleryConfig:
    BROKER_URL = get_env("CELERY_BROKER_URL", "sqla+sqlite:///celerydb.sqlite")
    CELERY_IMPORTS = ("superset.sql_lab", "superset.tasks")
    CELERY_RESULT_BACKEND = get_env("CELERY_RESULT_BACKEND", "db+sqlite:///celery_results.sqlite")
    CELERYD_LOG_LEVEL = get_env("CELERYD_LOG_LEVEL", "DEBUG")
    CELERY_ACKS_LATE = get_env("CELERY_ACKS_LATE", False, bool)
    CELERY_ANNOTATIONS = {
        "sql_lab.get_sql_results": {
            "rate_limit": "{}/s".format(get_env("CELERY_SQLLAB_GET_RESULTS_RATE_LIMIT_IN_SECS", "100"))
        },
        "email_reports.send": {
            "rate_limit": "{}/s".format(get_env("CELERY_EMAIL_REPORTS_SEND_RATE_LIMIT_IN_SECS", "1")),
            "time_limit": get_env("CELERY_EMAIL_REPORTS_TIME_LIMIT", 120, int),
            "soft_time_limit": get_env("CELERY_EMAIL_REPORTS_SOFT_TIME_LIMIT", 150, int),
            "ignore_result": get_env("CELERY_EMAIL_REPORTS_IGNORE_RESULT", True, bool)
        }
    }


CELERY_CONFIG = CeleryConfig
