from queue import Queue, Full
import time
import requests
import threading
import random
import string

def replace_char(name):
    if name[-1].isdigit():
        index = len(name)-1
    else:
        index = random.randint(0, len(name)-1)
    name = list(name)
    char = name[index]
    
    if char.isdigit():
        name[index] = random.choice(string.digits)
    elif char.isalpha() and char == char.lower():
        name[index] = random.choice(string.ascii_lowercase)
    elif char.isalpha() and char == char.upper():
        name[index] = random.choice(string.ascii_uppercase)
    else:
        del name[index]
        
    return "".join(name)

class UsernameGenerator:
    def __init__(self):
        self.q = Queue(maxsize=1000)
        self.workers = list()
        
    def start(self, n):
        for _ in range(n):
            self.Worker(self).start()
    
    def get(self):
        return self.q.get(True)
    
    class Worker(threading.Thread):
        def __init__(self, parent):
            self.parent = parent
            self.parent.workers.append(self)
            super().__init__()
        
        def run(self):
            while 1:
                try:
                    uid = random.randint(1, 100000000)
                    name = requests.get("https://users.roblox.com/v1/users/"+str(uid)).json()["name"]
                    name = replace_char(name)
                    
                    r = requests.get(f"https://auth.roblox.com/v1/usernames/validate?birthday=2005-01-02T23:00:00.000Z&context=Signup&username=" + name).json()
                    if r["code"] != 0: continue
                    
                    while 1:
                        try:
                            self.parent.q.put(name)
                            break
                        except Full:
                            time.sleep(1)
                except Exception as e:
                    pass#print(e)