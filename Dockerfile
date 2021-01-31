FROM python:3.8

RUN pip install requests pyyaml slackclient

COPY scraper.py .
COPY config.yml .

ENTRYPOINT ["python", "scraper.py"]
