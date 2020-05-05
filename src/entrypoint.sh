#!/bin/bash
# Written by Mutlu Polatcan
# 05.05.2020
# ---------------------------------------------
declare -A __SERVICE_PORTS__
declare -A __SUPERSET_DAEMONS__

__SERVICE_PORTS__[postgresql]="5432"
__SERVICE_PORTS__[mysql]="3306"
__SERVICE_PORTS__[redis]="6379"
__SERVICE_PORTS__[rabbitmq]="5672"

__SUPERSET_DAEMONS__[init]=init_superset
__SUPERSET_DAEMONS__[webserver]=run_superset_webserver
__SUPERSET_DAEMONS__[worker]=run_celery_worker
__SUPERSET_DAEMONS__[flower]=run_celery_flower

SUPERSET_COMPONENT_METADATA_DATABASE="metadata_database"
SUPERSET_COMPONENT_BROKER="broker"
SUPERSET_COMPONENT_RESULTS_BACKEND="results_backend"
SUPERSET_COMPONENT_CACHE="cache"
SUPERSET_COMPONENT_TABLE_NAMES_CACHE="table_names_cache"
SUPERSET_COMPONENT_THUMBNAIL_CACHE="thumbnail_cache"
SUPERSET_COMPONENT_STATS_LOGGER_STATSD="stats_logger_statsd"

# $1: message
function __log__() {
  echo "[$(date '+%d/%m/%Y %H:%M:%S')] -> $1"
}

# $1: Running command
# $2: Start message
# $3: Max retry times reached message
# $4: Retry message
# $5: Success message
function __retry_loop__() {
  __log__ "$2"
  counter=0
  $1

  until [[ $? -eq 0 ]]; do
    (( counter = counter + 1 ))

    if [[ ${SUPERSET_MAX_RETRY_TIMES:=-1} -ne -1 && $counter -ge ${SUPERSET_MAX_RETRY_TIMES:=-1} ]]; then
      __log__ $3
      __log__ "Max retry times \"${SUPERSET_MAX_RETRY_TIMES:=-1}\" reached. Exiting now..."
      exit 1
    fi

    __log__ "$4. Retrying after ${SUPERSET_RETRY_INTERVAL_IN_SECS:=2} seconds... (times: $counter)."
    sleep ${SUPERSET_RETRY_INTERVAL_IN_SECS:=2}
    $1
  done

  __log__ "$5"
}

# $1: Component name
# $2: Component type
# $3: Component hostname
# $4: Component port
function __health_checker__() {
  if [[ "$3" == "" ]]; then
    __log__ "Superset $1 host is not defined. Exiting ✘..."
    exit 1
  else
    __log__ "Superset $1 host is $3. OK ✔"
  fi

  __retry_loop__ "nc -z $3 $4" \
                 "Superset $1 healtcheck started ($1_type: \"$2\", $1_host: \"$3\", $1_port: \"$4\")..." \
                 "Superset $1 healthcheck failed ($1_type: \"$2\", $1_host: \"$3\", $1_port: \"$4\")..." \
                 "Waiting $1 is ready ($1_type: \"$2\", $1_host: \"$3\", $1_port: \"$4\")" \
                 "Superset $1 is ready ($1_type: \"$2\", $1_host: \"$3\", $1_port: \"$4\") ✔"
}

# $1: Component name
# $2: Component type
# $3: Memcached servers
function __memcached_servers_healthcheck__() {
  IFS="," read -r -a MEMCACHED_SERVERS <<< "$3"

  for server in ${MEMCACHED_SERVERS[@]}; do
    IFS=":" read -r -a SERVER_INFO <<< $server

    __health_checker__ "$1" "$2" ${SERVER_INFO[0]} ${SERVER_INFO[1]}
  done
}

# $1: Component name
# $2: Prefix
function __cache_or_results_backend_healthcheck__() {
  type=$2_TYPE
  redis_host=$2_REDIS_HOST
  redis_port=$2_REDIS_PORT
  memcached_servers=$2_MEMCACHED_SERVERS

  if [[ "${!type:=null}" == "redis" ]]; then
    __health_checker__ "$1" "${!type}" "${!redis_host}" "${!redis_port:=${__SERVICE_PORTS__[redis]}}"
  elif [[ "${!type:=null}" == "memcached" ]]; then
    __memcached_servers_healthcheck__ "$1" "${!type}" "${!memcached_servers}"
  fi
}


