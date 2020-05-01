FROM python:3.6.10-buster
COPY . /app
WORKDIR /app
RUN apt -y install git && pip3 install -r requirements.txt
ENTRYPOINT [ "python3", "image_capture_daemon.py" ]
CMD []
