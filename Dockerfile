# docker build -t dtms .
# docker run -d --name torrent-bot --rm dtms
# docker start torrent-bot (without --rm in run)
# docker logs torrent-bot (without --rm in run)
FROM python:3.9.6
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ /usr/src/app
CMD python main.py
