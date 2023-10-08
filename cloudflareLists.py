import json
from api import CloudflareAPI

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

    def deleteList(self, uuid: str):
        req = self.cloudflareAPI.delete(f'https://api.cloudflare.com/client/v4/accounts/$$identifier$$/gateway/lists/{uuid}')

        if req.status_code == 200:
            _json = req.json()
            if _json['success'] == True:
                return _json['result']
            else:
                raise Exception(f'Error on requests syntaxt: ' + str(_json))
        else:
            raise Exception(f'CODE [{req.status_code}] error, request not completed: ' + req.text)
        
    def createList(self, name: str, description: str, domains: list):
        req = self.cloudflareAPI.post('https://api.cloudflare.com/client/v4/accounts/$$identifier$$/gateway/lists', data = {
            'name': name,
            'description': description,
            'type': 'DOMAIN',
            'items': domains
        })

        if req.status_code == 200:
            _json = req.json()
            if _json['success'] == True:
                return _json['result']
            else:
                raise Exception(f'Error on requests syntaxt: ' + str(_json))
        else:
            print(req.text)
            raise Exception(f'CODE [{req.status_code}] error, request not completed: ' + req.text)