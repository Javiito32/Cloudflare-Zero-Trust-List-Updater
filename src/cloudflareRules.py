from api import CloudflareAPI
from utils import removeNones
import os

class CloudflareRules:

    def __init__(self, cloudflareAPI: CloudflareAPI, dns_fqdn):
        self.cloudflareAPI = cloudflareAPI
        self.dns_fqdn = dns_fqdn
        pass

    def getRules(self):
        req = self.cloudflareAPI.get('https://api.cloudflare.com/client/v4/accounts/$$identifier$$/gateway/rules')

        if req.status_code == 200:
            return req.json()['result']
        else:
            raise Exception(f'CODE [{req.status_code}] error, request not completed: ' + req.text)

    def getAdblockingRule(self):
        rules = self.getRules()

        for rule in rules:
            if rule['name'] == 'Blocks ads':
                return rule

    def putRule(self, uuid: str, rule: dict, traffic: list = []):
        removeKeys = ['id', 'created_at', 'updated_at', 'deleted_at', 'version']
        for key in removeKeys:
            if key in rule:
                rule.pop(key)

        for k in rule:
            if rule[k] == None:
                rule.pop(k)

        removeNones(rule)

        if len(traffic) > 0:
            ruleString = ''
            for id in traffic:
                ruleString += f'dns.fqdn in ${id} or '
            rule['traffic'] = ruleString[:-4]
        else:
            rule['traffic'] = 'dns.fqdn == "' + self.dns_fqdn + '"'

        req = self.cloudflareAPI.put(f'https://api.cloudflare.com/client/v4/accounts/$$identifier$$/gateway/rules/{uuid}', data = rule)

        if req.status_code == 200:
            _json = req.json()
            if _json['success'] == True:
                return _json['result']
            else:
                raise Exception('Error on requests syntaxt: ' + str(_json))
        else:
            raise Exception(f'CODE [{req.status_code}] error, request not completed: ' + req.text)
