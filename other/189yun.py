# ==============================================================================
# Author       : Courser
# Date         : 2024-07-04 16:50:21
# LastEditTime : 2024-07-07 13:37:37
# Description  : 天翼云盘签到
# ==============================================================================

import re
import rsa
import requests
from time import sleep
from sys import path
path.append('..')
from common import runtime, WeChat, ua_mobile, UA, getcfg, isCloud

app = '天翼云盘签到'
apis = [
    'https://m.cloud.189.cn/v2/drawPrizeMarketDetails.action?taskId=TASK_SIGNIN&activityId=ACT_SIGNIN',
    'https://m.cloud.189.cn/v2/drawPrizeMarketDetails.action?taskId=TASK_SIGNIN_PHOTOS&activityId=ACT_SIGNIN',
    'https://m.cloud.189.cn/v2/drawPrizeMarketDetails.action?taskId=TASK_2022_FLDFS_KJ&activityId=ACT_SIGNIN',
]
users = getcfg('e_189', 'e_189.cfg')
msg = ''


def hide_phone(phone):
    return f'{phone[:3]}***{phone[-3:]}'


def rsa_encode(j_rsakey, string):
    rsa_key = f'-----BEGIN PUBLIC KEY-----\n{j_rsakey}\n-----END PUBLIC KEY-----'
    pubkey = rsa.PublicKey.load_pkcs1_openssl_pem(rsa_key.encode())
    encrypted = rsa.encrypt(string.encode(), pubkey)
    return encrypted.hex()


def login(phone, pwd):
    global msg
    s = requests.Session()
    r = s.get('https://m.cloud.189.cn/udb/udb_login.jsp?clientType=wap')
    # print(r.text)
    match = re.search(r'https://.+\b', r.text)
    if match:
        url = match.group()
        # print('url:', url)
    else:
        print('没有找到url')
        return

    r = s.get(url)
    # print(r.text)
    # 匹配id为j-tab-login-link的a标签，并捕获href引号内的内容
    match = re.search(r'j-tab-login-link.+?href="(.+?)"', r.text)
    if match:
        href = match.group(1)
        # print('href:', href)
    else:
        print('没有找到href')
        return

    r = s.get(href)
    lt = re.findall(r'lt = "(.+?)"', r.text)[0]
    token = re.findall(r'token=(.+?)&', r.text)[0]
    returnUrl = re.findall(r"returnUrl= '(.+?)'", r.text)[0]
    paramId = re.findall(r'paramId = "(.+?)"', r.text)[0]
    j_rsakey = re.findall(r'j_rsaKey" value="(\S+)"', r.text)[0]

    s.headers.update({
        'User-Agent': UA,
        'Referer': 'https://open.e.189.cn/',
        'lt': lt,
    })
    r = s.post('https://open.e.189.cn/api/logbox/oauth2/loginSubmit.do', data={
        'appKey': 'cloud',
        'accountType': '01',
        'userName': f'{{RSA}}{rsa_encode(j_rsakey, phone)}',
        'password': f'{{RSA}}{rsa_encode(j_rsakey, pwd)}',
        'validateCode': '',
        'captchaToken': token,
        'returnUrl': returnUrl,
        'mailSuffix': '@189.cn',
        'paramId': paramId
    })
    rs = r.json()
    msg += f"\n[{hide_phone(phone)}] {rs['msg']}\n"
    if 'toUrl' in rs:
        s.get(rs['toUrl'])
        # print(r.text)
        return s
    else:
        return


@runtime(app)
def main():
    global msg
    for user in users:
        s = login(user['phone'], user['pwd'])
        if not s:
            continue
        info = ''

        s.headers.update({
            'Host': 'm.cloud.189.cn',
            'User-Agent': ua_mobile,
            'Referer': 'https://m.cloud.189.cn/zhuanti/2016/sign/index.jsp',
        })

        rs = s.get('https://api.cloud.189.cn/mkt/userSign.action').json()
        # print(rs)
        if not rs['isSign']:
            info += f"签到获得{rs['netdiskBonus']}M空间\n"
        else:
            msg += '今日已签过\n'
            continue

        for i, v in enumerate(apis):
            sleep(10)
            rs = s.get(v).json()
            if 'prizeName' in rs:
                info += f"抽奖{i+1}获得{rs['prizeName']}\n"
            else:
                print(i, rs)

        nums = re.findall(r'(\d+)M', info)
        total = sum([int(i) for i in nums])
        info += f'今日共获得{total}M空间\n'
        msg += info
        sleep(10)

    print(msg)
    if isCloud:
        notify = WeChat()
        notify.send(app, msg)


def run():
    main()


if __name__ == '__main__':
    run()
