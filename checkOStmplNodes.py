#!/usr/bin/python3

import subprocess
from subprocess import Popen, PIPE
import requests
import json


vzdict = {}
kvdict = {}
kvmdict = {}
fout = ''
with open('/opt/db/vztempl', 'r') as vzconf:
    for line in vzconf:
        k,v = line.strip().split(' ')[:2]
        vzdict[k] = v

with open('/opt/db/kvtempl', 'r') as vzconf:
    for line in vzconf:
        k,v = line.strip().split(' ')[:2]
        kvdict[k] = v
with open('/opt/db/kvntempl', 'r') as vzconf:
    for line in vzconf:
        k,v = line.strip().split(' ')[:2]
        kvmdict[k] = v
output = subprocess.run("ansible vznode -i /opt/ansible/inventory.py -m shell -a '/opt/listOStmp.py'", shell=True, stdout=subprocess.PIPE,universal_newlines=True) 
for l in str(output.stdout).split('\n'):
    if 'SUCCESS' in l: continue
    if 'FAILED' in l:
        name = l.split(' ')[0]
        print("can't login {}\n".format(name))
        fout = "{} can't login {}\n".format(fout,name)
    try:
        name,osname,ver = l.strip().split(' ')[:3]
    except Exception:
        if len(l) > 3:
            print("Bad Line:{}\n".format(l))
    if (osname not in vzdict.keys()):
        print ("New TMPL {} {} {}\n".format(name,osname,ver))
    if (osname in vzdict.keys()) and (vzdict[osname] != ver):
        print ("wrong TMPL {} {} {}".format(name,osname,ver))
        print ("wrong TMPL {} {} {}\n".format(name,osname,vzdict[osname]))

output = subprocess.run("ansible kvnode -i /opt/ansible/inventory.py -m shell -a '/opt/listOStmp.py'", shell=True, stdout=subprocess.PIPE,universal_newlines=True) 
for l in str(output.stdout).split('\n'):
    chk = kvdict
    if "neptune" in l or "moon" in l or "isp-vm" in l or "ndr" in l: continue
    if 'bitrix' in l: continue
    if "kvm" in l or "wkvm" in l:
        chk = kvmdict
    if 'SUCCESS' in l: continue
    if 'FAILED' in l:
        name = l.split(' ')[0]
        print("can't login {}\n".format(name))
        fout = "{} can't login {}\n".format(fout,name)
    try:
        name,osname,ver = l.strip().split(' ')[:3]
    except Exception:
        if len(l) > 3:
            print("Bad Line:{}\n".format(l))
    if (osname not in chk.keys()):
        print ("New TMPL {} {} {}\n".format(name,osname,ver))
    if (osname in chk.keys()) and (chk[osname] != ver):
        print ("wrong TMPL {} {} {}".format(name,osname,ver))
        print ("wrong TMPL {} {} {}\n".format(name,osname,chk[osname]))



print(fout)

