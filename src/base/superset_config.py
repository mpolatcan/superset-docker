# Written by Mutlu Polatcan
# 05.05.2020
# -------------------------------------------------
# TODO Write environment variables list to Markdown
# TODO S3 result backend will be added
import json
from os import environ
from dateutil import tz
from celery.schedules import crontab
from flask_appbuilder.security.manager import AUTH_DB, AUTH_LDAP, AUTH_OID, AUTH_REMOTE_USER
from cachelib import SimpleCache, RedisCache, MemcachedCache
from superset.stats_logger import DummyStatsLogger, StatsdStatsLogger

ENV_VAR_TYPE_CASTER = {
    int: lambda value: int(value),
    float: lambda value: float(value),
    bool: lambda value: str(value).lower() == "true",
    list: lambda value: value.split(","),
    str: lambda value: value
}


def get_env(env_var, default=None, cast: type = str):
    value = environ.get(env_var, None)

    if value:
        return ENV_VAR_TYPE_CASTER[cast](value)
    else:
        return default

# --------------------------------------------------------------------


DRUID_TIMEZONES = {"utc": tz.tzutc(), "local": tz.tzlocal()}

AUTH_TYPES = {"oid": AUTH_OID, "db": AUTH_DB, "ldap": AUTH_LDAP, "remote_user": AUTH_REMOTE_USER}

METADATA_DB_PREFIXES = {"postgresql": "postgresql+psycopg2", "mysql": "mysql", "sqllite": "sqllite"}

METADATA_DB_DEFAULT_PORTS = {"postgresql": 5432, "mysql": 3306}

BROKER_PREFIXES = {"redis": "redis", "rabbitmq": "pyamqp"}

BROKER_DEFAULT_PORTS = {"redis": 6379, "rabbitmq": 5672}

RESULTS_BACKENDS = {
    "simple": lambda: SimpleCache(
        threshold=get_env("RESULTS_BACKEND_THRESHOLD", default=10, cast=int),
        default_timeout=get_env("RESULTS_BACKEND_DEFAULT_TIMEOUT", default=300, cast=float)
    ),
    "redis": lambda: RedisCache(
        host=get_env("RESULTS_BACKEND_REDIS_HOST"),
        port=get_env("RESULTS_BACKEND_REDIS_PORT", default=6379, cast=int),
        password=get_env("RESULTS_BACKEND_REDIS_PASSWORD"),
        key_prefix=get_env("RESULTS_BACKEND_REDIS_KEY_PREFIX", default="superset_results"),
        db=get_env("RESULTS_BACKEND_REDIS_DB", default=0, cast=int),
        default_timeout=get_env("RESULTS_BACKEND_DEFAULT_TIMEOUT", default=300, cast=float)
    ),
    "memcached": lambda: MemcachedCache(
        servers=get_env("RESULTS_BACKEND_MEMCACHED_SERVERS", default=[], cast=list),
        default_timeout=get_env("RESULTS_BACKEND_DEFAULT_TIMEOUT", default=300, cast=float),
        key_prefix=get_env("RESULTS_BACKEND_MEMCACHED_KEY_PREFIX", default="superset_results")
    )
}

RESULTS_BACKENDS_URIS = {
    "redis": "redis://{password}{host}:{port}/{db}".format(
        password="{}@".format(get_env("RESULTS_BACKEND_REDIS_PASSWORD"))
                 if get_env("RESULTS_BACKEND_REDIS_PASSWORD") else "",
        host=get_env("RESULTS_BACKEND_REDIS_HOST"),
        port=get_env("RESULTS_BACKEND_REDIS_PORT", default=6379),
        db=get_env("RESULTS_BACKEND_REDIS_DB", default=1)
    ),
    "memcached": "cache+memcached://{servers}/".format(
        servers=";".join(get_env("RESULTS_BACKEND_MEMCACHED_SERVERS", default=[], cast=list))
    )
}

