# TODO Write environment variables list to Markdown
# TODO S3 result backend will be added
from dateutil import tz
from flask_appbuilder.security.manager import AUTH_DB, AUTH_LDAP, AUTH_OID, AUTH_REMOTE_USER
from os import environ
from werkzeug.contrib.cache import SimpleCache, MemcachedCache, RedisCache, FileSystemCache

DRUID_TIMEZONES = {"utc": tz.tzutc(), "local": tz.tzlocal()}
AUTH_TYPES = {"oid": AUTH_OID, "db": AUTH_DB, "ldap": AUTH_LDAP, "remote_user": AUTH_REMOTE_USER}
METADATA_DB_PREFIXES = {"postgresql": "postgresql+psycopg2", "mysql": "mysql", "sqllite": "sqllite"}
METADATA_DB_DEFAULT_PORTS = {"postgresql": 5432, "mysql": 3306}
BROKER_PREFIXES = {"redis": "redis", "rabbitmq": "pyamqp"}
BROKER_DEFAULT_PORTS = {"redis": 6379, "rabbitmq": 5672}
RESULTS_BACKEND_PREFIXES = {"redis": "redis", "memcached": "cache+memcached"}


def get_env(env_var, default_value=None, var_type: type = str):
    value = environ[env_var]

    if var_type == int:
        return int(value) if value != "NULL" else default_value
    elif var_type == float:
        return float(value) if value != "NULL" else default_value
    elif var_type == bool:
        return str(value).lower() == "true" if value != "NULL" else default_value
    elif var_type == list:
        return value.split(",") if value != "NULL" else default_value
    else:
        return value if value != "NULL" else default_value


def get_cache_config(env_var_prefix):
    def set_config(config_dict, config_key, var_type: type = str):
        value = get_env("{}_{}".format(env_var_prefix, config_key), var_type=var_type)

        if value:
            config_dict[config_key] = value

    cache_config = {}

    set_config(cache_config, "CACHE_TYPE")
    set_config(cache_config, "CACHE_NO_NULL_WARNING", var_type=bool)
    set_config(cache_config, "CACHE_DEFAULT_TIMEOUT", var_type=int)
    set_config(cache_config, "CACHE_THRESHOLD", var_type=int)
    set_config(cache_config, "CACHE_KEY_PREFIX")
    set_config(cache_config, "CACHE_MEMCACHED_SERVERS")
    set_config(cache_config, "CACHE_MEMCACHED_USERNAME")
    set_config(cache_config, "CACHE_MEMCACHED_PASSWORD")
    set_config(cache_config, "CACHE_REDIS_HOST")
    set_config(cache_config, "CACHE_REDIS_PORT", var_type=int)
    set_config(cache_config, "CACHE_REDIS_PASSWORD")
    set_config(cache_config, "CACHE_REDIS_DB", var_type=int)
    set_config(cache_config, "CACHE_DIR")

    if cache_config["CACHE_TYPE"] == "redis":
        redis_password = cache_config.get("CACHE_REDIS_PASSWORD", None)
        cache_config["CACHE_REDIS_URL"] = "redis://{password}{host}:{port}/{db}".format(
            password="{}@".format(redis_password) if redis_password else "",
            host=cache_config.get("CACHE_REDIS_HOST", ""),
            port=cache_config.get("CACHE_REDIS_PORT", ""),
            db=cache_config.get("CACHE_REDIS_DB", "")
        )

    return cache_config


