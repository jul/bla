FROM debian:buster-slim
ENV LANG C.UTF-8
RUN mkdir -p /usr/share/man/man1 && mkdir -p /usr/share/man/man7
RUN apt-get update && apt-get -y dist-upgrade \
    && rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get -y --no-install-recommends install \
	python3 python3-pip python3-venv python3-setuptools
RUN useradd bla -d /app --uid 1000 -m -s /bin/bash
COPY --chown=bla . /app
USER bla 
WORKDIR /app
RUN python3 -m pip install --no-cache-dir --disable-pip-version-check -r requirements.full.txt
EXPOSE 5001
CMD PYTHONPATH="$PYTHONPATH:." python3 /app/scripts/lhl /app/bla.anonymous.json