STATS_LOGGERS = {
    "dummy": lambda: DummyStatsLogger(prefix=get_env("DUMMY_STATS_LOGGER_PREFIX", default="superset")),
    "statsd": lambda: StatsdStatsLogger(
        host=get_env("STATSD_STATS_LOGGER_HOST", default="localhost"),
        port=get_env("STATSD_STATS_LOGGER_PORT", default=8125, cast=int),
        prefix=get_env("STATSD_STATS_LOGGER_PREFIX", default="superset")
    )
}


def get_db_or_broker_uri(env_var_prefix, default_prefixes, default_ports):
    type = get_env("{}_TYPE".format(env_var_prefix))

    try:
        username = get_env("{}_USERNAME".format(env_var_prefix))
        password = get_env("{}_PASSWORD".format(env_var_prefix))

        return "{prefix}://{username}{password}{host}:{port}/{db}".format(
            prefix=default_prefixes[type],
            username="{}{}".format(username, ":" if password else "@") if username else "",
            password="{}@".format(password) if password else "",
            host=get_env("{}_HOST".format(env_var_prefix)),
            port=default_ports.get(type, None),
            db=get_env("{}_DATABASE".format(env_var_prefix))
        )
    except Exception:
        raise Exception("Wrong type \"{}\"".format(type))


def get_cache_config(env_var_prefix):
    def set_config(config_dict, config_key, default=None, cast: type = str):
        value = get_env("{}_{}".format(env_var_prefix, config_key), default=default, cast=cast)

        if value:
            config_dict[config_key] = value

    cache_config = {}

    for cache_config_info in [("TYPE", "null", str), ("NO_NULL_WARNING", bool), ("DEFAULT_TIMEOUT", int),
                              ("THRESHOLD", int), ("KEY_PREFIX", str), ("MEMCACHED_SERVERS", str),
                              ("MEMCACHED_SERVERS", str), ("MEMCACHED_PASSWORD", str), ("REDIS_HOST", str),
                              ("REDIS_PORT", 6379, int), ("REDIS_PASSWORD", str), ("REDIS_DB", 0, int), ("DIR", str)]:
        set_config(
            config_dict=cache_config,
            config_key="CACHE_{}".format(cache_config_info[0]),
            default=cache_config_info[1] if len(cache_config_info) > 2 else None,
            cast=cache_config_info[-1]
        )

    if cache_config["CACHE_TYPE"] == "redis":
        redis_password = cache_config.get("CACHE_REDIS_PASSWORD", None)

        cache_config["CACHE_REDIS_URL"] = "redis://{password}{host}:{port}/{db}".format(
            password="{}@".format(redis_password) if redis_password else "",
            host=cache_config.get("CACHE_REDIS_HOST", ""),
            port=cache_config.get("CACHE_REDIS_PORT", ""),
            db=cache_config.get("CACHE_REDIS_DB", "")
        )

    return cache_config


def get_celery_beat_schedule():
    celery_beat_schedule = {
        "email_reports.schedule_hourly": {
            "task": "email_reports.schedule_hourly",
            "schedule": crontab(minute=get_env("EMAIL_REPORTS_SCHEDULE_HOURLY_MINUTE", default="1"), hour="*")
        },
    }

    if get_env("ENABLE_CACHE_WARMUP", default=False, cast=bool):
        cache_warmups = json.loads(get_env("CACHE_WARMUPS"))

        for idx, cache_warmup in enumerate(cache_warmups):
            cache_warmup_id = "cache-warmup-{}".format(idx)

            celery_beat_schedule[cache_warmup_id] = {
                "task": "cache-warmup",
                "schedule": crontab(*cache_warmup["schedule"].split()),
                "kwargs": cache_warmup["kwargs"]
            }

    return celery_beat_schedule


# ------------------------------------------------------
APP_ICON = get_env("APP_ICON", default="/static/assets/images/superset-logo@2x.png")
APP_ICON_WIDTH = get_env("APP_ICON_WIDTH", default=126, cast=int)
APP_NAME = get_env("APP_NAME", default="Superset")
# ------------------------------------------------------

# ------------------------------------------------------
AUTH_TYPE = AUTH_TYPES.get(get_env("AUTH_TYPE", default="db"))
# ------------------------------------------------------

