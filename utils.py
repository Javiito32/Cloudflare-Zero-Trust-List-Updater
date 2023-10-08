def removeNones(obj: dict):
        keyList = list(obj.keys())
        for k in keyList:
            if k in obj:
                if obj[k] == None:
                    obj.pop(k)
                elif type(obj[k]) == dict:
                    removeNones(obj[k])