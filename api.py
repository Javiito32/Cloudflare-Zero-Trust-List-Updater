import requests
import json

class CloudflareAPI:

    def __init__(self, apiToken: str, identifier: str):
        self.apiToken = apiToken
        self.identifier = identifier

    def get(self, url: str, headers: dict = {}):
        headers['Authorization'] = 'Bearer ' + self.apiToken
        url = url.replace('$$identifier$$', self.identifier)

        return requests.get(url, headers=headers)
    
    def put(self, url: str, headers: dict = {}, data: dict = {}):
        headers['Authorization'] = 'Bearer ' + self.apiToken
        url = url.replace('$$identifier$$', self.identifier)

        return requests.put(url, headers=headers, data = json.dumps(data))
    
    def delete(self, url: str, headers: dict = {}):
        headers['Authorization'] = 'Bearer ' + self.apiToken
        url = url.replace('$$identifier$$', self.identifier)

        return requests.delete(url, headers=headers)
    
    def post(self, url: str, headers: dict = {}, data: dict = {}):
        headers['Authorization'] = 'Bearer ' + self.apiToken
        url = url.replace('$$identifier$$', self.identifier)

        return requests.post(url, headers=headers, data = json.dumps(data))