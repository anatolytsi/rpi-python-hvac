FROM python:3.8-slim-buster

WORKDIR /app
RUN chmod 777 /app

COPY ./flask_server/requirements.txt ./requirements.txt
RUN pip3 install -r requirements.txt

COPY ./flask_server ./
COPY ./flask_server/rpi_interface.py ./rpi_interface.py
COPY ./.env ./.env

CMD ["python3", "server.py"]
