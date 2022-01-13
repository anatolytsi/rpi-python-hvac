FROM python:3.8-slim-buster

WORKDIR /app
RUN chmod 777 /app

COPY . ./
COPY ../rpi_interface.py ./pi_interface.py
COPY ../.env ./.env

RUN pip3 install -r requirements.txt

CMD ["python3", "flask_server/server.py"]
