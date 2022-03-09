# ==============================================================================
# Author       : Courser
# Date         : 2022-01-29 21:08:26
# LastEditTime : 2022-03-09 23:22:06
# Description  : 机场签到
# ==============================================================================

import re
import time
import requests
import sys
import subprocess
import platform

sys.path.append('..')
from common import runtime, UA, WeChat, getcfg, isCloud

app = '机场签到'
notify = WeChat()

s = requests.session()
s.headers = {
    'Accept-Encoding': 'gzip, deflate',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'User-Agent': UA,
}


def SignIn(url):
    url += '/user/checkin'
    response = s.post(url)
    if response.status_code != 200:
        time.sleep(1)
        SignIn(url)
    rs = response.json()
    # {'ret': 0, 'msg': '您似乎已经签到过了...'}
    # {'msg': '获得了 90 MB流量.', 'unflowtraffic': 2412773376, 'traffic': '2.25GB', 'trafficInfo': {'todayUsedTraffic': '0B', 'lastUsedTraffic': '1.75MB', 'unUsedTraffic': '2.25GB'}, 'ret': 1}
    msg = rs['msg']
    if rs['ret'] == 1:
        msg += '，剩余流量：' + rs['traffic']
    return msg


def login(url, user, passwd):
    url += '/auth/login'
    data = f'email={user}&passwd={passwd}&code='
    response = s.post(url, data=data)
    if response.status_code != 200:
        time.sleep(1)
        login(url, user, passwd)
    # {'ret':1,'msg':'登录成功'}
    return response.json()['msg']


def Ping(host):
    if platform.system() == 'Windows':
        try:
            ping = subprocess.Popen(f'ping -n 1 {host}', stdout=subprocess.PIPE, encoding='gbk', shell=True)
            ping.wait()
            lines = ping.stdout.readlines()
            D = str([line for line in lines])
            pat = re.compile('平均' + '(.*?)' + 'ms', re.S)
            result = pat.findall(D)
            return str(result[0]).replace(' ', '').replace('=', '')
            # 数据包: 已发送 = 1，已接收 = 0，丢失 = 1 (100% 丢失)，\n
        except BaseException:
            return -1
    elif platform.system() == 'Linux':
        try:
            p = subprocess.Popen(f'ping -c 1 {host}', stdout=subprocess.PIPE, encoding='gbk', shell=True)
            out = p.stdout.read()
            pat = re.compile('time=' + '(.*?)' + ' ms', re.S)
            result = pat.findall(out)
            return result[0]
        except BaseException:
            return -1


@runtime(app)
def main():
    airport = getcfg('airport', 'airport.cfg')
    Feedback = '共计' + str(len(airport['site'])) + '个站点需签到\n'
    for i in airport['site']:
        print('开始计算最快的服务器...')
        U = [{}] * len(i['url'])
        for j, k in enumerate(i['url']):
            ms = Ping(str(k).replace('http://', '').replace('https://', ''))
            U[j] = {'ms': int(ms), 'url': k}
        U.sort(key=lambda x: x['ms'])
        print(U)
        for j in U:
            if j['ms'] != -1:
                url = j['url']
                break
        print('最快的服务器为：' + url)
        try:
            foo = login(url, i['email'], i['password'])
            if foo != '登录成功':
                print('登录失败:', foo)
                continue
            case = SignIn(url)
            Feedback += i['note'] + '：' + case + '\n'
        except Exception:
            Feedback += i['note'] + '：出错\n'
    print(Feedback)

    if isCloud:
        notify.send(app, Feedback)


def run():
    main()


if __name__ == '__main__':
    run()
