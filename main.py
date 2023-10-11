import json
import requests
import sys
import asyncio
import httpx
import datetime
#import subprocess
import os
from api import CloudflareAPI
from cloudflareLists import CloudflareLists
from cloudflareRules import CloudflareRules

args = sys.argv

try:
    def log(message: str):
        #if bool(os.environ.get("COMMANDS_USE_SUBPROCESS", False)):
        #    subprocess.run(["echo", message])
        #else:
        print(message)

    listsConfig = json.load(open('./lists.json'))

    _domains = {}
    domains = []
    domainsErrors = []

    log("::notice::Fetching domains...")

    #######################
    # Async fetch domains #
    #######################
    async def fetchDomain(url: str, listType: str, domains: list, _domains: dict):
        try:
            async with httpx.AsyncClient() as session:
                log("::notice::Gettint list: " + url)
                list = await session.get(url)
                log("::notice::List fetched: " + url)

                for line in list.text.splitlines():
                    if not line.startswith('#') and not line == '' and not line == ' ' and not line.endswith('.'):

                            if listType == 'hostfile':
                                value = line.split(' ')[1]
                                if value not in _domains:
                                    domains.append({ "value": value })
                                    _domains[value] = True
                            elif listType == 'directDomains':
                                value = line
                                if value not in _domains:
                                    domains.append({ "value": value })
                                    _domains[value] = True
        except Exception as e:
            log("::error::Error fetching list: " + url)
            log("::error::" + str(e))
            domainsErrors.append(url)
        
    async def fetchDomains(lists: list, domains: list, _domains: dict):
        async with asyncio.TaskGroup() as tg:
            for list in lists:
                tg.create_task(fetchDomain(list['url'], list['type'], domains, _domains))


    asyncio.run(fetchDomains(listsConfig['lists'], domains, _domains))

    log("::notice::Done! " + str(len(domains)) + " domains fetched")

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

    log("::notice::Verifying Cloudflare API token...")
    get = cloudflareAPI.get('https://api.cloudflare.com/client/v4/user/tokens/verify')
    if get.status_code == 200:
        data = get.json()
        if data['success'] == True:
            expiresOn = data['result']['expires_on']
            if datetime.datetime.strptime(expiresOn, '%Y-%m-%dT%H:%M:%S%z') < datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=8):
                requests.post(args[3], data = json.dumps({
                    "text": "El token de Cloudflare Adblocker está a punto de caducar, por favor, renuévalo",
                    "username": "⚠️ [TOKEN RENEWAL] Cloudflare Adblocker"
                }))
                log("::notice::Cloudflare API token verified, but it's about to expire, please renew it")
            else:
                log("::notice::Cloudflare API token verified")
        else:
            log("::error file=main.py,line=79,title=Api Error::Cloudflare API token verification failed")

    cloudflareLists = CloudflareLists(cloudflareAPI)
    cloudflareRules = CloudflareRules(cloudflareAPI)
    log("::notice::Cloudflare API initialized")


    adBlockingRule = cloudflareRules.getAdblockingRule()
    adBlockingRuleId = adBlockingRule['id']
    log("::notice::Cloudflare Adblocking rule initialized")

    # Clear the rule before deleting the lists
    cloudflareRules.putRule(adBlockingRuleId, adBlockingRule)
    log("::notice::Cloudflare Adblocking rule cleared")

    lists = cloudflareLists.getLists()
    log("::notice::Cloudflare lists initialized")

    async def deleteLists(_lists: list):
        async with asyncio.TaskGroup() as tg:
            for list in _lists:
                if list['name'].startswith('adlist_'):
                    tg.create_task(cloudflareLists.deleteList(list['id']))

    log("::notice::Deleting Cloudflare lists")
    if lists is not None and len(lists) > 0:
        asyncio.run(deleteLists(lists))
        log("::notice::Cloudflare lists deleted")
    else:
        log("::notice::Cloudflare lists not found, skipping...")


    listsIds = []
    tasks = []
    errorLists = []

    log("::notice::Creating Cloudflare lists")
    async def createLists(_chunks: list, _tasks: list):
        async with asyncio.TaskGroup() as tg:
            for chunk in _chunks:
                task = tg.create_task(cloudflareLists.createList(f'adlist_{_chunks.index(chunk)}', f'Adlist {_chunks.index(chunk)}', chunk))
                _tasks.append((task, _chunks.index(chunk)))

    asyncio.run(createLists(chunks, tasks))

    for value in tasks:
        task = value[0]
        chunk = chunks[value[1]]
        if type(task.result()) == tuple:
            listName = task.result()[0]
            error = task.result()[1]
            errorLists.append((chunks.index(chunk), str(error)))
            log("::group::Error creating list " + listName)
            log("::error::Error creating the list")
            log("::error::" + str(error))
            log("::notice::-----------------------------------") 
            log("::notice::" + str(chunk))
            log("::endgroup::")
        else:
            listsIds.append(task.result()['id'])

    if len(errorLists) > 0:
        log("::warning::Cloudflare lists created with " + str(len(errorLists)) + " errors")
    elif len(listsIds) > 0:
        log("::notice::Cloudflare lists created")

    cloudflareRules.putRule(adBlockingRuleId, adBlockingRule, listsIds)
    log("::notice::Cloudflare Adblocking rule updated")

    if len(errorLists) > 0 or len(domainsErrors) > 0:

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
                "username": "⚠️ [WARNING] Cloudflare Adblocker",
                "attachments":[
                    {
                        "fallback":"Listado de errores",
                        "pretext":"Listado de errores",
                        "color":"#D00000",
                        "fields": attachmentFields
                    }
                ]
            }))

        if len(domainsErrors) > 0:
            attachmentFieldsDomains = []

            for error in domainsErrors:
                attachmentFieldsDomains.append({
                    "title": "# [Error URL " + str(error) + "]",
                    "value": error,
                    "short": False
                })

            requests.post(args[3], data = json.dumps({
                "text": "Algunos dominios de las listas no han funcionado o ya no están disponibles, " + str(len(domainsErrors)) + " listas no se han podido añadir",
                "username": "⚠️ [WARNING] Cloudflare Adblocker",
                "attachments":[
                    {
                        "fallback":"Dominios con errores",
                        "pretext":"Dominios con errores",
                        "color":"#D00000",
                        "fields": attachmentFields
                    }
                ]
            }))
    else:
        requests.post(args[3], data = json.dumps({
            "text": "Las listas de adblockers se han actualizado correctamente, se han añadido " + str(len(listsIds)) + " listas.",
            "username": "✅ Cloudflare Adblocker"
        }))

    log("::notice::Done! " + str(len(listsIds)) + " lists added")

except Exception as e:
    
    requests.post(args[3], data = json.dumps({
        "text": "Ha ocurrido un error al actualizar las listas de adblockers: " + str(e),
        "username": "🚨 [ERROR] Cloudflare Adblocker"
    }))
    log("::error file=main.py,title=Fatal error::" + str(e))
    
    raise e
