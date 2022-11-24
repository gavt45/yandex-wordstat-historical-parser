FROM python:3.9

ENV EMAIL=""
ENV PASS=""
ENV PROXY_URI=http://host.docker.internal
ENV RUCAPTCHA_TOKEN=""
ENV WEBDRIVER=""
ENV RHOST="redis"
ENV RPORT=6379

RUN mkdir /app
WORKDIR /app

COPY requirements.txt /app/
RUN python3 -m pip install -r requirements.txt

RUN curl -L https://raw.githubusercontent.com/eficode/wait-for/v2.2.3/wait-for -o /bin/wait-for && chmod +x /bin/wait-for

COPY . .
#COPY yandex_parser/ /app/
#COPY browsermob_proxy_py/ /app/

CMD ["python3", "main.py"]
