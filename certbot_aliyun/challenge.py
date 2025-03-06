from .config import get_config
import alibabacloud_alidns20150109.client as alidns
import alibabacloud_alidns20150109.models as alidnsmdl
from alibabacloud_tea_openapi import models as open_api_models

from certbot.plugins import dns_common


def init_client(conf):
    cli = alidns.Client(open_api_models.Config(
        access_key_id=conf.get('access_key_id'),
        access_key_secret=conf.get('access_key_secret'),
    ))
    return cli


class Challenger(object):
    CHALLENGE_PREFIX = '_acme-challenge'

    def __init__(self, conf):
        self.cli = init_client(conf)

    def auth(self, name, value):
        prefix, domain = self._split_name(name)
        rr = self._get_challenge_prefix(prefix)

        try:
            self._cleanup(rr, domain)
        except Exception as e:
            pass

        self.cli.add_domain_record(alidnsmdl.AddDomainRecordRequest(
            domain_name=domain,
            type='TXT',
            rr=rr,
            value=value,
        ))

    def cleanup(self, name):
        prefix, domain = self._split_name(name)
        rr = self._get_challenge_prefix(prefix)

        try:
            self._cleanup(rr, domain)
        except Exception as e:
            pass
    
    def _cleanup(self, rr, domain):
        r = self.cli.describe_domain_records(alidnsmdl.DescribeDomainRecordsRequest(
            domain_name=domain,
            rrkey_word=rr,
        ))

        if not r.body or not r.body.domain_records or not r.body.domain_records.record:
            raise ValueError(f"records not found, domain= {domain}")
        
        for record in r.body.domain_records.record:
            if record.rr != rr:
                continue
            self.cli.delete_domain_record(alidnsmdl.DeleteDomainRecordRequest(record_id=record.record_id))

    def _get_challenge_prefix(self, prefix: str):
        if prefix == '@':
            return self.CHALLENGE_PREFIX
        return self.CHALLENGE_PREFIX + '.' + prefix

    def _split_name(self, name: str):
        domain_name_guesses = dns_common.base_domain_name_guesses(name)

        for domain_name in domain_name_guesses:
            r = self.cli.describe_domains(alidnsmdl.DescribeDomainsRequest(key_word=domain_name))
            if not r.body or not r.body.domains or not r.body.domains.domain:
                continue

            for d in r.body.domains.domain:
                if d.domain_name != domain_name:
                    continue

                if domain_name == name:
                    return '@', domain_name

                prefix = name[:name.rindex('.' + domain_name)]
                return prefix, domain_name

        raise ValueError(f"domain not found, name= {name}")


if __name__ == '__main__':
    import sys, getopt, logging, os

    argc, argv = len(sys.argv), sys.argv
    opts, args = getopt.getopt(
        argv[1:],
        '',
        [
            'conf=',
            'auth',
            'cleanup',
        ]
    )

    conf = None
    for opt, arg in opts:
        if opt in ('--conf'):
            conf = get_config(arg)
            continue

        if opt in ('-a', '--auth'):
            if 'CERTBOT_DOMAIN' not in os.environ:
                raise Exception('Environment variable CERTBOT_DOMAIN is empty.')
            if 'CERTBOT_VALIDATION' not in os.environ:
                raise Exception('Environment variable CERTBOT_VALIDATION is empty.')

            Challenger(conf).auth(os.environ['CERTBOT_DOMAIN'], os.environ['CERTBOT_VALIDATION'])
            continue

        if opt in ('-c', '--cleanup'):
            if 'CERTBOT_DOMAIN' not in os.environ:
                raise Exception('Environment variable CERTBOT_DOMAIN is empty.')

            Challenger(conf).cleanup(os.environ['CERTBOT_DOMAIN'])
            continue

        logging.error('Invalid option: ' + opt)

    sys.exit()
