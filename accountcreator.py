## Roblox account generator 
## twitter.com/h0nde
## 2020-09-10

from solver import Solver
from username_gen import UsernameGenerator
import requests
import threading
from random import randint, choice
from counter import IntervalCounter
import yaml
import exrex
import ctypes
import time
import string
import os

with open("config.yaml") as f:
    config = yaml.safe_load(f)

if not os.path.exists("logs"):
    os.mkdir("logs")

if config["username_method"] == "experimental":
    un_gen = UsernameGenerator()
    un_gen.start(15)

counter = IntervalCounter()
solver = Solver(
    public_key="A2A14B1D-1AF3-C791-9BBC-EE33CC7A0A6F",
    service_url="https://roblox-api.arkoselabs.com",
    proxies=open("proxies.txt").read().splitlines())

class RobloxError(Exception): pass
class Captcha(Exception): pass

lock = threading.Lock()
def save_account(account):
    counter.add()
    with lock:
        print("Created account:", account)

        with open("logs/cookies.txt", "a") as f:
            f.write(account.cookie + "\n")
        
        with open("logs/combos_cookies.txt", "a") as f:
            f.write(f"{account.name}:{account.password}:{account.safe_cookie()}" + "\n")

def create_account(ch):
    if config["username_method"] == "random":
        username = exrex.getone(config["username_template"])
    elif config["username_method"] == "experimental":
        username = un_gen.get()
                
    password = exrex.getone(config["password_template"])
    resp = requests.post(
        url="https://auth.roblox.com/v2/signup",
        headers={"X-CSRF-TOKEN": ch.proxy.xsrf_token or "-"},
        json=dict(
            username=username,
            password=password,
            gender=choice(config["genders"]),
            referralData=None,
            context="MultiverseSignupForm",
            displayAvatarV2=False,
            displayContextV2=False,
            birthday="%d %s %d" % (randint(10, 28), choice(["Jan", "Feb"]), randint(1990,2005)),
            isTosAgreementBoxChecked=True,
            captchaToken=ch.full_token,
            captchaProvider="PROVIDER_ARKOSE_LABS"
        ),
        proxies=dict(https="https://%s:%d" % (ch.proxy.host, ch.proxy.port))
    )
    if "x-csrf-token" in resp.headers:
        ch.proxy.xsrf_token = resp.headers["x-csrf-token"]
        return create_account(ch)
    data = resp.json()
    for err in data.get("errors", []):
        if err["code"] == 2:
            raise Captcha("%s (%d)" % (err["message"], err["code"]))
        else:
            raise RobloxError("%s (%d)" % (err["message"], err["code"]))
    return CreatedAccount(data["userId"], username, password, resp.cookies[".ROBLOSECURITY"])

class CreatedAccount:
    id: int
    name: str
    password: str
    cookie: str

    def __init__(self, id, name, password, cookie):
        self.id = id
        self.name = name
        self.password = password
        self.cookie = cookie
    
    def __repr__(self):
        return self.name

    def safe_cookie(self):
        return self.cookie.replace("WARNING:", "WARNING")

class TitleWorker(threading.Thread):
    def __init__(self, interval=0.1):
        self.interval = 0.1
        super().__init__()
    
    def run(self):
        while 1:
            time.sleep(self.interval)
            st = solver.success_count+solver.failure_count
            ratio = (solver.success_count/st) * 100 if st else 0
            s = "  |  ".join([
                "Created: %d" % counter.total,
                "CPM: %d" % counter.cpm(),
                "Solve Ratio: %.2f%% (S:%d,F:%d)" % (ratio, solver.success_count, solver.failure_count)
            ])
            ctypes.windll.kernel32.SetConsoleTitleW(s)

class Worker(threading.Thread):
    def __init__(self):
        super().__init__()
    
    def run(self):
        while 1:
            ch = solver.get_solve()

            try:
                account = create_account(ch)
                solver.resubmit_queue.put(ch)
                save_account(account)

            except Captcha:
                print("Captcha token was denied!")
                solver.resubmit_queue.put(ch)

            except RobloxError as err:
                print("Roblox returned error:", err)
                solver.resubmit_queue.put(ch)
            
            except Exception as err:
                print("Error:", err)

## start workers
TitleWorker().start()
for _ in range(config["workers"]):
    Worker().start()
solver.start(config["solvers"], config["resubmitters"])