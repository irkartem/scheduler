#!/usr/bin/python3
# collect nodes data
import subprocess
from subprocess import Popen, PIPE
import requests
import json
import urllib.parse
import urllib.request
import sys
from influxdb import InfluxDBClient

# url = 'https://my.ispsystem.com/mancgi/processingmodule'


def read_authfile(path):
    with open(path, 'r') as f:
        return f.read().strip()


def response(url):
    with urllib.request.urlopen(url) as response:
        return response.read()


def getversion(host, panel='vmmgr'):
    stdout, stderr = Popen(['ssh', '-q', '-o UserKnownHostsFile=/dev/null ', '-o StrictHostKeyChecking=no', '-o ConnectTimeout=10',
                           'root@{}'.format(host), '/usr/local/mgr5/bin/core {} -V'.format(panel)], stdout=PIPE, universal_newlines=True).communicate()
    return stdout


def decreaseLimit(host, elid, lmt, panel='vmmgr'):
    master = host
    stdout, stderr = Popen(['ssh', '-q', '-o UserKnownHostsFile=/dev/null ', '-o StrictHostKeyChecking=no', '-o ConnectTimeout=10', 'root@{}'.format(master),
                           '/usr/local/mgr5/sbin/mgrctl -m {} vmhostnode.edit  elid={} maxvmcount={} sok=ok'.format(panel, elid, lmt)], stdout=PIPE, universal_newlines=True).communicate()
    return stdout


def sendinflux(jdata):
    client = InfluxDBClient('store.firstvds.ru', 8086,
                            'cron', 'Yuoph2ah', 'clusters')
    return client.write_points(jdata)


if __name__ == '__main__':
    res = response('http://mon.hoztnode.net/inventory.txt')
    outj = json.loads(res)
    nodes = outj['kvnode'] + outj['vznode']
    if len(nodes) < 2:
        sys.exit("Empty list of processingmodules {}".format(nodes))
    tout = 'cron:checkDdSpeed\n'
    for hn in nodes:
        if len(hn) < 3:
            continue
        if hn in ["moon.hoztnode.net", ]:
            continue
        if 'jupiter' in hn:
            continue
        panel = 'vm'
        if hn in outj['vzmaster']:
            panel = 'vz'
        output = subprocess.run("ansible all -f 30  -i '{},' -m shell -a 'dd if=/dev/zero of=/{}/test bs=64k count=16k conv=fdatasync '".format(
            hn, panel), shell=True, stdout=subprocess.PIPE, universal_newlines=True)
        for l in str(output.stdout).split('\n'):
            if "MB" in l:
                print(l)
                tray = l.replace(',', '.').split()
                print(tray)
        try:
            sp = tray[-2].split('.')[0]
            json_body = [{"measurement": "nodeDdspeed", "tags": {"nodename": hn, },
                          "fields": {"ddspeed": int(sp)}}]
            print(json_body)
            print(sendinflux(json_body))
        except IndexError:
            print('Json format error for {}'.format(hn))
            continue