def get_results_backend():
    backend_type = get_env("RESULTS_BACKEND_TYPE")
    default_timeout = get_env("RESULTS_BACKEND_DEFAULT_TIMEOUT", var_type=float)
    threshold = get_env("RESULTS_BACKEND_THRESHOLD", var_type=int)

    if backend_type == "simple":
        return SimpleCache(threshold=threshold, default_timeout=default_timeout)
    elif backend_type == "redis":
        return RedisCache(host=get_env("RESULTS_BACKEND_REDIS_HOST"),
                          port=get_env("RESULTS_BACKEND_REDIS_PORT", var_type=int),
                          password=get_env("RESULTS_BACKEND_REDIS_PASSWORD"),
                          key_prefix=get_env("RESULTS_BACKEND_REDIS_KEY_PREFIX"),
                          db=get_env("RESULTS_BACKEND_REDIS_DB", var_type=int),
                          default_timeout=default_timeout)
    elif backend_type == "memcached":
        return MemcachedCache(servers=get_env("RESULTS_BACKEND_MEMCACHED_SERVERS", var_type=list),
                              default_timeout=default_timeout,
                              key_prefix=get_env("RESULTS_BACKEND_MEMCACHED_KEY_PREFIX"))
    elif backend_type == "filesystem":
        return FileSystemCache(cache_dir=get_env("RESULTS_BACKEND_FILESYSTEM_CACHE_DIR"),
                               threshold=threshold,
                               default_timeout=default_timeout,
                               mode=get_env("RESULTS_BACKEND_FILESYSTEM_MODE", var_type=int))
    else:
        return None


def get_results_backend_uri():
    backend_type = get_env("RESULTS_BACKEND_TYPE")

    if backend_type not in RESULTS_BACKEND_PREFIXES.keys():
        raise Exception("Wrong result backend type \"{}\"".format(backend_type))
    else:
        if backend_type == "redis":
            host = get_env("RESULTS_BACKEND_REDIS_HOST")
            port = get_env("RESULTS_BACKEND_REDIS_PORT")
            password = get_env("RESULTS_BACKEND_REDIS_PASSWORD")
            db = get_env("RESULTS_BACKEND_REDIS_DB")

            return "{prefix}://{password}{host}:{port}/{db}".format(prefix=RESULTS_BACKEND_PREFIXES[backend_type],
                                                                    password="{}@".format(password) if password else "",
                                                                    host=host,
                                                                    port=port,
                                                                    db=db)
        elif backend_type == "memcached":
            return "{prefix}://{servers}/".format(prefix=RESULTS_BACKEND_PREFIXES[backend_type],
                                                  servers=";".join(get_env("RESULTS_BACKEND_MEMCACHED_SERVERS", var_type=list)))


def get_db_or_broker_uri(env_var_prefix, default_prefixes, default_ports):
    type = get_env("{}_TYPE".format(env_var_prefix))
    username = get_env("{}_USERNAME".format(env_var_prefix))
    password = get_env("{}_PASSWORD".format(env_var_prefix))
    host = get_env("{}_HOST".format(env_var_prefix))
    port = get_env("{}_PORT".format(env_var_prefix))

    if not port:
        port = default_ports.get(type, None)

    db = get_env("{}_DATABASE".format(env_var_prefix))

    if type not in default_prefixes.keys():
        raise Exception("Wrong type \"{}\"".format(type))
    else:
        return "{prefix}://{username}{password}{host}:{port}/{db}".format(
            prefix=default_prefixes[type],
            username="{}{}".format(username, ":" if password else "@") if username else "",
            password="{}@".format(password) if password else "",
            host=host,
            port=port,
            db=db
        )


# ------------------------------------------------------
APP_ICON = get_env("APP_ICON")
APP_ICON_WIDTH = get_env("APP_ICON_WIDTH", var_type=int)
APP_NAME = get_env("APP_NAME")
# ------------------------------------------------------

# ------------------------------------------------------
AUTH_TYPE = AUTH_TYPES.get(get_env("AUTH_TYPE"))
# ------------------------------------------------------

# ------------------------------------------------------
BABEL_DEFAULT_LOCALE = get_env("BABEL_DEFAULT_LOCALE")
BABEL_DEFAULT_FOLDER = get_env("BABEL_DEFAULT_FOLDER")
# ------------------------------------------------------

# ------------------------------------------------------
BACKUP_COUNT = get_env("BACKUP_COUNT", var_type=int)
# ------------------------------------------------------

# ------------------------------------------------------
BUG_REPORT_URL = get_env("BUG_REPORT_URL")
# ------------------------------------------------------

# ------------------------------------------------------
CACHE_CONFIG = get_cache_config("CACHE_CONFIG")
CACHE_DEFAULT_TIMEOUT = get_env("CACHE_DEFAULT_TIMEOUT", var_type=int)
# ------------------------------------------------------


