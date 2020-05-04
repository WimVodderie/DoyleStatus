FROM python:3-alpine

WORKDIR /usr/src/DoyleStatus

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY config.py ./
COPY DoyleStatus.py ./

CMD [ "python", "./DoyleStatus.py" ]
