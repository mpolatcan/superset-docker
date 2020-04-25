#!/bin/bash

function initialize_superset() {
   # Initialize Superset application database
  superset db upgrade

  export FLASK_APP=superset

  # Create admin user
  superset fab create-admin --username ${ADMIN_USERNAME} \
                            --firstname ${ADMIN_FIRSTNAME} \
                            --lastname ${ADMIN_LASTNAME} \
                            --email ${ADMIN_EMAIL} \
                            --password ${ADMIN_PASSWORD}

  if [[ "${LOAD_EXAMPLES}" == "true" ]]; then
      echo "Loading Superset examples..."
      superset load_examples
  fi

  # Initialize Superset
  superset init
}


initialize_superset
superset run --host 0.0.0.0 --port 8088 --with-threads --reload --debugger

