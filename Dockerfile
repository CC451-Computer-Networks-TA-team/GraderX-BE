# Use the Python3.7.2 image
FROM python:latest

RUN python -m pip install --upgrade pip setuptools wheel

COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD [ "python", "app.py" ]