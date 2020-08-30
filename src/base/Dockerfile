ARG PYTHON_VERSION=""

FROM python:${PYTHON_VERSION}-slim

MAINTAINER Mutlu Polatcan <mutlupolatcan@gmail.com>

ENV SUPERSET_USER_HOME="/home/superset"
ENV SUPERSET_HOME="${SUPERSET_USER_HOME}/superset" \
    SUPERSET_VIRTUALENV="${SUPERSET_USER_HOME}/superset/venv"\
    SUPERSET_CONFIG_PATH="${SUPERSET_USER_HOME}/superset/superset_config.py" \
    SUPERSET_DAEMONS="NULL"
ENV PATH=${SUPERSET_VIRTUALENV}/bin:$PATH \
    PYTHONUNBUFFERED=1

WORKDIR ${SUPERSET_USER_HOME}

COPY db_deps.txt other_deps.txt entrypoint.sh ./
COPY superset_config.py ${SUPERSET_CONFIG_PATH}

RUN apt-get update && \
    mkdir -p /usr/share/man/man1 && \
    apt-get -y install build-essential \
                       default-jre \
                       libssl-dev \
                       libffi-dev \
                       libsasl2-dev \
                       libldap2-dev \
                       libmariadb-dev \
                       unixodbc \
                       unixodbc-dev \
                       procps \
                       netcat \
                       iputils-ping \
                       nano && \
    pip install --upgrade setuptools pip virtualenv && \
    addgroup superset && adduser --disabled-password --gecos "" --ingroup superset superset && \
    mkdir -p ${SUPERSET_USER_HOME} && \
    mkdir -p ${SUPERSET_HOME} ${SUPERSET_VIRTUALENV} && \
    virtualenv -p python3 ${SUPERSET_VIRTUALENV} && \
    chmod +x entrypoint.sh && \
    chown -R superset:superset ${SUPERSET_USER_HOME}
