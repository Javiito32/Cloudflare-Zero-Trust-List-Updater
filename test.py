from api import CloudflareAPI
import datetime

apiToken = 'zA3GoUls0gf9osYSRKr1nlIS782IVC57tB30hdqx'
identifier = 'f51c931df52df09c67c857205ada793c'

cloudflareAPI = CloudflareAPI(apiToken, identifier)

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
    else:
        print('Error: ' + data['errors'][0]['message'])