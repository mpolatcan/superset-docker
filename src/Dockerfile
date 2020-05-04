FROM python:3.7-slim

MAINTAINER <mutlupolatcan@gmail.com> Mutlu Polatcan

ENV SUPERSET_HOME="/superset"
ENV SUPERSET_VIRTUALENV="${SUPERSET_HOME}/venv"\
    SUPERSET_CONFIG_PATH="${SUPERSET_HOME}/superset_config.py" \
    SUPERSET_DAEMONS="NULL"
ENV PATH=${SUPERSET_VIRTUALENV}/bin:$PATH \
    PYTHONUNBUFFERED=1

ADD db_deps.txt /db_deps.txt
ADD other_deps.txt /other_deps.txt
ADD entrypoint.sh /entrypoint.sh
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
                       netcat && \
    pip install --upgrade setuptools pip virtualenv && \
    mkdir -p ${SUPERSET_VIRTUALENV} && \
    virtualenv -p python3 ${SUPERSET_VIRTUALENV} && \
    ${SUPERSET_VIRTUALENV}/bin/pip install apache-superset && \
    ${SUPERSET_VIRTUALENV}/bin/pip install -r other_deps.txt && \
    ${SUPERSET_VIRTUALENV}/bin/pip install -r db_deps.txt && \
    chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]