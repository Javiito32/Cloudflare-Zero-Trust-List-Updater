import requests
import json
import time

class CloudflareAPI:

    def __init__(self, apiToken: str, identifier: str):
        self.apiToken = apiToken
        self.identifier = identifier
        self.madeRequests = 0
        self.cloudflareAPImaxRequests = 1200
        self.cloudflareAPImaxRequestsTime = 301

    def requestCounter(self, amount: int = 1):
        self.madeRequests += amount
        if self.madeRequests >= self.cloudflareAPImaxRequests:
            self.madeRequests = 0
            time.sleep(self.cloudflareAPImaxRequestsTime)

    def get(self, url: str, headers: dict = {}):
        headers['Authorization'] = 'Bearer ' + self.apiToken
        url = url.replace('$$identifier$$', self.identifier)
        
        self.requestCounter()
        return requests.get(url, headers=headers)
    
    def put(self, url: str, headers: dict = {}, data: dict = {}):
        headers['Authorization'] = 'Bearer ' + self.apiToken
        url = url.replace('$$identifier$$', self.identifier)

        self.requestCounter()
        return requests.put(url, headers=headers, data = json.dumps(data))
    
    def delete(self, url: str, headers: dict = {}):
        headers['Authorization'] = 'Bearer ' + self.apiToken
        url = url.replace('$$identifier$$', self.identifier)

        self.requestCounter()
        return requests.delete(url, headers=headers)
    
    def post(self, url: str, headers: dict = {}, data: dict = {}):
        headers['Authorization'] = 'Bearer ' + self.apiToken
        url = url.replace('$$identifier$$', self.identifier)

        self.requestCounter()
        return requests.post(url, headers=headers, data = json.dumps(data))