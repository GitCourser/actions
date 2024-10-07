# ==============================================================================
# Author       : Courser
# Date         : 2024-07-04 16:50:21
# LastEditTime : 2024-10-07 11:33:19
# Description  : 天翼云盘签到
# ==============================================================================

import re
import rsa
from hashlib import md5
from random import randint
from requests import Session, get
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from time import sleep, time
from sys import path
path.append('..')
from common import runtime, WeChat, ua_mobile, UA, getcfg, isCloud

app = '天翼云盘签到'
apis = [
    'https://m.cloud.189.cn/v2/drawPrizeMarketDetails.action?taskId=TASK_SIGNIN&activityId=ACT_SIGNIN',
    'https://m.cloud.189.cn/v2/drawPrizeMarketDetails.action?taskId=TASK_SIGNIN_PHOTOS&activityId=ACT_SIGNIN',
    'https://m.cloud.189.cn/v2/drawPrizeMarketDetails.action?taskId=TASK_2022_FLDFS_KJ&activityId=ACT_SIGNIN',
]
api_tv = 'http://api.cloud.189.cn/family/manage/exeFamilyUserSign.action'
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
    s = Session()
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

    s.headers.update(
        {
            'User-Agent': UA,
            'Referer': 'https://open.e.189.cn/',
            'lt': lt,
        }
    )
    r = s.post(
        'https://open.e.189.cn/api/logbox/oauth2/loginSubmit.do',
        data={
            'appKey': 'cloud',
            'accountType': '01',
            'userName': f'{{RSA}}{rsa_encode(j_rsakey, phone)}',
            'password': f'{{RSA}}{rsa_encode(j_rsakey, pwd)}',
            'validateCode': '',
            'captchaToken': token,
            'returnUrl': returnUrl,
            'mailSuffix': '@189.cn',
            'paramId': paramId,
        },
    )
    rs = r.json()
    msg += f"\n[{hide_phone(phone)}] {rs['msg']}\n"
    if 'toUrl' in rs:
        s.get(rs['toUrl'])
        # print(r.text)
        return s
    else:
        return


def family(sessionKey):
    # accessToken
    rs = get(
        'https://cloud.189.cn/api/open/oauth2/getAccessTokenBySsKey.action',
        headers={'Appkey': '600100885'},
        params={'sessionKey': sessionKey},
    ).json()
    accessToken = rs['accessToken']

    # 签名
    def get_sign(data):
        e = sorted([f'{k}={v}' for k, v in data.items()])
        sign = md5('&'.join(e).encode()).hexdigest()
        return sign

    # 家庭api
    def family_api(url, params={}):
        t = str(int(time() * 1000))
        data = {
            'Timestamp': t,
            'AccessToken': accessToken,
        }
        data |= params
        headers = {
            'Accept': 'application/json;charset=UTF-8',
            'Sign-Type': '1',
            'Signature': get_sign(data),
            'Timestamp': t,
            'Accesstoken': accessToken,
        }
        rs = get(url, headers=headers, params=params).json()
        # print(rs)
        if params:
            return rs['bonusSpace']
        else:
            return rs['familyInfoResp'][0]['familyId']

    id = family_api('https://api.cloud.189.cn/open/family/manage/getFamilyList.action')
    return family_api('https://api.cloud.189.cn/open/family/manage/exeFamilyUserSign.action', {'familyId': id})


@runtime(app)
def main():
    global msg
    for user in users:
        s = login(user['phone'], user['pwd'])
        if not s:
            continue
        info = ''

        s.mount('https://', HTTPAdapter(max_retries=Retry(total=3, status_forcelist=[500, 502, 503, 504])))
        s.headers.update(
            {
                'Host': 'm.cloud.189.cn',
                'User-Agent': ua_mobile,
                'Referer': 'https://m.cloud.189.cn/zhuanti/2016/sign/index.jsp',
            }
        )

        # 签到
        print('签到')
        rs = s.get('https://api.cloud.189.cn/mkt/userSign.action').json()
        # print(rs)
        if not rs['isSign']:
            info += f"签到获得{rs['netdiskBonus']}M空间\n"
        else:
            msg += f"已签过, 获得{rs['netdiskBonus']}M空间\n"
            # continue

        # 抽奖
        print('抽奖')
        for i, v in enumerate(apis):
            sleep(randint(5, 9))
            rs = s.get(v).json()
            if 'prizeName' in rs:
                info += f"抽奖{i+1}获得{rs['prizeName']}\n"
            else:
                print(i, rs)

        # 家庭云
        print('家庭云')
        s.headers = {'Accept': 'application/json;charset=UTF-8'}
        rs = s.get('https://cloud.189.cn/api/portal/v2/getUserBriefInfo.action').json()
        sessionKey = rs['sessionKey']
        info += f'家庭云签到获得{family(sessionKey)}M空间\n'

        # 计算
        nums = re.findall(r'(\d+)M', info)
        total = sum([int(i) for i in nums])
        info += f'今日共获得{total}M空间\n'

        # 查容量
        print('查容量')
        rs = s.get('https://cloud.189.cn/api/portal/getUserSizeInfo.action').json()
        G = 1024**3
        cloud_total = rs['cloudCapacityInfo']['totalSize'] / G
        cloud_free = rs['cloudCapacityInfo']['freeSize'] / G if rs['cloudCapacityInfo']['freeSize'] > G else 0
        family_total = rs['familyCapacityInfo']['totalSize'] / G
        family_free = rs['familyCapacityInfo']['freeSize'] / G if rs['familyCapacityInfo']['freeSize'] > G else 0
        info += f'个人: {cloud_total:.2f} G, 剩: {cloud_free:.2f} G\n'
        info += f'家庭: {family_total:.2f} G, 剩: {family_free:.2f} G\n'

        msg += info
        sleep(randint(5, 7))

    print(msg)
    if isCloud:
        notify = WeChat()
        notify.send(app, msg)


def run():
    main()


if __name__ == '__main__':
    run()