# ------------------------------------------------------
class CeleryConfig:
    BROKER_URL = get_db_or_broker_uri("CELERY_BROKER", BROKER_PREFIXES, BROKER_DEFAULT_PORTS)
    CELERY_IMPORTS = ("superset.sql_lab", "superset.tasks")
    CELERY_RESULT_BACKEND = get_results_backend_uri()
    CELERYD_LOG_LEVEL = get_env("CELERYD_LOG_LEVEL")
    CELERY_ACKS_LATE = get_env("CELERY_ACKS_LATE", var_type=bool)
    CELERY_ANNOTATIONS = {
        "sql_lab.get_sql_results": {
            "rate_limit": "{}/s".format(get_env("CELERY_SQLLAB_GET_RESULTS_RATE_LIMIT_IN_SECS", var_type=int))
        },
        "email_reports.send": {
            "rate_limit": "{}/s".format(get_env("CELERY_EMAIL_REPORTS_SEND_RATE_LIMIT_IN_SECS", var_type=int)),
            "time_limit": get_env("CELERY_EMAIL_REPORTS_TIME_LIMIT", var_type=int),
            "soft_time_limit": get_env("CELERY_EMAIL_REPORTS_SOFT_TIME_LIMIT", var_type=int),
            "ignore_result": get_env("CELERY_EMAIL_REPORTS_IGNORE_RESULT", var_type=bool)
        }
    }


CELERY_CONFIG = CeleryConfig
# ------------------------------------------------------

# ------------------------------------------------------
CORS_OPTIONS = {
    "origins": get_env("CORS_OPTIONS_ORIGINS", var_type=list),
    "methods": get_env("CORS_OPTIONS_METHODS", var_type=list),
    "expose_headers": get_env("CORS_OPTIONS_EXPOSE_HEADERS", var_type=list),
    "allow_headers": get_env("CORS_OPTIONS_ALLOW_HEADERS", var_type=list),
    "send_wildcard": get_env("CORS_OPTIONS_SEND_WILDCARD", var_type=bool),
    "vary_header": get_env("CORS_OPTIONS_VARY_HEADER", var_type=bool)
}
# ------------------------------------------------------

# ------------------------------------------------------
CSV_TO_HIVE_UPLOAD_S3_BUCKET = get_env("CSV_TO_HIVE_UPLOAD_S3_BUCKET")
CSV_TO_HIVE_UPLOAD_DIRECTORY = get_env("CSV_TO_HIVE_UPLOAD_DIRECTORY")
# ------------------------------------------------------

# ------------------------------------------------------
DEBUG = get_env("DEBUG", bool)
# ------------------------------------------------------

# ------------------------------------------------------
DEFAULT_RELATIVE_START_TIME = get_env("DEFAULT_RELATIVE_START_TIME")
DEFAULT_RELATIVE_END_TIME = get_env("DEFAULT_RELATIVE_END_TIME")
DEFAULT_SQLLAB_LIMIT = get_env("DEFAULT_SQLLAB_LIMIT", var_type=int)
# ------------------------------------------------------

# ------------------------------------------------------
DISPLAY_MAX_ROW = get_env("DISPLAY_MAX_ROW", var_type=int)
# ------------------------------------------------------

# ------------------------------------------------------
DOCUMENTATION_URL = get_env("DOCUMENTATION_URL")
DOCUMENTATION_TEXT = get_env("DOCUMENTATION_TEXT")
DOCUMENTATION_ICON = get_env("DOCUMENTATION_ICON")
# ------------------------------------------------------

# ------------------------------------------------------
DRUID_ANALYSIS_TYPES = get_env("DRUID_ANALYSIS_TYPES", var_type=list)
DRUID_DATA_SOURCE_BLACKLIST = get_env("DRUID_DATA_SOURCE_BLACKLIST", default_value=[], var_type=list)
DRUID_IS_ACTIVE = get_env("DRUID_IS_ACTIVE", var_type=bool)
DRUID_METADATA_LINKS_ENABLED = get_env("DRUID_METADATA_LINKS_ENABLED", var_type=bool)
DRUID_TZ = DRUID_TIMEZONES.get(get_env("DRUID_TZ"), tz.gettz(get_env("DRUID_TZ")))
# ------------------------------------------------------