# ------------------------------------------------------
BABEL_DEFAULT_LOCALE = get_env("BABEL_DEFAULT_LOCALE", default="en")
BABEL_DEFAULT_FOLDER = get_env("BABEL_DEFAULT_FOLDER", default="superset/translations")
# ------------------------------------------------------

# ------------------------------------------------------
BACKUP_COUNT = get_env("BACKUP_COUNT", default=30, cast=int)
# ------------------------------------------------------

# ------------------------------------------------------
BUG_REPORT_URL = get_env("BUG_REPORT_URL")
# ------------------------------------------------------

# ------------------------------------------------------
CACHE_CONFIG = get_cache_config("CACHE_CONFIG")
CACHE_DEFAULT_TIMEOUT = get_env("CACHE_DEFAULT_TIMEOUT", default=60 * 60 * 24, cast=int)
# ------------------------------------------------------


# ------------------------------------------------------
class CeleryConfig:
    BROKER_URL = get_db_or_broker_uri("CELERY_BROKER", BROKER_PREFIXES, BROKER_DEFAULT_PORTS)
    CELERY_IMPORTS = ("superset.sql_lab", "superset.tasks")
    CELERY_RESULT_BACKEND = RESULTS_BACKENDS_URIS.get(get_env("RESULTS_BACKEND_TYPE", default="null"), "")
    CELERYD_LOG_LEVEL = get_env("CELERYD_LOG_LEVEL", default="DEBUG")
    CELERY_ACKS_LATE = get_env("CELERY_ACKS_LATE", default=False, cast=bool)
    CELERY_ANNOTATIONS = {
        "sql_lab.get_sql_results": {
            "rate_limit": get_env("CELERY_SQLLAB_GET_RESULTS_RATE_LIMIT", default="100/s")
        },
        "email_reports.send": {
            "rate_limit": get_env("CELERY_EMAIL_REPORTS_SEND_RATE_LIMIT_IN_SECS", default="1/s"),
            "time_limit": get_env("CELERY_EMAIL_REPORTS_TIME_LIMIT", default=120, cast=int),
            "soft_time_limit": get_env("CELERY_EMAIL_REPORTS_SOFT_TIME_LIMIT", default=150, cast=int),
            "ignore_result": get_env("CELERY_EMAIL_REPORTS_IGNORE_RESULT", default=True, cast=bool)
        }
    }
    CELERY_BEAT_SCHEDULE = get_celery_beat_schedule()


CELERY_CONFIG = CeleryConfig
# ------------------------------------------------------

# ------------------------------------------------------
CORS_OPTIONS = {
    "origins": get_env("CORS_OPTIONS_ORIGINS", default=["*"], cast=list),
    "methods": get_env("CORS_OPTIONS_METHODS", default=["GET", "HEAD", "POST", "OPTIONS", "PUT", "PATCH", "DELETE"], cast=list),
    "expose_headers": get_env("CORS_OPTIONS_EXPOSE_HEADERS", default=[], cast=list),
    "allow_headers": get_env("CORS_OPTIONS_ALLOW_HEADERS", default=["*"], cast=list),
    "send_wildcard": get_env("CORS_OPTIONS_SEND_WILDCARD", default=False, cast=bool),
    "vary_header": get_env("CORS_OPTIONS_VARY_HEADER", default=True, cast=bool)
}
# ------------------------------------------------------

# ------------------------------------------------------
CSV_TO_HIVE_UPLOAD_S3_BUCKET = get_env("CSV_TO_HIVE_UPLOAD_S3_BUCKET")
CSV_TO_HIVE_UPLOAD_DIRECTORY = get_env("CSV_TO_HIVE_UPLOAD_DIRECTORY", default="EXTERNAL_HIVE_TABLES/")
# ------------------------------------------------------

# ------------------------------------------------------
DEBUG = get_env("DEBUG", default=False, cast=bool)
# ------------------------------------------------------

