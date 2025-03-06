# certbot-aliyun
tools regarding certbot built for aliyun

本工具可以利用 Certbot，通过阿里云 DNS 签发 Let's Encrypt 证书。之后通过阿里云 OpenAPI 将签发出来的证书配置到 CLB。再不给阿里云交冤枉钱！

使用 `build.sh` 脚本安装依赖，并使用 `run.sh` 脚本运行。只有在证书将过期时才会更新，可以加在每周自动任务中。