# ------------------------------------------------------
EMAIL_ASYNC_TIME_LIMIT_SEC = get_env("EMAIL_ASYNC_TIME_LIMIT_SEC", var_type=int)
EMAIL_NOTIFICATIONS = get_env("EMAIL_NOTIFICATIONS", var_type=bool)
EMAIL_REPORT_BCC_ADDRESS = get_env("EMAIL_REPORT_BCC_ADDRESS")
EMAIL_REPORT_FROM_ADDRESS = get_env("EMAIL_REPORT_FROM_ADDRESS")
EMAIL_REPORTS_CRON_RESOLUTION = get_env("EMAIL_REPORTS_CRON_RESOLUTION", var_type=int)
EMAIL_REPORTS_USER = get_env("EMAIL_REPORTS_USER")
EMAIL_REPORTS_SUBJECT_PREFIX = get_env("EMAIL_REPORTS_SUBJECT_PREFIX")
EMAIL_REPORTS_WEBDRIVER = get_env("EMAIL_REPORTS_WEBDRIVER")
# ------------------------------------------------------

# ------------------------------------------------------
ENABLE_ACCESS_REQUEST = get_env("ENABLE_ACCESS_REQUEST", var_type=bool)
# ------------------------------------------------------

# ------------------------------------------------------
ENABLE_CHUNK_ENCODING = get_env("ENABLE_CHUNK_ENCODING", var_type=bool)
# ------------------------------------------------------

# ------------------------------------------------------
ENABLE_CORS = get_env("ENABLE_CORS", var_type=bool)
# ------------------------------------------------------

# ------------------------------------------------------
ENABLE_FLASK_COMPRESS = get_env("ENABLE_FLASK_COMPRESS", var_type=bool)
# ------------------------------------------------------

# ------------------------------------------------------
ENABLE_JAVASCRIPT_CONTROLS = get_env("ENABLE_JAVASCRIPT_CONTROLS", var_type=bool)
# ------------------------------------------------------

# ------------------------------------------------------
ENABLE_PROXY_FIX = get_env("ENABLE_PROXY_FIX", var_type=bool)
# ------------------------------------------------------

# ------------------------------------------------------
ENABLE_REACT_CRUD_VIEWS = get_env("ENABLE_REACT_CRUD_VIEWS", var_type=bool)
# ------------------------------------------------------

# ------------------------------------------------------
ENABLE_SCHEDULED_EMAIL_REPORTS = get_env("ENABLE_SCHEDULED_EMAIL_REPORTS", var_type=bool)
# ------------------------------------------------------

# ------------------------------------------------------
ENABLE_TIME_ROTATE = get_env("ENABLE_TIME_ROTATE", var_type=bool)
# ------------------------------------------------------

# ------------------------------------------------------
FAB_ADD_SECURITY_PERMISSION_VIEW = get_env("FAB_ADD_SECURITY_PERMISSION_VIEW", var_type=bool)
FAB_ADD_SECURITY_PERMISSION_VIEWS_VIEW = get_env("FAB_ADD_SECURITY_PERMISSION_VIEWS_VIEW", var_type=bool)
FAB_ADD_SECURITY_VIEW_MENU_VIEW = get_env("FAB_ADD_SECURITY_VIEW_MENU_VIEW", var_type=bool)
FAB_ADD_SECURITY_VIEWS = get_env("FAB_ADD_SECURITY_VIEWS", var_type=bool)
FAB_API_SWAGGER_UI = get_env("FAB_API_SWAGGER_UI", var_type=bool)
# ------------------------------------------------------

