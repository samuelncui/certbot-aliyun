from .config import get_config
import alibabacloud_slb20140515.client as slb
import alibabacloud_slb20140515.models as slbmdl
from alibabacloud_tea_openapi import models as open_api_models

from certbot.plugins import dns_common
from collections import defaultdict
from cryptography.x509 import load_pem_x509_certificate
import logging


def init_client(conf, region_id):
    cli = slb.Client(open_api_models.Config(
        access_key_id=conf.get('access_key_id'),
        access_key_secret=conf.get('access_key_secret'),
        region_id=region_id,
    ))
    return cli


class Uploader(object):
    def __init__(self, conf):
        self.conf = conf
        pass

    def upload(self, cert):
        path = f'{self.conf['work_dir']}/live/{cert['name']}'
        with open(f'{path}/fullchain.pem') as f:
            fullchain = f.read()
        with open(f'{path}/privkey.pem') as f:
            privkey = f.read()

        x509 = load_pem_x509_certificate(fullchain.encode())
        expire_date = x509.not_valid_after_utc.strftime('%Y-%m-%d')
        try:
            with open(f'{path}/.last_expire_date') as f:
                current_expire_date = f.read()
                logging.info(f'{cert['name']}: current_expire_date= {current_expire_date} new_expire_date= {expire_date}')
                if current_expire_date == expire_date:
                    logging.info(f'{cert['name']}: expire_date not changed, cert don\'t need update')
                    return
        except FileNotFoundError:
            pass

        for target in cert['targets']:
            cli = init_client(self.conf, target['region_id'])

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

        with open(f'{path}/.last_expire_date', 'w') as f:
            f.write(expire_date)

        logging.info(f'cert upload success, name= {cert['name']} expire_date= {expire_date}')