# ------------------------------------------------------
DEFAULT_RELATIVE_START_TIME = get_env("DEFAULT_RELATIVE_START_TIME", default="today")
DEFAULT_RELATIVE_END_TIME = get_env("DEFAULT_RELATIVE_END_TIME", default="today")
DEFAULT_SQLLAB_LIMIT = get_env("DEFAULT_SQLLAB_LIMIT", default=1000, cast=int)
# ------------------------------------------------------

# ------------------------------------------------------
DISPLAY_MAX_ROW = get_env("DISPLAY_MAX_ROW", default=10000, cast=int)
# ------------------------------------------------------

# ------------------------------------------------------
DOCUMENTATION_URL = get_env("DOCUMENTATION_URL")
DOCUMENTATION_TEXT = get_env("DOCUMENTATION_TEXT", default="Documentation")
DOCUMENTATION_ICON = get_env("DOCUMENTATION_ICON")
# ------------------------------------------------------

# ------------------------------------------------------
DRUID_ANALYSIS_TYPES = get_env("DRUID_ANALYSIS_TYPES", default=["cardinality"], cast=list)
DRUID_DATA_SOURCE_BLACKLIST = get_env("DRUID_DATA_SOURCE_BLACKLIST", default=[], cast=list)
DRUID_IS_ACTIVE = get_env("DRUID_IS_ACTIVE", default=False, cast=bool)
DRUID_METADATA_LINKS_ENABLED = get_env("DRUID_METADATA_LINKS_ENABLED", default=False, cast=bool)
DRUID_TZ = DRUID_TIMEZONES.get(get_env("DRUID_TZ", default="utc"),
                               tz.gettz(get_env("DRUID_TZ", default="utc")))
# ------------------------------------------------------

# ------------------------------------------------------
EMAIL_ASYNC_TIME_LIMIT_SEC = get_env("EMAIL_ASYNC_TIME_LIMIT_SEC", default=300, cast=int)
EMAIL_NOTIFICATIONS = get_env("EMAIL_NOTIFICATIONS", default=False, cast=bool)
EMAIL_REPORT_BCC_ADDRESS = get_env("EMAIL_REPORT_BCC_ADDRESS")
EMAIL_REPORT_FROM_ADDRESS = get_env("EMAIL_REPORT_FROM_ADDRESS", default="reports@superset.org")
EMAIL_REPORTS_CRON_RESOLUTION = get_env("EMAIL_REPORTS_CRON_RESOLUTION", default=15, cast=int)
EMAIL_REPORTS_USER = get_env("EMAIL_REPORTS_USER", default="admin")
EMAIL_REPORTS_SUBJECT_PREFIX = get_env("EMAIL_REPORTS_SUBJECT_PREFIX", default="[Report] ")
EMAIL_REPORTS_WEBDRIVER = get_env("EMAIL_REPORTS_WEBDRIVER", default="firefox")
# ------------------------------------------------------

# ------------------------------------------------------
ENABLE_ACCESS_REQUEST = get_env("ENABLE_ACCESS_REQUEST", default=False, cast=bool)
# ------------------------------------------------------

# ------------------------------------------------------
ENABLE_CHUNK_ENCODING = get_env("ENABLE_CHUNK_ENCODING", default=False, cast=bool)
# ------------------------------------------------------

# ------------------------------------------------------
ENABLE_CORS = get_env("ENABLE_CORS", default=False, cast=bool)
# ------------------------------------------------------

# ------------------------------------------------------
ENABLE_FLASK_COMPRESS = get_env("ENABLE_FLASK_COMPRESS", default=True, cast=bool)
# ------------------------------------------------------

# ------------------------------------------------------
ENABLE_JAVASCRIPT_CONTROLS = get_env("ENABLE_JAVASCRIPT_CONTROLS", default=False, cast=bool)
# ------------------------------------------------------

# ------------------------------------------------------
ENABLE_PROXY_FIX = get_env("ENABLE_PROXY_FIX", default=False, cast=bool)
# ------------------------------------------------------

# ------------------------------------------------------
ENABLE_REACT_CRUD_VIEWS = get_env("ENABLE_REACT_CRUD_VIEWS", default=False, cast=bool)
# ------------------------------------------------------

