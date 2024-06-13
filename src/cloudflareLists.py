import aiohttp
from api import CloudflareAPI
from asyncio import CancelledError

class CloudflareLists:

    def __init__(self, cloudflareAPI: CloudflareAPI):
        self.cloudflareAPI = cloudflareAPI
        pass

    def getLists(self):
        req = self.cloudflareAPI.get(f'https://api.cloudflare.com/client/v4/accounts/$$identifier$$/gateway/lists')

        if req.status_code == 200:
            return req.json()['result']
        else:
            raise Exception(f'CODE [{req.status_code}] error, request not completed: ' + req.text)

    async def deleteList(self, uuid: str, session: aiohttp.ClientSession):
        try:
            req = await self.cloudflareAPI.deleteAsync(f'https://api.cloudflare.com/client/v4/accounts/$$identifier$$/gateway/lists/{uuid}', session)

            if req.status == 200:
                _json = await req.json()
                if _json['success'] == True:
                    return _json['result']
                else:
                    return (uuid, f'Error on requests syntaxt: ' + str(_json))
            else:
                return (uuid, f'CODE [{req.status}] error, request not completed: ' + req.text)
        except Exception as e:
            return (uuid, f'Error on request: ' + str(e))
        
    async def createList(self, name: str, description: str, domains: list, session: aiohttp.ClientSession):
        try:
            req = await self.cloudflareAPI.postAsync('https://api.cloudflare.com/client/v4/accounts/$$identifier$$/gateway/lists', session, data = {
                'name': name,
                'description': description,
                'type': 'DOMAIN',
                'items': domains
            })

            if req.status == 200:
                _json = await req.json()
                if _json['success'] == True:
                    return _json['result']
                else:
                    return (name, f'Error on requests syntaxt: ' + str(_json))
            else:
                return (name, f'CODE [{req.status}] error, request not completed: ' + req.text)
        except Exception as e:
            return (name, f'Error on request: ' + str(e))
