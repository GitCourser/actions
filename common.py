# ==============================================================================
# Author       : Courser
# Date         : 2020-12-29 22:56:15
# LastEditTime : 2022-01-05 22:45:53
# Description  : 脚本公共库
# ==============================================================================

"""脚本公共库"""

import json
import time
import requests
from datetime import datetime, timedelta  # , timezone
from os import environ, path
from functools import wraps

dirpath = path.dirname(__file__)
ua_mobile = 'Mozilla/5.0 (Linux; Android 11; M2012K11AC Build/RKQ1.200826.002; wv)'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36'
isCloud = environ.get('GITHUB_ACTIONS')


def getcfg(var, file):
    """读取环境变量或者配置文件"""
    filepath = path.join(dirpath, 'config', file)
    if var in environ:
        cfg = environ[var]
    elif path.isfile(filepath):
        with open(filepath, 'r') as f:
            cfg = f.read()
    else:
        print(f'无 {var} 或配置文件')
        return
    try:
        return json.loads(cfg)
    except Exception:
        return cfg.split()


def setcfg(file, cfg):
    """写入配置文件"""
    filepath = path.join(dirpath, 'config', file)
    with open(filepath, 'w') as f:
        f.write(cfg)


class WeChat:
    """企业微信模块"""
    def __init__(self):
        datacfg = getcfg('WX_CFG', 'wx.cfg')
        self.corpid = datacfg['corpid']  # 企业ID，在管理后台获取
        self.secret = datacfg['secret']  # 自建应用的Secret，每个自建应用里都有单独的secret
        self.agentid = datacfg['agentid']  # 应用ID，在后台应用中获取
        self.touser = datacfg['touser']  # 接收者用户名,多个用户用|分割
        self.api = 'https://qyapi.weixin.qq.com/cgi-bin/'

    def _get_access_token(self):
        """获取access_token"""
        url = f'{self.api}gettoken'
        params = {
            'corpid': self.corpid,
            'corpsecret': self.secret,
        }
        response = requests.get(url, params)
        result = response.json()
        return result['access_token']

    def get_access_token(self):
        """获取并保存access_token"""
        try:
            with open('access_token.conf', 'r') as f:
                t, access_token = f.read().split()
        except Exception:
            with open('access_token.conf', 'w') as f:
                access_token = self._get_access_token()
                cur_time = time.time()
                f.write('\t'.join([str(cur_time), access_token]))
                return access_token
        else:
            cur_time = time.time()
            if 0 < cur_time - float(t) < 7200:
                return access_token
            else:
                with open('access_token.conf', 'w') as f:
                    access_token = self._get_access_token()
                    f.write('\t'.join([str(cur_time), access_token]))
                    return access_token

    def send(self, title, content):
        msg = f'''🔔 {title}\n⏲ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{'——' * 7}\n{content}'''
        token = self.get_access_token() if isCloud else self._get_access_token()
        url = f'{self.api}message/send?access_token={token}'
        data = {
            'touser': self.touser,
            'msgtype': 'text',
            'agentid': self.agentid,
            'text': {'content': msg}
        }
        response = requests.post(url, json.dumps(data))
        result = response.json()
        if result['errmsg'] == 'ok':
            print('消息发送成功')
        else:
            print(result)


class Gotify:
    """Gotify消息通知"""
    def __init__(self):
        try:
            datacfg = getcfg('GOTIFY_CFG', 'gotify.cfg')
            self.api = datacfg['api']
            self.token_info = datacfg['info']
            self.token_warn = datacfg['warn']
            self.token_error = datacfg['error']
        except Exception:
            print('Gotify配置错误')
            return

    def send(self, title, message, mode='info'):
        """发送markdown消息

        Args:
            title (str): 标题
            message (str): 消息内容
            mode (str): info, warn, error
        """
        message = message.replace('\n', '  \n')
        # print(message)
        if mode == 'info':
            token = self.token_info
        elif mode == 'warn':
            token = self.token_warn
        else:
            token = self.token_error

        headers = {
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/json'
        }
        data = {
            'title': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'message': f'## {title}\n{message}',
            'extras': {
                'client::display': {
                    'contentType': 'text/markdown'
                }
            },
        }
        response = requests.post(self.api, headers=headers, params={'token': token}, json=data)
        if response.status_code == 200:
            print('消息发送成功')
        else:
            print('消息发送失败', response.status_code)

    def send_tab(self, title, table, message='', mode='info'):
        """发送表格消息

        Args:
            title (str): 标题
            table (list): 表格列表
            message (str, 可选): 表格外文字内容.
            mode (str): info, warn, error
        """
        if message:
            message += '\n\n'
        message += '|'.join(table[0]) + '\n' + (len(table[0]) * ':-:|')[:-1] + '\n'
        for row in table[1:]:
            message += '|'.join(row) + '\n'
        # print(message)
        self.send(title, message, mode)


class runtime:
    """运行并计时"""
    def __init__(self, title=''):
        self.title = title

    def __call__(self, func):
        @wraps(func)
        def inner(*args, **kwargs):
            symbol = '-' * 10
            print(f'''🔔【{self.title}】开始\n{symbol} {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {symbol}\n''')
            start = time.perf_counter()
            ret = func(*args, **kwargs)
            end = time.perf_counter()
            symbol = '-' * 41
            print(f'\n{symbol}\n🔔【{self.title}】结束 ⏱{round(end - start, 3)}秒')
            return ret
        return inner
