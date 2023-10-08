import json
import requests
import os
import time
from api import CloudflareAPI
from cloudflareLists import CloudflareLists
from cloudflareRules import CloudflareRules

listsConfig = json.load(open('./lists.json'))

_domains = []
domains = []

for _list in listsConfig['lists']:

    req = requests.get(_list['url'], verify=False)

    if req.status_code == 200:
        for line in req.text.splitlines():

            if not line.startswith('#') and not line == '' and not line == ' ' and not line.endswith('.'):

                if _list['type'] == 'hostfile':
                    value = line.split(' ')[1]
                    if value not in _domains:
                        domains.append({ "value": value })
                        _domains.append(value)
                elif _list['type'] == 'directDomains':
                    value = line
                    if value not in _domains:
                        domains.append({ "value": value })
                        _domains.append(value)


chunks = [domains[x:x+1000] for x in range(0, len(domains), 1000)]

key = 0
for chunk in chunks:

    file = open(f'./domains/domains_{key}.csv', 'w')
    for domain in chunk:

        file.write(domain['value'] + '\n')

    file.close()
    key += 1


apiToken = os.environ.get('token')
email = os.environ.get('email')
identifier = os.environ.get('identifier')

cloudflareAPI = CloudflareAPI(apiToken, identifier)

cloudflareLists = CloudflareLists(cloudflareAPI)
cloudflareRules = CloudflareRules(cloudflareAPI)


adBlockingRule = cloudflareRules.getAdblockingRule()

# Clear the rule before deleting the lists
cloudflareRules.putRule(adBlockingRule['id'], adBlockingRule)

lists = cloudflareLists.getLists()

time.sleep(3)

counter = 0
if lists is not None and len(lists) > 0:
    for list in lists:
        if lists['name'].startswith('adlist_'):
            cloudflareLists.deleteList(list['id'])

            counter += 1
            if counter == 5:
                time.sleep(3) # Just to avoid bans


listsIds = []

counter = 0
for chunk in chunks:
    listsIds.append(cloudflareLists.createList(f'adlist_{chunks.index(chunk)}', f'Adlist {chunks.index(chunk)}', chunk)['id'])
    counter += 1
    if counter == 5:
        time.sleep(3) # Just to avoid bans
    
cloudflareRules.putRule(adBlockingRule['id'], adBlockingRule, listsIds)