# ------------------------------------------------------
ENABLE_SCHEDULED_EMAIL_REPORTS = get_env("ENABLE_SCHEDULED_EMAIL_REPORTS", default=False, cast=bool)
# ------------------------------------------------------

# ------------------------------------------------------
ENABLE_TIME_ROTATE = get_env("ENABLE_TIME_ROTATE", default=False, cast=bool)
# ------------------------------------------------------

# ------------------------------------------------------
FAB_ADD_SECURITY_PERMISSION_VIEW = get_env("FAB_ADD_SECURITY_PERMISSION_VIEW", default=False, cast=bool)
FAB_ADD_SECURITY_PERMISSION_VIEWS_VIEW = get_env("FAB_ADD_SECURITY_PERMISSION_VIEWS_VIEW", default=False, cast=bool)
FAB_ADD_SECURITY_VIEW_MENU_VIEW = get_env("FAB_ADD_SECURITY_VIEW_MENU_VIEW", default=False, cast=bool)
FAB_ADD_SECURITY_VIEWS = get_env("FAB_ADD_SECURITY_VIEWS", default=True, cast=bool)
FAB_API_SWAGGER_UI = get_env("FAB_API_SWAGGER_UI", default=True, cast=bool)
# ------------------------------------------------------

# ------------------------------------------------------
FEATURE_FLAGS = {
    "CLIENT_CACHE": get_env("FEATURE_FLAG_CLIENT_CACHE", default=False, cast=bool),
    "ENABLE_EXPLORE_JSON_CSRF_PROTECTION": get_env("FEATURE_FLAG_ENABLE_EXPLORE_JSON_CSRF_PROTECTION",
                                                   default=False,
                                                   cast=bool),
    "KV_STORE": get_env("FEATURE_FLAG_KV_STORE", default=False, cast=bool),
    "PRESTO_EXPAND_DATA": get_env("FEATURE_FLAG_PRESTO_EXPAND_DATA", default=False, cast=bool),
    "THUMBNAILS": get_env("FEATURE_FLAG_THUMBNAILS", default=False, cast=bool),
    "REDUCE_DASHBOARD_BOOTSTRAP_PAYLOAD": get_env("FEATURE_FLAG_REDUCE_DASHBOARD_BOOTSTRAP_PAYLOAD",
                                                  default=True,
                                                  cast=bool),
    "SHARE_QUERIES_VIA_KV_STORE": get_env("FEATURE_FLAG_SHARE_QUERIES_VIA_KV_STORE", default=False, cast=bool),
    "SIP_38_VIZ_REARCHITECTURE": get_env("FEATURE_FLAG_SIP_38_VIZ_REARCHITECTURE", default=False, cast=bool),
    "TAGGING_SYSTEM": get_env("FEATURE_FLAG_TAGGING_SYSTEM", default=False, cast=bool),
    "SQLLAB_BACKEND_PERSISTENCE": get_env("FEATURE_FLAG_SQLLAB_BACKEND_PERSISTENCE", default=False, cast=bool),
    "LIST_VIEWS_SIP34_FILTER_UI": get_env("FEATURE_FLAG_LIST_VIEWS_SIP34_FILTER_UI", default=False, cast=bool)
}
# ------------------------------------------------------

# ------------------------------------------------------
FILTER_SELECT_ROW_LIMIT = get_env("FILTER_SELECT_ROW_LIMIT", default=10000, cast=int)
# ------------------------------------------------------

# ------------------------------------------------------
FLASK_USE_RELOAD = get_env("FLASK_USE_RELOAD", default=True, cast=bool)
# ------------------------------------------------------

# ------------------------------------------------------
HIVE_POLL_INTERVAL = get_env("HIVE_POLL_INTERVAL", default=5, cast=int)
# ------------------------------------------------------

# ------------------------------------------------------
INTERVAL = get_env("INTERVAL", default=1, cast=int)
# ------------------------------------------------------

