FROM python:3.8-slim-buster

COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt

RUN useradd --create-home app
WORKDIR /home/app

USER app
COPY update_pool.py .
CMD [ "python", "./update_pool.py" ]
