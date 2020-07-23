# Use the Python3.7.2 image
FROM python:3.8.5-slim

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN pip install -r requirements.txt
RUN rm requirements.txt
CMD [ "python", "run.py" ]