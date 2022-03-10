# 工具类集合

import sys
import uuid
import time
import requests
from ruamel.yaml import YAML
from urllib.parse import urlparse
from datetime import datetime, timedelta


yaml = YAML()


# 读取yml配置
def getYmlConfig(yaml_file='config.yml'):
    with open(yaml_file, encoding='utf-8') as f:
        data = f.read()
        config = yaml.load(data)
    return config


# 设置yml配置
def setYmlConfig(data, yaml_file='config1.yml'):
    with open(yaml_file, 'w', encoding='utf-8') as f:
        yaml.dump(data, f)
    log('配置保存成功')


# 输出调试信息，并及时刷新缓冲区
def log(content):
    print(f'{getTimeStr()} {content}')
    sys.stdout.flush()


# 获取当前utc时间，并格式化为北京时间
def getTimeStr():
    utc_dt = datetime.utcnow()
    bj_dt = utc_dt + timedelta(hours=8)
    return bj_dt.strftime("%Y-%m-%d %H:%M:%S")


# 将cookieStr转换为字典
def cookieStrToDict(cookieStr):
    cookies = {}
    for line in cookieStr.split(';'):
        name, value = line.strip().split('=', 1)
        cookies[name] = value
    return cookies


# 获取今日校园api
def getCpdailyApis(user, debug=False):
    apis = {}
    schools = requests.get('https://mobile.campushoy.com/v6/config/guest/tenant/list').json()['data']
    flag = True
    for one in schools:
        if one['name'] == user['school']:
            if one['joinType'] == 'NONE':
                log(user['school'] + ' 未加入今日校园')
                exit(-1)
            flag = False
            params = {'ids': one['id']}
            apis['tenantId'] = one['id']
            res = requests.get('https://mobile.campushoy.com/v6/config/guest/tenant/info', params=params)
            data = res.json()['data'][0]
            joinType = data['joinType']
            idsUrl = data['idsUrl']
            ampUrl = data['ampUrl']
            ampUrl2 = data['ampUrl2']
            if 'campusphere' in ampUrl or 'cpdaily' in ampUrl:
                parse = urlparse(ampUrl)
                host = parse.netloc
                apis['login-url'] = (
                    idsUrl + '/login?service=' + parse.scheme + r"%3A%2F%2F" + host + r'%2Fportal%2Flogin'
                )
                apis['host'] = host
            if 'campusphere' in ampUrl2 or 'cpdaily' in ampUrl2:
                parse = urlparse(ampUrl2)
                host = parse.netloc
                apis['login-url'] = (
                    idsUrl + '/login?service=' + parse.scheme + r"%3A%2F%2F" + host + r'%2Fportal%2Flogin'
                )
                apis['host'] = host
            if joinType == 'NOTCLOUD':
                res = requests.get(apis['login-url'], verify=not debug)
                if urlparse(apis['login-url']).netloc != urlparse(res.url):
                    apis['login-url'] = res.url
            break
    if flag:
        log(user['school'] + ' 未找到该院校信息，请检查是否是学校全称错误')
        exit(-1)
    log(apis)
    return apis


# 全局配置
config = getYmlConfig()
session = requests.session()
user = config['user']
apis = getCpdailyApis(user)
host = apis['host']
deviceID = str(uuid.uuid1())


# 获取MOD_AUTH_CAS
def getModAuthCas(data):
    log('正在获取MOD_AUTH_CAS')
    sessionToken = data['sessionToken']
    headers = {
        'Host': host,
        'Connection': 'keep-alive',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 4.4.4; PCRT00 Build/KTU84P) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/33.0.0.0 Safari/537.36 cpdaily/8.0.8 wisedu/8.0.8',
        'Accept-Encoding': 'gzip,deflate',
        'Accept-Language': 'zh-CN,en-US;q=0.8',
        'X-Requested-With': 'com.wisedu.cpdaily',
    }
    url = f'https://{host}/wec-counselor-collector-apps/stu/mobile/index.html?timestamp={int(time.time() * 1000)}'
    res = session.get(url, headers=headers, allow_redirects=False)
    location = res.headers['location']
    # print(location)
    headers2 = {
        'Host': 'mobile.campushoy.com',
        'Connection': 'keep-alive',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Linux; Android 4.4.4; PCRT00 Build/KTU84P) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/33.0.0.0 Safari/537.36 cpdaily/8.0.8 wisedu/8.0.8',
        'Accept-Encoding': 'gzip,deflate',
        'Accept-Language': 'zh-CN,en-US;q=0.8',
        'Cookie': 'clientType=cpdaily_student; tenantId=' + apis['tenantId'] + '; sessionToken=' + sessionToken,
    }
    res = session.get(location, headers=headers2, allow_redirects=False)
    location = res.headers['location']
    # print(location)
    session.get(location, headers=headers)
    cookies = requests.utils.dict_from_cookiejar(session.cookies)
    if 'MOD_AUTH_CAS' not in cookies:
        log('获取MOD_AUTH_CAS失败')
        exit(-1)
    log('获取MOD_AUTH_CAS成功')
