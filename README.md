# Yandex wordstat parser

with blackjack and hookers

## run

```sh
docker run --rm \
  -e EMAIL="asdsaddsasda@yandex.ru" \
  -e PASS="sadsda" \
  -e PROXY_URI="http://host.docker.internal" \
  -e RUCAPTCHA_TOKEN="asdsdadsadsa" \
  -e WEBDRIVER="http://host.docker.internal:4444" \
  -e RHOST="host.docker.internal" \
  -e RPORT="6379" \
  yandex-worker:latest
```
