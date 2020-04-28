#!/bin/bash

# TODO Healthcheck for result backend

declare -A __SERVICE_PORTS__
__SERVICE_PORTS__[postgresql]="5432"
__SERVICE_PORTS__[mysql]="3306"
__SERVICE_PORTS__[redis]="6379"
__SERVICE_PORTS__[rabbitmq]="5672"
SUPERSET_COMPONENT_METADATA_DATABASE="metadata_database"
SUPERSET_COMPONENT_BROKER="broker"
SUPERSET_COMPONENT_BROKER_RESULT_BACKEND="broker_result_backend"

# $1: message
function __log__() {
  echo "[$(date '+%d/%m/%Y %H:%M:%S')] -> $1"
}

# $1: Service name
# $2: Service type
# $3: Service hostname
# $4: Service port
function health_checker() {
  __log__ "Superset $1 healtcheck started ($1_type: \"$2\", $1_host: \"$3\", $1_port: \"$4\")..."
  nc -z $3 $4
  result=$?
  counter=0

  until [[ $result -eq 0 ]]; do
    (( counter = counter + 1 ))

    if [[ ${SUPERSET_MAX_RETRY_TIMES} -ne -1 && $counter -ge ${SUPERSET_MAX_RETRY_TIMES} ]]; then
        __log__ "Superset $1 healthcheck failed ($1_type: \"$2\", $1_host: \"$3\", $1_port: \"$4\")..."
        __log__ "Max retry times \"${SUPERSET_MAX_RETRY_TIMES}\" reached. Exiting now..."
        exit 1
    fi

    __log__ "Waiting $1 is ready ($1_type: \"$2\", $1_host: \"$3\", $1_port: \"$4\"). Retrying after ${SUPERSET_RETRY_INTERVAL_IN_SECS} seconds... (times: $counter)."
    sleep ${SUPERSET_RETRY_INTERVAL_IN_SECS}
    nc -z $3 $4
    result=$?
  done

  __log__ "Superset $1 is ready ($1_type: \"$2\", $1_host: \"$3\", $1_port: \"$4\") ✔"
}

# $1: Service name
# $2: Service host
function __host_checker__() {
  if [[ "$2" == "" ]]; then
    __log__ "Superset $1 host is not defined. Exiting ✘..."
    exit 1
  else
    __log__ "Superset $1 host is $2. OK ✔"
  fi
}

function check_hosts_defined() {
  __host_checker__ "${SUPERSET_COMPONENT_METADATA_DATABASE}" "${METADATA_DB_HOST}"
}

function apply_default_ports_ifnotdef() {
    if [[ "${METADATA_DB_PORT}" == "NULL" ]]; then
      __log__ "Superset metadata database port is not defined. Default port \"${__SERVICE_PORTS__[${METADATA_DB_TYPE}]}\" will be used!"
      export METADATA_DB_PORT=${__SERVICE_PORTS__[${METADATA_DB_TYPE}]}
    fi

    if [[ "${CELERY_BROKER_PORT}" == "NULL" ]]; then
      __log__ "Superset broker port is not defined. Default port \"${__SERVICE_PORTS__[${CELERY_BROKER_TYPE}]}\" will be used!"
      export CELERY_BROKER_PORT=${__SERVICE_PORTS__[${CELERY_BROKER_TYPE]}}
    fi
}

function run_healthchecks() {
  health_checker "${SUPERSET_COMPONENT_METADATA_DATABASE}" "${METADATA_DB_TYPE}" "${METADATA_DB_HOST}" "${METADATA_DB_PORT}"
  health_checker "${SUPERSET_COMPONENT_BROKER}" "${CELERY_BROKER_TYPE}" "${CELERY_BROKER_HOST}" "${CELERY_BROKER_PORT}"
}

function run_superset() {
   # Initialize Superset application database
  superset db upgrade

  export FLASK_APP=superset

  __log__ "Creating admin user..."
  superset fab create-admin --username ${ADMIN_USERNAME} \
                            --firstname ${ADMIN_FIRSTNAME} \
                            --lastname ${ADMIN_LASTNAME} \
                            --email ${ADMIN_EMAIL} \
                            --password ${ADMIN_PASSWORD}

  if [[ "${LOAD_EXAMPLES}" == "true" ]]; then
      __log__ "Loading Superset examples..."
      superset load_examples
  fi

  __log__ "Initializing Superset..."
  superset init

  __log__ "Running Superset..."
  superset run --host 0.0.0.0 --port 8088 --with-threads --reload --debugger
}


function main() {
    check_hosts_defined

    apply_default_ports_ifnotdef

    run_healthchecks

    run_superset
}

main