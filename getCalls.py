#!/usr/bin/python3
# collect nodes data
import requests

def read_authfile(path):
    with open(path, 'r') as f:
        return f.read().strip()


ps = read_authfile('/opt/auth/asterisk')
out = requests.get('http://asterisk.ispsystem.net/triple.txt', auth=('cron', ps))

print(out.text)
