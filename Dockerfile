FROM python:3.12-alpine
WORKDIR /opt/certbot-aliyun

RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.aliyun.com/g' /etc/apk/repositories && \
    apk add bash ca-certificates git gcc g++ libc-dev libxml2-dev libxslt-dev tzdata && \
    cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" >  /etc/timezone && \
    apk del tzdata

COPY . .
RUN /opt/certbot-aliyun/build_aliyun.sh;

ENTRYPOINT ["/opt/certbot-aliyun/bootstrap.sh"]
