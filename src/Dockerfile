FROM python:3.7-slim

MAINTAINER <mutlupolatcan@gmail.com> Mutlu Polatcan

ENV SUPERSET_USER_HOME="/home/superset"
ENV SUPERSET_HOME="${SUPERSET_USER_HOME}/superset" \
    SUPERSET_VIRTUALENV="${SUPERSET_USER_HOME}/superset/venv"\
    SUPERSET_CONFIG_PATH="${SUPERSET_HOME}/superset/superset_config.py" \
    SUPERSET_DAEMONS="NULL"
ENV PATH=${SUPERSET_VIRTUALENV}/bin:$PATH \
    PYTHONUNBUFFERED=1

WORKDIR ${SUPERSET_USER_HOME}

ADD db_deps.txt .
ADD other_deps.txt .
ADD entrypoint.sh .
ADD superset_config.py ${SUPERSET_CONFIG_PATH}

RUN apt-get update && \
    apt-get -y install build-essential \
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
    ${SUPERSET_VIRTUALENV}/bin/pip install apache-superset && \
    ${SUPERSET_VIRTUALENV}/bin/pip install -r other_deps.txt && \
    ${SUPERSET_VIRTUALENV}/bin/pip install -r db_deps.txt && \
    chmod +x entrypoint.sh && \
    chown -R superset:superset ${SUPERSET_USER_HOME}

USER superset
ENTRYPOINT ["./entrypoint.sh"]