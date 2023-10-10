import json
import requests
import sys
import asyncio
import httpx
import datetime
import logging
from api import CloudflareAPI
from cloudflareLists import CloudflareLists
from cloudflareRules import CloudflareRules

args = sys.argv
logger = logging.getLogger(__name__)

try:

    listsConfig = json.load(open('./lists.json'))

    _domains = {}
    domains = []

    logger.info("echo ::debug::Fetching domains...")

    #######################
    # Async fetch domains #
    #######################
    async def fetchDomain(url: str, listType: str, domains: list, _domains: dict):
        async with httpx.AsyncClient() as session:
                logger.info("echo ::debug::Gettint list: " + url)
                list = await session.get(url)
                logger.info("echo ::debug::List fetched: " + url)

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

                return list
        
    async def fetchDomains(lists: list, domains: list, _domains: dict):
        async with asyncio.TaskGroup() as tg:
            for list in lists:
                tg.create_task(fetchDomain(list['url'], list['type'], domains, _domains))


    asyncio.run(fetchDomains(listsConfig['lists'], domains, _domains))

    logger.info("echo ::debug::Done! " + str(len(domains)) + " domains fetched")

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

    logger.info("echo ::debug::Verifying Cloudflare API token...")
    get = cloudflareAPI.get('https://api.cloudflare.com/client/v4/user/tokens/verify')
    if get.status_code == 200:
        data = get.json()
        if data['success'] == True:
            expiresOn = data['result']['expires_on']
            if datetime.datetime.strptime(expiresOn, '%Y-%m-%dT%H:%M:%S%z') < datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=8):
                requests.post(args[3], data = json.dumps({
                    "text": "El token de Cloudflare Adblocker está a punto de caducar, por favor, renuévalo",
                    "username": "⚠️ [TOKEN RENEWAL] Cloudflare Adblockers"
                }))
                logger.info("echo ::debug::Cloudflare API token verified, but it's about to expire, please renew it")
            else:
                logger.info("echo ::debug::Cloudflare API token verified")
        else:
            logger.info("echo ::error file=main.py,line=79,title=Api Error::Cloudflare API token verification failed")

    cloudflareLists = CloudflareLists(cloudflareAPI)
    cloudflareRules = CloudflareRules(cloudflareAPI)
    logger.info("echo ::debug::Cloudflare API initialized")


    adBlockingRule = cloudflareRules.getAdblockingRule()
    adBlockingRuleId = adBlockingRule['id']
    logger.info("echo ::debug::Cloudflare Adblocking rule initialized")

    # Clear the rule before deleting the lists
    cloudflareRules.putRule(adBlockingRuleId, adBlockingRule)
    logger.info("echo ::debug::Cloudflare Adblocking rule cleared")

    lists = cloudflareLists.getLists()
    logger.info("echo ::debug::Cloudflare lists initialized")

    counter = 0
    logger.info("echo ::debug::Deleting Cloudflare lists")
    if lists is not None and len(lists) > 0:
        for list in lists:
            if list['name'].startswith('adlist_'):
                cloudflareLists.deleteList(list['id'])
        logger.info("echo ::debug::Cloudflare lists deleted")
    else:
        logger.info("echo ::debug::Cloudflare lists not found, skipping...")


    listsIds = []
    errorLists = []

    counter = 0
    logger.info("echo ::debug::Creating Cloudflare lists")
    for chunk in chunks:
        try:
            listsIds.append(cloudflareLists.createList(f'adlist_{chunks.index(chunk)}', f'Adlist {chunks.index(chunk)}', chunk)['id'])
        except Exception as e:
            errorLists.append((chunks.index(chunk), str(e)))
            logger.info("echo ::group::Error creating list " + str(chunks.index(chunk)))
            logger.info("echo ::error::Error creating the list")
            logger.info("echo ::error::" + str(e))
            logger.info("echo ::debug::-----------------------------------") 
            logger.info("echo ::debug::" + str(chunk))
            logger.info("echo ::endgroup::")
            pass
    logger.info("echo ::debug::Cloudflare lists created")

    cloudflareRules.putRule(adBlockingRuleId, adBlockingRule, listsIds)
    logger.info("echo ::debug::Cloudflare Adblocking rule updated")

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

    logger.info("echo ::debug::Done!")

except Exception as e:
    
    requests.post(args[3], data = json.dumps({
        "text": "Ha ocurrido un error al actualizar las listas de adblockers: " + str(e),
        "username": "🚨 [ERROR] Cloudflare Adblockers"
    }))
    logger.info("echo ::error file=main.py,title=Fatal error::" + str(e))
    
    raise e
