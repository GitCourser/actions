# ==============================================================================
# Author       : Courser
# Date         : 2023-05-23 23:36:01
# LastEditTime : 2023-05-31 16:57:30
# Description  : moss签到
# ==============================================================================

import requests
from sys import path
path.append('..')
from common import runtime, WeChat, isCloud, getcfg

app = 'moss签到'
api = 'http://43.154.117.92:82/luomacode-api/'


@runtime(app)
def main():
    msg = ''
    users = getcfg('moss', 'moss.cfg')

    for i in users:
        try:
            resp = requests.post(f'{api}user/login', json=i).json()
            rs = requests.post(f'{api}activity/signin', headers={'token': resp['loginToken']}).json()
            msg += rs['msg']
        except Exception as e:
            msg += repr(e)
        msg += '\n'

    print(msg)
    if isCloud:
        notify = WeChat()
        notify.send(app, msg)


def run():
    main()


if __name__ == '__main__':
    run()