# ------------------------------------------------------
FEATURE_FLAGS = {
    "CLIENT_CACHE": get_env("FEATURE_FLAG_CLIENT_CACHE", var_type=bool),
    "ENABLE_EXPLORE_JSON_CSRF_PROTECTION": get_env("FEATURE_FLAG_ENABLE_EXPLORE_JSON_CSRF_PROTECTION", var_type=bool),
    "KV_STORE": get_env("FEATURE_FLAG_KV_STORE", var_type=bool),
    "PRESTO_EXPAND_DATA": get_env("FEATURE_FLAG_PRESTO_EXPAND_DATA", var_type=bool),
    "THUMBNAILS": get_env("FEATURE_FLAG_THUMBNAILS", var_type=bool),
    "REDUCE_DASHBOARD_BOOTSTRAP_PAYLOAD": get_env("FEATURE_FLAG_REDUCE_DASHBOARD_BOOTSTRAP_PAYLOAD", var_type=bool),
    "SHARE_QUERIES_VIA_KV_STORE": get_env("FEATURE_FLAG_SHARE_QUERIES_VIA_KV_STORE", var_type=bool),
    "SIP_38_VIZ_REARCHITECTURE": get_env("FEATURE_FLAG_SIP_38_VIZ_REARCHITECTURE", var_type=bool),
    "TAGGING_SYSTEM": get_env("FEATURE_FLAG_TAGGING_SYSTEM", var_type=bool),
    "SQLLAB_BACKEND_PERSISTENCE": get_env("FEATURE_FLAG_SQLLAB_BACKEND_PERSISTENCE", var_type=bool),
    "LIST_VIEWS_NEW_UI": get_env("FEATURE_FLAG_LIST_VIEWS_NEW_UI", var_type=bool)
}
# ------------------------------------------------------

# ------------------------------------------------------
FILTER_SELECT_ROW_LIMIT = get_env("FILTER_SELECT_ROW_LIMIT", var_type=int)
# ------------------------------------------------------

# ------------------------------------------------------
FLASK_USE_RELOAD = get_env("FLASK_USE_RELOAD", var_type=bool)
# ------------------------------------------------------

# ------------------------------------------------------
HIVE_POLL_INTERVAL = get_env("HIVE_POLL_INTERVAL", var_type=int)
# ------------------------------------------------------

# ------------------------------------------------------
INTERVAL = get_env("INTERVAL", var_type=int)
# ------------------------------------------------------

# ------------------------------------------------------
LOG_FORMAT = get_env("LOG_FORMAT")
LOG_LEVEL = get_env("LOG_LEVEL")
# ------------------------------------------------------

# ------------------------------------------------------
LOGO_TARGET_PATH = get_env("LOGO_TARGET_PATH", default_value=None)
# ------------------------------------------------------

# ------------------------------------------------------
MAX_TABLE_NAMES = get_env("MAX_TABLE_NAMES", var_type=int)
# ------------------------------------------------------

# ------------------------------------------------------
MAPBOX_API_KEY = get_env("MAPBOX_API_KEY")
# ------------------------------------------------------

# ------------------------------------------------------
PERMISSION_INSTRUCTIONS_LINK = get_env("PERMISSION_INSTRUCTIONS_LINK")
# ------------------------------------------------------

# ------------------------------------------------------
PREVENT_UNSAFE_DB_CONNECTIONS = get_env("PREVENT_UNSAFE_DB_CONNECTIONS", var_type=bool)
# ------------------------------------------------------

# ------------------------------------------------------
PROXY_FIX_CONFIG = {
    "x_for": get_env("PROXY_FIX_CONFIG_X_FOR", var_type=int),
    "x_proto": get_env("PROXY_FIX_CONFIG_X_PROTO", var_type=int),
    "x_host": get_env("PROXY_FIX_CONFIG_X_HOST", var_type=int),
    "x_prefix": get_env("PROXY_FIX_CONFIG_X_PREFIX", var_type=int)
}
# ------------------------------------------------------

# ------------------------------------------------------
PUBLIC_ROLE_LIKE_GAMMA = get_env("PUBLIC_ROLE_LIKE_GAMMA", var_type=bool)
# ------------------------------------------------------

# ------------------------------------------------------
RESULTS_BACKEND = get_results_backend()
# ------------------------------------------------------

# ------------------------------------------------------
ROLLOVER = get_env("ROLLOVER")
# ------------------------------------------------------

# ------------------------------------------------------
ROW_LIMIT = get_env("ROW_LIMIT", var_type=int)
# ------------------------------------------------------

