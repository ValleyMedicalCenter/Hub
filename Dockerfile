FROM python:3.9

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
    REMOTE=https://github.com/Riverside-Healthcare/extract_management.git

RUN apt-get update -qq \
     && apt-get install -y -qq --no-install-recommends apt-utils curl pkg-config postgresql postgresql-contrib > /dev/null

RUN su - postgres -c "/etc/init.d/postgresql start && psql --command \"CREATE USER webapp WITH SUPERUSER PASSWORD 'nothing';\"  && createdb -O webapp atlas_hub_test"

RUN apt-get install -y -qq \
    build-essential \
    libssl-dev \
    libffi-dev \
    curl \
    git \
    wget \
    libldap2-dev \
    python3-dev \
    python3-pip \
    python3-setuptools \
    unixodbc \
    unixodbc-dev \
    libsqlite3-0 \
    libsasl2-dev \
    libxml2-dev \
    libxmlsec1-dev \
    libxmlsec1-dev \
    redis-server

WORKDIR /app

RUN git -c http.sslVerify=false clone --depth 1 "$REMOTE" . \
    && python -m pip install --disable-pip-version-check poetry \
    && poetry config virtualenvs.create false \
    && poetry install \
    && poetry env info

RUN cp web/model.py scheduler/ && cp web/model.py runner/

ENV FLASK_ENV=development \
    FLASK_DEBUG=True \
    FLASK_APP=web

RUN /etc/init.d/postgresql start && flask db init && flask db migrate && flask db upgrade && flask cli seed && flask cli seed_demo

CMD (redis-server &) && (/etc/init.d/postgresql start &) && (FLASK_APP=scheduler && flask run --port=5001 &) && (FLASK_APP=runner && flask run --port=5002 &) && flask run --host=0.0.0.0 --port=$PORT
