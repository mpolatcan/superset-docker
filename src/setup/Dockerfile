ARG PYTHON_VERSION=""

FROM mpolatcan/superset:base-python${PYTHON_VERSION}

ARG SUPERSET_VERSION=""

MAINTAINER Mutlu Polatcan <mutlupolatcan@gmail.com>

RUN ${SUPERSET_VIRTUALENV}/bin/pip install apache-superset==${SUPERSET_VERSION} && \
    ${SUPERSET_VIRTUALENV}/bin/pip install -r other_deps.txt && \
    ${SUPERSET_VIRTUALENV}/bin/pip install -r db_deps.txt

USER superset
ENTRYPOINT ["./entrypoint.sh"]