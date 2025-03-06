import os
import logging
from .config import get_config
from .upload import Uploader


class Certbot(object):
    def __init__(self, conf_path):
        self.conf_path = conf_path
        self.conf = get_config(conf_path)
        self.uploader = Uploader(conf_path, self.conf)

    def sign_cert(self, cert):
        domains = ','.join(d.strip() for d in cert['domains'])
        command = f"""certbot certonly \
            --config-dir '{self.conf['config_dir']}' \
            --work-dir '{self.conf['work_dir']}' \
            --logs-dir '{self.conf['logs_dir']}' \
            --non-interactive \
            --agree-tos \
            --no-eff-email \
            --no-redirect \
            --email '{self.conf['email']}' \
            --manual \
            --manual-auth-hook $'python -m certbot_aliyun.challenge --conf=\'{self.conf_path}\' --auth' \
            --manual-cleanup-hook $'python -m certbot_aliyun.challenge --conf=\'{self.conf_path}\' --cleanup' \
            --preferred-challenges dns \
            --cert-name '{cert['name']}' \
            -d '{domains}'
        """
        if 'certbot_proxy' in self.conf:
            proxy = self.conf['certbot_proxy']
            command = f'HTTP_PROXY="{proxy}" HTTPS_PROXY="{proxy}" ALL_PROXY="{proxy}" ' + command

        logging.info(f'sign cert, command= {command}')
        sign = os.system(command)
        if sign != 0:
            raise ValueError(f'cert failed, sign unexpected, {sign}')

    def upload(self, cert):
        self.uploader.upload(cert)

    def update_all(self):
        for cert in self.conf['certs']:
            logging.info(f'{cert['name']}: updating...')
            self.sign_cert(cert)
            self.upload(cert)


if __name__ == '__main__':
    import sys, getopt, logging, os

    import logging
    logging.basicConfig(
        level=logging.INFO,
        handlers=[logging.StreamHandler()]
    )

    argc, argv = len(sys.argv), sys.argv
    opts, args = getopt.getopt(
        argv[1:],
        '',
        [
            'conf=',
        ]
    )

    conf_path = 'config.yaml'
    for opt, arg in opts:
        if opt in ('--conf'):
            conf_path = arg
            continue

        logging.error('Invalid option: ' + opt)

    c = Certbot(conf_path)
    c.update_all()
    sys.exit()