# ------------------------------------------------------
LOG_FORMAT = get_env("LOG_FORMAT", default="%(asctime)s:%(levelname)s:%(name)s:%(message)s")
LOG_LEVEL = get_env("LOG_LEVEL", default="DEBUG")
# ------------------------------------------------------

# ------------------------------------------------------
LOGO_TARGET_PATH = get_env("LOGO_TARGET_PATH")
# ------------------------------------------------------

# ------------------------------------------------------
MAX_TABLE_NAMES = get_env("MAX_TABLE_NAMES", default=3000, cast=int)
# ------------------------------------------------------

# ------------------------------------------------------
MAPBOX_API_KEY = get_env("MAPBOX_API_KEY", default="")
# ------------------------------------------------------

# ------------------------------------------------------
PERMISSION_INSTRUCTIONS_LINK = get_env("PERMISSION_INSTRUCTIONS_LINK", default="")
# ------------------------------------------------------

# ------------------------------------------------------
PREVENT_UNSAFE_DB_CONNECTIONS = get_env("PREVENT_UNSAFE_DB_CONNECTIONS", default=True, cast=bool)
# ------------------------------------------------------

# ------------------------------------------------------
PROXY_FIX_CONFIG = {
    "x_for": get_env("PROXY_FIX_CONFIG_X_FOR", default=1, cast=int),
    "x_proto": get_env("PROXY_FIX_CONFIG_X_PROTO", default=1, cast=int),
    "x_host": get_env("PROXY_FIX_CONFIG_X_HOST", default=1, cast=int),
    "x_prefix": get_env("PROXY_FIX_CONFIG_X_PREFIX", default=1, cast=int)
}
# ------------------------------------------------------

# ------------------------------------------------------
PUBLIC_ROLE_LIKE_GAMMA = get_env("PUBLIC_ROLE_LIKE_GAMMA", default=False, cast=bool)
# ------------------------------------------------------

# ------------------------------------------------------
RESULTS_BACKEND = RESULTS_BACKENDS.get(get_env("RESULTS_BACKEND_TYPE", default="null"), lambda: None)()
RESULTS_BACKEND_USE_MSGPACK = get_env("RESULTS_BACKEND_USE_MSGPACK", default=True, cast=bool)
# ------------------------------------------------------

# ------------------------------------------------------
ROLLOVER = get_env("ROLLOVER", default="midnight")
# ------------------------------------------------------

# ------------------------------------------------------
ROW_LIMIT = get_env("ROW_LIMIT", default=50000, cast=int)
# ------------------------------------------------------

# ------------------------------------------------------
SAMPLES_ROW_LIMIT = get_env("SAMPLES_ROW_LIMIT", default=1000, cast=int)
# ------------------------------------------------------

# ------------------------------------------------------
SCHEDULED_EMAIL_DEBUG_MODE = get_env("SCHEDULED_EMAIL_DEBUG_MODE", default=False, cast=bool)
# ------------------------------------------------------

# ------------------------------------------------------
SECRET_KEY = get_env("SECRET_KEY", default="\1\2thisismysecretkey\1\2\e\y\y\h")
# ------------------------------------------------------

# ------------------------------------------------------
SEND_FILE_MAX_AGE_DEFAULT = get_env("SEND_FILE_MAX_AGE_DEFAULT", default=31536000, cast=int)
# ------------------------------------------------------

# ------------------------------------------------------
SESSION_COOKIE_HTTPONLY = get_env("SESSION_COOKIE_HTTPONLY", default=True, cast=bool)
SESSION_COOKIE_SAMESITE = get_env("SESSION_COOKIE_SAMESITE", default="Lax")
SESSION_COOKIE_SECURE = get_env("SESSION_COOKIE_SECURE", default=False, cast=bool)
# ------------------------------------------------------

# ------------------------------------------------------
SHOW_STACKTRACE = get_env("SHOW_STACKTRACE", default=True, cast=bool)
# ------------------------------------------------------

# ------------------------------------------------------
SILENCE_FAB = get_env("SILENCE_FAB", default=True, cast=bool)
# ------------------------------------------------------

