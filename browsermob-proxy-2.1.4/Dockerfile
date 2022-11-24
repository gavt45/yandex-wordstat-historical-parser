FROM openjdk:8-alpine3.9

EXPOSE 8080
EXPOSE 8082

WORKDIR /app

COPY . .

CMD ["./bin/browsermob-proxy", "--port", "8080", "--proxyPortRange", "8082", "--proxyPortRange", "8082"]