# ------------------------------------------------------
SCHEDULED_EMAIL_DEBUG_MODE = get_env("SCHEDULED_EMAIL_DEBUG_MODE", var_type=bool)
# ------------------------------------------------------

# ------------------------------------------------------
SECRET_KEY = get_env("SECRET_KEY")
# ------------------------------------------------------

# ------------------------------------------------------
SEND_FILE_MAX_AGE_DEFAULT = get_env("SEND_FILE_MAX_AGE_DEFAULT", var_type=int)
# ------------------------------------------------------

# ------------------------------------------------------
SESSION_COOKIE_HTTPONLY = get_env("SESSION_COOKIE_HTTPONLY", var_type=bool)
SESSION_COOKIE_SAMESITE = get_env("SESSION_COOKIE_SAMESITE")
SESSION_COOKIE_SECURE = get_env("SESSION_COOKIE_SECURE", var_type=bool)
# ------------------------------------------------------

# ------------------------------------------------------
SHOW_STACKTRACE = get_env("SHOW_STACKTRACE", var_type=bool)
# ------------------------------------------------------

# ------------------------------------------------------
SILENCE_FAB = get_env("SILENCE_FAB", var_type=bool)
# ------------------------------------------------------

# ------------------------------------------------------
SIP_15_DEFAULT_TIME_RANGE_ENDPOINTS = get_env("SIP_15_DEFAULT_TIME_RANGE_ENDPOINTS", var_type=list)
SIP_15_ENABLED = get_env("SIP_15_ENABLED", var_type=bool)
SIP_15_GRACE_PERIOD_END = get_env("SIP_15_GRACE_PERIOD_END")
# ------------------------------------------------------

# ------------------------------------------------------
SMTP_HOST = get_env("SMTP_HOST")
SMTP_MAIL_FROM = get_env("SMTP_MAIL_FROM")
SMTP_PASSWORD = get_env("SMTP_PASSWORD")
SMTP_PORT = get_env("SMTP_PORT", var_type=int)
SMTP_STARTTLS = get_env("SMTP_STARTTLS", var_type=bool)
SMTP_SSL = get_env("SMTP_SSL", var_type=bool)
SMTP_USER = get_env("SMTP_USER")
# ------------------------------------------------------

# ------------------------------------------------------
SSL_CERT_PATH = get_env("SSL_CERT_PATH")
# ------------------------------------------------------

# ------------------------------------------------------
SUPERSET_DASHBOARD_POSITION_DATA_LIMIT = get_env("SUPERSET_DASHBOARD_POSITION_DATA_LIMIT", var_type=int)
# ------------------------------------------------------

# ------------------------------------------------------
SUPERSET_LOG_VIEW = get_env("SUPERSET_LOG_VIEW", var_type=bool)
# ------------------------------------------------------

# ------------------------------------------------------
SUPERSET_WEBSERVER_ADDRESS = get_env("SUPERSET_WEBSERVER_ADDRESS")
SUPERSET_WEBSERVER_PORT = get_env("SUPERSET_WEBSERVER_PORT", var_type=int)
SUPERSET_WEBSERVER_PROTOCOL = get_env("SUPERSET_WEBSERVER_PROTOCOL")
SUPERSET_WEBSERVER_TIMEOUT = get_env("SUPERSET_WEBSERVER_TIMEOUT", var_type=int)
# ------------------------------------------------------

# ------------------------------------------------------
SQL_MAX_ROW = get_env("SQL_MAX_ROW", var_type=int)
# ------------------------------------------------------

# ------------------------------------------------------
SQLALCHEMY_TRACK_MODIFICATIONS = get_env("SQLALCHEMY_TRACK_MODIFICATIONS", var_type=bool)
SQLALCHEMY_DATABASE_URI = get_db_or_broker_uri("METADATA_DB", METADATA_DB_PREFIXES, METADATA_DB_DEFAULT_PORTS)
SQLALCHEMY_EXAMPLES_URI = get_db_or_broker_uri("METADATA_DB", METADATA_DB_PREFIXES, METADATA_DB_DEFAULT_PORTS)
# ------------------------------------------------------