# ------------------------------------------------------
SIP_15_DEFAULT_TIME_RANGE_ENDPOINTS = get_env("SIP_15_DEFAULT_TIME_RANGE_ENDPOINTS",
                                              default=["unknown", "inclusive"],
                                              cast=list)
SIP_15_ENABLED = get_env("SIP_15_ENABLED", default=True, cast=bool)
SIP_15_GRACE_PERIOD_END = get_env("SIP_15_GRACE_PERIOD_END")
# ------------------------------------------------------

# ------------------------------------------------------
SMTP_HOST = get_env("SMTP_HOST", default="localhost")
SMTP_MAIL_FROM = get_env("SMTP_MAIL_FROM", default="superset@superset.org")
SMTP_PASSWORD = get_env("SMTP_PASSWORD", default="superset")
SMTP_PORT = get_env("SMTP_PORT", default=25, cast=int)
SMTP_STARTTLS = get_env("SMTP_STARTTLS", default=True, cast=bool)
SMTP_SSL = get_env("SMTP_SSL", default=False, cast=bool)
SMTP_USER = get_env("SMTP_USER", default="superset")
# ------------------------------------------------------

# ------------------------------------------------------
SSL_CERT_PATH = get_env("SSL_CERT_PATH")
# ------------------------------------------------------

# ------------------------------------------------------
STATS_LOGGER = STATS_LOGGERS.get(get_env("STATS_LOGGER_TYPE", default="dummy"), STATS_LOGGERS["dummy"])()
# ------------------------------------------------------

# ------------------------------------------------------
SUPERSET_DASHBOARD_POSITION_DATA_LIMIT = get_env("SUPERSET_DASHBOARD_POSITION_DATA_LIMIT", default=65535, cast=int)
SUPERSET_DASHBOARD_PERIODICAL_REFRESH_LIMIT = get_env("SUPERSET_DASHBOARD_PERIODICAL_REFRESH_LIMIT", default=0, cast=int)
SUPERSET_DASHBOARD_PERIODICAL_REFRESH_WARNING_MESSAGE = get_env("SUPERSET_DASHBOARD_PERIODICAL_REFRESH_WARNING_MESSAGE")
# ------------------------------------------------------

# ------------------------------------------------------
SUPERSET_LOG_VIEW = get_env("SUPERSET_LOG_VIEW", default=True, cast=bool)
# ------------------------------------------------------

# ------------------------------------------------------
SUPERSET_WEBSERVER_ADDRESS = get_env("SUPERSET_WEBSERVER_ADDRESS", default="0.0.0.0")
SUPERSET_WEBSERVER_PORT = get_env("SUPERSET_WEBSERVER_PORT", default=8088, cast=int)
SUPERSET_WEBSERVER_PROTOCOL = get_env("SUPERSET_WEBSERVER_PROTOCOL", default="http")
SUPERSET_WEBSERVER_TIMEOUT = get_env("SUPERSET_WEBSERVER_TIMEOUT", default=60, cast=int)
# ------------------------------------------------------

# ------------------------------------------------------
SQL_MAX_ROW = get_env("SQL_MAX_ROW", default=100000, cast=int)
# ------------------------------------------------------

# ------------------------------------------------------
SQLALCHEMY_TRACK_MODIFICATIONS = get_env("SQLALCHEMY_TRACK_MODIFICATIONS", default=False, cast=bool)
SQLALCHEMY_DATABASE_URI = get_db_or_broker_uri("METADATA_DB", METADATA_DB_PREFIXES, METADATA_DB_DEFAULT_PORTS)
SQLALCHEMY_EXAMPLES_URI = get_db_or_broker_uri("METADATA_DB", METADATA_DB_PREFIXES, METADATA_DB_DEFAULT_PORTS)
# ------------------------------------------------------

