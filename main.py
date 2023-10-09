import json
import requests
import os
import sys
from api import CloudflareAPI
from cloudflareLists import CloudflareLists
from cloudflareRules import CloudflareRules

args = sys.argv

try:

    listsConfig = json.load(open('./lists.json'))

    _domains = []
    domains = []

    print("Fetching domains...")
    for _list in listsConfig['lists']:

        req = requests.get(_list['url'])

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
    print("Done! " + str(len(domains)) + " domains fetched")

    chunks = [domains[x:x+1000] for x in range(0, len(domains), 1000)]

    # Disabled saving domains to a file
    '''
    key = 0
    for chunk in chunks:

        file = open(f'./domains/domains_{key}.csv', 'w')
        for domain in chunk:

            file.write(domain['value'] + '\n')

        file.close()
        key += 1
    '''

    apiToken = args[1]
    identifier = args[2]

    cloudflareAPI = CloudflareAPI(apiToken, identifier)

    cloudflareLists = CloudflareLists(cloudflareAPI)
    cloudflareRules = CloudflareRules(cloudflareAPI)
    print("Cloudflare API initialized")


    adBlockingRule = cloudflareRules.getAdblockingRule()
    adBlockingRuleId = adBlockingRule['id']
    print("Cloudflare Adblocking rule initialized")

    # Clear the rule before deleting the lists
    cloudflareRules.putRule(adBlockingRuleId, adBlockingRule)
    print("Cloudflare Adblocking rule cleared")

    lists = cloudflareLists.getLists()
    print("Cloudflare lists initialized")

    counter = 0
    print("Deleting Cloudflare lists")
    if lists is not None and len(lists) > 0:
        for list in lists:
            if list['name'].startswith('adlist_'):
                cloudflareLists.deleteList(list['id'])
        print("Cloudflare lists deleted")
    else:
        print("Cloudflare lists not found, skipping...")


    listsIds = []
    errorLists = []

    counter = 0
    print("Creating Cloudflare lists")
    for chunk in chunks:
        try:
            listsIds.append(cloudflareLists.createList(f'adlist_{chunks.index(chunk)}', f'Adlist {chunks.index(chunk)}', chunk)['id'])
        except Exception as e:
            errorLists.append((chunks.index(chunk), str(e)))
            print("Error creating list " + str(chunks.index(chunk)))
            pass
    print("Cloudflare lists created")

    cloudflareRules.putRule(adBlockingRuleId, adBlockingRule, listsIds)
    print("Cloudflare Adblocking rule updated")

    if len(errorLists) > 0:

        attachmentFields = []

        for error in errorLists:
            attachmentFields.append({
                "title": "# [Error chunk " + str(error[0]) + "]",
                "value": error[1],
                "short": False
            })
            

        requests.post(args[3], data = json.dumps({
            "text": "Las listas de adblockers se han actualizado con errores, " + str(len(errorLists)) + " listas no se han podido añadir",
            "username": "⚠️ [WARNING] Cloudflare Adblockers",
            "attachments":[
                {
                    "fallback":"Listado de errores",
                    "pretext":"Listado de errores",
                    "color":"#D00000",
                    "fields": attachmentFields
                }
            ]
        }))
    else:
        requests.post(args[3], data = json.dumps({
            "text": "Las listas de adblockers se han actualizado correctamente, se han añadido " + str(len(listsIds)) + " listas.",
            "username": "✅ Cloudflare Adblockers"
        }))

    print("Done!")

except Exception as e:
    
    requests.post(args[3], data = json.dumps({
        "text": "Ha ocurrido un error al actualizar las listas de adblockers: " + str(e),
        "username": "🚨 [ERROR] Cloudflare Adblockers"
    }))
    print("Fatal error has ocurred")
    
    raise e
