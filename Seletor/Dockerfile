FROM python:latest

COPY app.py /
COPY requirements.txt /

RUN pip install -r ./requirements.txt

EXPOSE 5001

CMD [ "python", "./app.py" ]
