#!/usr/bin/python3
  
import subprocess
from subprocess import Popen, PIPE
import requests
import json
import urllib.parse
import re
import urllib.request
import sys
from influxdb import InfluxDBClient

#url = 'https://my.ispsystem.com/mancgi/processingmodule'

def read_authfile(path):
    with open(path, 'r') as f:
        return f.read().strip()

def response(url):
    with urllib.request.urlopen(url) as response:
        return response.read()

def getversion(host,panel='vmmgr'):
     stdout, stderr = Popen(['ssh', '-q','-o UserKnownHostsFile=/dev/null ','-o StrictHostKeyChecking=no','-o ConnectTimeout=10', 'root@{}'.format(host), '/usr/local/mgr5/bin/core {} -V'.format(panel)],stdout=PIPE,universal_newlines=True).communicate()
     return stdout

def decreaseLimit(host,elid,lmt,panel='vmmgr'):
     master = host
     stdout, stderr = Popen(['ssh', '-q','-o UserKnownHostsFile=/dev/null ','-o StrictHostKeyChecking=no','-o ConnectTimeout=10', 'root@{}'.format(master), '/usr/local/mgr5/sbin/mgrctl -m {} vmhostnode.edit  elid={} maxvmcount={} sok=ok'.format(panel,elid,lmt)],stdout=PIPE,universal_newlines=True).communicate()
     return stdout

def sendinflux(jdata):
    client = InfluxDBClient('store.firstvds.ru', 8086, 'cron', 'Yuoph2ah', 'clusters')
    return client.write_points(jdata)


if __name__ == '__main__':
    res = response('http://mon.hoztnode.net/inventory.txt')
    outj = json.loads(res)
    nodes = outj['kvmaster'] + outj['vzmaster']
    if len(nodes) < 2:
        sys.exit("Empty list of processingmodules {}".format(nodes))
    tout = 'cron:collectClusterInfoInflux\n'
    for hn in nodes:
        if hn in ["moon.hoztnode.net",]: continue
        if 'jupiter' in hn: continue
        all = 0
        overmem = 0
        overdisk = 0
        available = 0
        blocked = 0
        error = 0
        vdsavailable = 0
        panel = 'vmmgr'
        if hn in outj['vzmaster']: panel= 'vemgr'
        if len(hn) < 3: continue
        output = subprocess.run("ansible all -i '{},' -m shell -a '/usr/local/mgr5/sbin/mgrctl -m {} vmhostnode'".format(hn,panel), shell=True, stdout=subprocess.PIPE,universal_newlines=True) 
        for l in str(output.stdout).split('\n'):
            vls = {}
            for vv in l.strip().split(' '):
                try:
                    n,v = vv.split('=')[:2]
                    vls[n] = v
                except Exception:
                    continue
            if 'name' in vls.keys():
                if ('disabled' in vls.keys()):
                    vls['disabled'] = 1
                    blocked += 1
                else:
                    vls['disabled'] = 0 
                if 'active' in  vls.keys():
                    if vls['active'] == 'off': 
                        vls['disabled'] = 1
                        blocked += 1
                all += 1
                try:
                    if int(vls['meminfo'].split('.')[0]) > 80:
                        overmem += 1
                        print("{} overmem {}".format(vls['name'],vls['meminfo']))
                        if int(vls['maxvmcount']) >= int(vls['countvm']):
                            nlimit = int(vls['countvm']) - 1
                            out = decreaseLimit(hn,vls['id'],nlimit,panel)
                            print(out)
                    if int(vls['storageinfo'].split('.')[0]) > 90:
                        overdisk += 1
                        print("{} overmem {}".format(vls['name'],vls['meminfo']))
                        if panel == 'vmmgr' and int(vls['maxvmcount']) >= int(vls['countvm']):
                            nlimit = int(vls['countvm']) - 1
                            out = decreaseLimit(hn,vls['id'],nlimit,panel)
                            print(out)
                    if panel == 'vmmgr' and int(vls['storageinfo'].split('.')[0]) < 80 and int(vls['meminfo'].split('.')[0]) < 70 and int(vls['maxvmcount']) > 10 and vls['disabled'] == 0:
                        if int(vls['maxvmcount']) == int(vls['countvm']):
                            nlimit = int(vls['countvm']) + 1
                            out = decreaseLimit(hn,vls['id'],nlimit,panel)
                            print(out)
                            tout += '{} UNUSED NODE mem={} store={} vds={}/{}\n'.format(vls['name'],vls['meminfo'],vls['storageinfo'],vls['countvm'],vls['maxvmcount'])
                        if int(vls['maxvmcount']) > int(vls['countvm']):
                            vdsavailable += int(vls['maxvmcount']) - int(vls['countvm'])
                            available += 1
                    if panel == 'vemgr' and int(vls['storageinfo'].split('.')[0]) < 85 and int(vls['meminfo'].split('.')[0]) < 70 and int(vls['maxvmcnt']) > 10 and vls['disabled'] == 0:
                        if int(vls['maxvmcnt']) > int(vls['vmcount']):
                            vdsavailable += int(vls['maxvmcnt']) - int(vls['vmcount'])
                            available += 1
                except KeyError:
                    continue
        json_body = [
        {
            "measurement": "clusters",
            "tags": {
                "cluster": hn,
            },
            "fields": {
                "limitvds": int(vdsavailable),
                'version': getversion(hn,panel),
                'nodescount': all,
                'nodesstoreoversell': overdisk,
                'nodesmemoversell': overmem,
                'nodesavailable': available,
                'nodesblocked': blocked,
                'nodeserror': error,
            }
        }
    ]
        print(json_body)
        print(sendinflux(json_body))
    if len(tout) > 30:
       r = requests.post('http://mon.ispsystem.net/telegram_senderart.py',data={'text':tout})
       if r.status_code > 250:
           print("can't sent telegram data {} {}".format(r,tout))
