FROM python:latest

COPY main.py /
COPY requirements.txt /

RUN pip install -r ./requirements.txt

EXPOSE 5001

CMD [ "python", "./main.py" ]