# ------------------------------------------------------
SQLLAB_ASYNC_TIME_LIMIT_SEC = get_env("SQLLAB_ASYNC_TIME_LIMIT_SEC", default=21600, cast=int)
SQLLAB_CTAS_NO_LIMIT = get_env("SQLLAB_CTAS_NO_LIMIT", default=False, cast=bool)
SQLLAB_SAVE_WARNING_MESSAGE = get_env("SQLLAB_SAVE_WARNING_MESSAGE")
SQLLAB_SCHEDULE_WARNING_MESSAGE = get_env("SQLLAB_SCHEDULE_WARNING_MESSAGE")
SQLLAB_TIMEOUT = get_env("SQLLAB_TIMEOUT", default=30, cast=int)
SQLLAB_VALIDATION_TIMEOUT = get_env("SQLLAB_VALIDATION_TIMEOUT", default=10, cast=int)
SQLLAB_QUERY_COST_ESTIMATE_TIMEOUT = get_env("SQLLAB_QUERY_COST_ESTIMATE_TIMEOUT", default=10, cast=int)
# ------------------------------------------------------

# ------------------------------------------------------
TABLE_NAMES_CACHE_CONFIG = get_cache_config("TABLE_NAMES_CACHE_CONFIG")
# ------------------------------------------------------

# ------------------------------------------------------
TALISMAN_ENABLED = get_env("TALISMAN_ENABLED", default=False, cast=bool)
TALISMAN_CONFIG = {
    "content_security_policy": get_env("TALISMAN_CONFIG_CONTENT_SECURITY_POLICY"),
    "force_https": get_env("TALISMAN_CONFIG_FORCE_HTTPS", default=True, cast=bool),
    "force_https_permanent": get_env("TALISMAN_CONFIG_FORCE_HTTPS_PERMANENT", default=False, cast=bool)
}
# ------------------------------------------------------

# ------------------------------------------------------
THUMBNAIL_CACHE_CONFIG = get_cache_config("THUMBNAIL_CACHE_CONFIG")
THUMBNAIL_SELENIUM_USER = get_env("THUMBNAIL_SELENIUM_USER", default="Admin")
# ------------------------------------------------------

# ------------------------------------------------------
TIME_ROTATE_LOG_LEVEL = get_env("TIME_ROTATE_LOG_LEVEL", default="DEBUG")
# ------------------------------------------------------

# ------------------------------------------------------
TROUBLESHOOTING_LINK = get_env("TROUBLESHOOTING_LINK", default="")
# ------------------------------------------------------

# ------------------------------------------------------
VIZ_TYPE_BLACKLIST = get_env("VIZ_TYPE_BLACKLIST", default=[], cast=list)
VIZ_ROW_LIMIT = get_env("VIZ_ROW_LIMIT", default=10000, cast=int)
# ------------------------------------------------------

# ------------------------------------------------------
WARNING_MSG = get_env("WARNING_MSG")
# ------------------------------------------------------

# ------------------------------------------------------
WEBDRIVER_BASEURL = get_env("WEBDRIVER_BASEURL", default="http://0.0.0.0:8080/")
WEBDRIVER_WINDOW = {
    "dashboard": (get_env("WEBDRIVER_WINDOW_DASHBOARD_WIDTH", default=1600, cast=int),
                  get_env("WEBDRIVER_WINDOW_DASHBOARD_HEIGHT", default=2000, cast=int)),
    "slice": (get_env("WEBDRIVER_WINDOW_SLICE_WIDTH", default=3000, cast=int),
              get_env("WEBDRIVER_WINDOW_SLICE_HEIGHT", default=1200, cast=int))
}
# ------------------------------------------------------


# ------------------------------------------------------
WTF_CSRF_ENABLED = get_env("WTF_CSRF_ENABLED", default=True, cast=bool)
WTF_CSRF_EXEMPT_LIST = get_env("WTF_CSRF_EXEMPT_LIST", default=["superset.views.core.log"], cast=list)
WTF_CSRF_TIME_LIMIT = get_env("WTF_CSRF_TIME_LIMIT", default=604800, cast=int)
# ------------------------------------------------------

# ------------------------------------------------------
QUERY_SEARCH_LIMIT = get_env("QUERY_SEARCH_LIMIT", default=1000, cast=int)
# ------------------------------------------------------
