from .config import get_config
import alibabacloud_slb20140515.client as slb
import alibabacloud_slb20140515.models as slbmdl
from alibabacloud_tea_openapi import models as open_api_models

from certbot.plugins import dns_common
from collections import defaultdict
from cryptography.x509 import load_pem_x509_certificate
import logging
import hashlib


def init_client(conf, cert, target):
    access_key_id = target.get('access_key_id') or cert.get('access_key_id') or conf.get('access_key_id')
    access_key_secret = target.get('access_key_secret') or cert.get('access_key_secret') or conf.get('access_key_secret')
    cli = slb.Client(open_api_models.Config(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        region_id=target.get('region_id'),
    ))
    return cli


class Uploader(object):
    def __init__(self, conf_path, conf):
        self.conf_path = conf_path
        self.conf = conf
        
        with open(conf_path) as f:
            self.conf_sign = hashlib.sha256(f.read().encode()).hexdigest()

    def upload(self, cert):
        path = f'{self.conf['work_dir']}/live/{cert['name']}'
        with open(f'{path}/fullchain.pem') as f:
            fullchain = f.read()
        with open(f'{path}/privkey.pem') as f:
            privkey = f.read()

        x509 = load_pem_x509_certificate(fullchain.encode())
        expire_date = x509.not_valid_after_utc.strftime('%Y-%m-%d')
        current_sign = f'{expire_date}|{self.conf_sign}'
        original_sign = ''
        try:
            with open(f'{path}/.update_sign') as f:
                original_sign = f.read()
        except FileNotFoundError:
            pass

        logging.info(f'{cert['name']}: original_sign= {original_sign} current_sign= {current_sign}')
        if original_sign == current_sign:
            logging.info(f'{cert['name']}: update sign not changed, cert don\'t need update')
            return

        for target in cert['targets']:
            cli = init_client(self.conf, cert, target)

            aliyun_cert_name = f'lets-encrypt/{expire_date}/{cert['name']}'
            r = cli.upload_server_certificate(slbmdl.UploadServerCertificateRequest(
                ali_cloud_certificate_name=aliyun_cert_name,
                ali_cloud_certificate_region_id=target['region_id'],
                server_certificate_name=aliyun_cert_name,
                server_certificate=fullchain,
                private_key=privkey,
            ))
            cert_id = r.body.server_certificate_id
            region_id = target['region_id']

            for lb in target['lbs']:
                try:
                    if 'ext_domain' in lb:
                        r = cli.describe_domain_extensions(slbmdl.DescribeDomainExtensionsRequest(
                            load_balancer_id=lb['id'],
                            region_id=region_id,
                            listener_port=lb['port'],
                        ))
                        
                        if not r.body or not r.body.domain_extensions or not r.body.domain_extensions.domain_extension:
                            continue

                        ext = None
                        for e in r.body.domain_extensions.domain_extension:
                            if e.domain == lb['ext_domain']:
                                ext = e
                                break
                        else:
                            raise ValueError("ext_domain not found, {lb['ext_domain']}")

                        r = cli.set_domain_extension_attribute(slbmdl.SetDomainExtensionAttributeRequest(
                            domain_extension_id=ext.domain_extension_id,
                            region_id=region_id,
                            server_certificate_id=cert_id,
                        ))
                        continue

                    r = cli.set_load_balancer_httpslistener_attribute(slbmdl.SetLoadBalancerHTTPSListenerAttributeRequest(
                        region_id=region_id,
                        load_balancer_id=lb['id'],
                        listener_port=lb['port'],
                        server_certificate_id=cert_id,
                    ))
                    continue
                except Exception as e:
                    logging.error(f'upload for lb failed, lb= {lb}, error= {e}')

        with open(f'{path}/.update_sign', 'w') as f:
            f.write(current_sign)

        logging.info(f'cert upload success, name= {cert['name']} expire_date= {expire_date} current_sign= {current_sign}')
