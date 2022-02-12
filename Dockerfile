FROM python:3.8

RUN pip install --upgrade pip
COPY requirements.txt /
RUN pip install -r /requirements.txt
RUN mkdir /app
COPY . /app
WORKDIR /app

EXPOSE 8000

CMD run python app.py