function run_worker_healthchecks() {
  # Celery broker health check
  __health_checker__ "${SUPERSET_COMPONENT_BROKER}" \
                     "${CELERY_BROKER_TYPE:=redis}" \
                     "${CELERY_BROKER_HOST}" \
                     "${CELERY_BROKER_PORT:=${__SERVICE_PORTS__[${CELERY_BROKER_TYPE:=redis}]}}"

  # Result backend health check
  __cache_or_results_backend_healthcheck__ "${SUPERSET_COMPONENT_RESULTS_BACKEND}" "RESULTS_BACKEND"
}

function run_common_healthchecks() {
  # Metadata database health check
  __health_checker__ "${SUPERSET_COMPONENT_METADATA_DATABASE}" \
                     "${METADATA_DB_TYPE:=postgresql}" \
                     "${METADATA_DB_HOST}" \
                     "${METADATA_DB_PORT:=${__SERVICE_PORTS__[${METADATA_DB_TYPE:=postgresql}]}}"

  # Main cache health check
  __cache_or_results_backend_healthcheck__ "${SUPERSET_COMPONENT_CACHE}" "CACHE_CONFIG_CACHE"

  # Table names cache health check
  __cache_or_results_backend_healthcheck__ "${SUPERSET_COMPONENT_TABLE_NAMES_CACHE}" "TABLE_NAMES_CACHE_CONFIG_CACHE"

  # Thumbnail cache health check
  __cache_or_results_backend_healthcheck__ "${SUPERSET_COMPONENT_THUMBNAIL_CACHE}" "THUMBNAIL_CACHE_CONFIG_CACHE"

  # Statsd server health check
  if [[ "${STATS_LOGGER_TYPE:=dummy}" == "statsd" ]]; then
    __health_checker__ "${SUPERSET_COMPONENT_STATS_LOGGER_STATSD}" \
                       "${STATS_LOGGER_TYPE}" \
                       "${STATSD_STATS_LOGGER_HOST}" \
                       "${STATSD_STATS_LOGGER_PORT}"
  fi
}

function init_superset() {
  __log__ "Upgrading metadata database..."

  superset db upgrade

  export FLASK_APP=superset

  __log__ "Creating admin user..."
  superset fab create-admin --username ${ADMIN_USERNAME:=admin} \
                            --firstname ${ADMIN_FIRSTNAME:=Admin} \
                            --lastname ${ADMIN_LASTNAME:=User} \
                            --email ${ADMIN_EMAIL:=admin@superset.apache.org} \
                            --password ${ADMIN_PASSWORD:=admin}

  if [[ "${LOAD_EXAMPLES:=false}" == "true" ]]; then
    __log__ "Loading Superset examples..."
    superset load_examples
  fi

  __log__ "Initializing Superset..."
  superset init
}

function run_superset_webserver() {
  __log__ "Running Superset webserver..."

  superset run --host 0.0.0.0 --port 8088 --with-threads --reload --debugger
}

function run_celery_worker() {
  __retry_loop__ "celery worker --app=superset.tasks.celery_app:app --pool=${CELERY_BROKER_POOL_TYPE:=prefork} -O fair -c ${CELERY_BROKER_CONCURRENCY:=4} -E" \
                 "Running Celery worker..." \
                 "Celery worker cannot be started!" \
                 "Waiting Celery worker to start..." \
                 "Celery worker successfully started!"
}

function run_celery_flower() {
  __log__ "Running Celery Flower..."

  celery flower --app=superset.tasks.celery_app:app
}

function main() {
  run_common_healthchecks

  if [[ "${SUPERSET_DAEMONS}" != "" ]]; then
    for daemon in ${SUPERSET_DAEMONS[@]}; do
      if [[ "$daemon" == "init" ]]; then
        ${__SUPERSET_DAEMONS__[$daemon]}
      else
        if [[ "$daemon" == "worker" ]]; then
          run_worker_healthchecks
        fi

        ${__SUPERSET_DAEMONS__[$daemon]} &
      fi
    done

    tail -f /dev/null
  else
    __log__ "Any Superset daemons not defined. Exiting..."
  fi
}

main