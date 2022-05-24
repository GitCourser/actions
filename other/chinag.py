# ==============================================================================
# Author       : Courser
# Date         : 2021-08-10 23:28:35
# LastEditTime : 2022-05-24 23:05:18
# Description  : ChinaG 签到
# ==============================================================================

import sys
import requests
sys.path.append('..')
from common import runtime, isCloud, WeChat, getcfg

app = 'ChinaG 签到'
# api = 'http://j01.best/'
api = 'http://a.luxury/'
headers = {
    'Accept-Encoding': 'gzip, deflate',
    'Content-Type': 'application/json;charset=UTF-8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
}
data = getcfg('chinag', 'chinag.cfg')


@runtime(app)
def main():
    s = requests.Session()
    s.headers = headers

    # 登录
    msg = s.post(f'{api}signin', json=data).json()['msg']

    # 签到
    if msg == '登录成功(如果登陆死循环，请切换服务器)':
        r = s.post(f'{api}user/checkin').json()
        msg = r['msg']
        if msg != '您似乎已经签到过了...':
            msg += f'''\n剩余流量: {r['traffic']}'''
    print(msg)

    # 通知
    if isCloud:
        notify = WeChat()
        notify.send(app, msg)


def run():
    main()


if __name__ == '__main__':
    run()