# ------------------------------------------------------
SQLLAB_ASYNC_TIME_LIMIT_SEC = get_env("SQLLAB_ASYNC_TIME_LIMIT_SEC", var_type=int)
SQLLAB_CTAS_NO_LIMIT = get_env("SQLLAB_CTAS_NO_LIMIT", var_type=bool)
SQLLAB_SAVE_WARNING_MESSAGE = get_env("SQLLAB_SAVE_WARNING_MESSAGE")
SQLLAB_SCHEDULE_WARNING_MESSAGE = get_env("SQLLAB_SCHEDULE_WARNING_MESSAGE")
SQLLAB_TIMEOUT = get_env("SQLLAB_TIMEOUT", var_type=int)
SQLLAB_VALIDATION_TIMEOUT = get_env("SQLLAB_VALIDATION_TIMEOUT", var_type=int)
SQLLAB_QUERY_COST_ESTIMATE_TIMEOUT = get_env("SQLLAB_QUERY_COST_ESTIMATE_TIMEOUT", var_type=int)
# ------------------------------------------------------

# ------------------------------------------------------
TABLE_NAMES_CACHE_CONFIG = get_cache_config("TABLE_NAMES_CACHE_CONFIG")
# ------------------------------------------------------

# ------------------------------------------------------
TALISMAN_ENABLED = get_env("TALISMAN_ENABLED", var_type=bool)
TALISMAN_CONFIG = {
    "content_security_policy": get_env("TALISMAN_CONFIG_CONTENT_SECURITY_POLICY"),
    "force_https": get_env("TALISMAN_CONFIG_FORCE_HTTPS", var_type=bool),
    "force_https_permanent": get_env("TALISMAN_CONFIG_FORCE_HTTPS_PERMANENT", var_type=bool)
}
# ------------------------------------------------------

# ------------------------------------------------------
THUMBNAIL_CACHE_CONFIG = get_cache_config("THUMBNAIL_CACHE_CONFIG")
THUMBNAIL_SELENIUM_USER = get_env("THUMBNAIL_SELENIUM_USER")
# ------------------------------------------------------

# ------------------------------------------------------
TIME_ROTATE_LOG_LEVEL = get_env("TIME_ROTATE_LOG_LEVEL")
# ------------------------------------------------------

# ------------------------------------------------------
TROUBLESHOOTING_LINK = get_env("TROUBLESHOOTING_LINK")
# ------------------------------------------------------

# ------------------------------------------------------
VIZ_TYPE_BLACKLIST = get_env("VIZ_TYPE_BLACKLIST", default_value=[], var_type=list)
VIZ_ROW_LIMIT = get_env("VIZ_ROW_LIMIT", var_type=int)
# ------------------------------------------------------

# ------------------------------------------------------
WARNING_MSG = get_env("WARNING_MSG")
# ------------------------------------------------------

# ------------------------------------------------------
WEBDRIVER_BASEURL = get_env("WEBDRIVER_BASEURL")
WEBDRIVER_WINDOW = {
    "dashboard": (
        get_env("WEBDRIVER_WINDOW_DASHBOARD_WIDTH", var_type=int),
        get_env("WEBDRIVER_WINDOW_DASHBOARD_HEIGHT", var_type=int)
    ),
    "slice": (
        get_env("WEBDRIVER_WINDOW_SLICE_WIDTH", var_type=int),
        get_env("WEBDRIVER_WINDOW_SLICE_HEIGHT", var_type=int)
    )
}
# ------------------------------------------------------


# ------------------------------------------------------
WTF_CSRF_ENABLED = get_env("WTF_CSRF_ENABLED", var_type=bool)
WTF_CSRF_EXEMPT_LIST = get_env("WTF_CSRF_EXEMPT_LIST", var_type=list)
WTF_CSRF_TIME_LIMIT = get_env("WTF_CSRF_TIME_LIMIT", var_type=int)
# ------------------------------------------------------

# ------------------------------------------------------
QUERY_SEARCH_LIMIT = get_env("QUERY_SEARCH_LIMIT", var_type=int)
# ------------------------------------------------------
