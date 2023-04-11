# ==============================================================================
# Author       : Courser
# Date         : 2023-03-18 16:15:01
# LastEditTime : 2023-04-03 19:59:11
# Description  : 阿里云盘签到
# ==============================================================================

from sys import path
from time import sleep
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

path.append('..')
from common import runtime, WeChat, getcfg, setcfg, isCloud

app = '阿里云盘签到'


class SignIn:
    def __init__(self, refresh_token, is_reward=False):
        """签到类

        Args:
            refresh_token (str): 云盘token
            is_reward (bool, optional): 是否当天领取奖励, 默认为否.
        """
        self.refresh_token = refresh_token
        self.is_reward = is_reward
        self.hide_refresh_token = self._hide_refresh_token()
        self.new_token = ''
        self.s = Session()
        self.s.mount('https://', HTTPAdapter(max_retries=Retry(total=3, allowed_methods=['POST'])))
        self.s.headers = {'Accept-Encoding': 'gzip, deflate'}

    def _hide_refresh_token(self):
        """隐藏 refresh_token"""
        return self.refresh_token[:4] + '*' * len(self.refresh_token[4:-4]) + self.refresh_token[-4:]

    def _get_access_token(self):
        """获取 access_token"""
        data = self.s.post(
            'https://auth.aliyundrive.com/v2/account/token',
            json={'grant_type': 'refresh_token', 'refresh_token': self.refresh_token},
        ).json()
        # print(data)

        if 'code' in data and data['code'] in ['RefreshTokenExpired', 'InvalidParameter.RefreshToken']:
            self.error = f'[{self.hide_refresh_token}] 获取 access token 失败, 可能是 refresh token 无效.'
            return

        try:
            self.nick_name = data['nick_name'] if data['nick_name'] else data['user_name']
            self.access_token = data['access_token']
            self.new_token = data['refresh_token']
        except KeyError:
            self.error = f'[{self.hide_refresh_token}] 获取 access token 失败, 参数缺失: {data}'
            return

        return True

    def _sign_in(self):
        """签到"""
        api = 'https://member.aliyundrive.com/v1/activity/'
        self.s.headers |= {'Authorization': f'Bearer {self.access_token}'}
        self.s.params = {'_rx-s': 'mobile'}
        data = self.s.post(f'{api}sign_in_list', json={'isReward': False}).json()
        # print(data)

        if data['code'] == 'AccessTokenInvalid':
            self.error = f'[{self.nick_name}] AccessTokenInvalid, 重试一次.'
            return

        if 'success' not in data:
            return f'[{self.nick_name}] 签到失败:\n{data}'

        count = data['result']['signInCount']  # 签到天数
        days = len(data['result']['signInLogs'])  # 本月总天数

        if self.is_reward:
            # 当天领奖
            data = self.s.post(f'{api}sign_in_reward', json={'signInDay': count}).json()
            # print(data)
            try:
                reward = f'''\n今日获得: {data['result']['name']} {data['result']['description']}'''
            except Exception:
                reward = '\n无奖励'
        else:
            # 月底领奖
            if count == days:
                foo = []
                for i in range(1, days + 1):
                    data = self.s.post(f'{api}sign_in_reward', json={'signInDay': i}).json()
                    try:
                        foo.append(data['result']['notice'])
                    except Exception:
                        pass
                    sleep(1)
                bar = '\n'.join(foo)
                reward = f'\n本月奖励已全部领取.\n{bar}'
            # 只签不领
            else:
                reward = '\n今日暂不领奖'

        return f'[{self.nick_name}] 签到成功, 本月累计签到 {count} 天{reward}'

    def run(self):
        """入口"""
        return {
            'msg': self._sign_in() if self._get_access_token() else self.error,
            'token': self.new_token or self.refresh_token,
        }


@runtime(app)
def main():
    result = []
    users = getcfg('ALIYUN', 'aliyun.cfg')
    for i in users:
        foo = SignIn(i).run()
        if '重试一次' in foo['msg']:
            foo = SignIn(i).run()
        result.append(foo)

    msg = '\n\n'.join([i['msg'] for i in result])
    token = '\n'.join([i['token'] for i in result])

    try:
        if isCloud:
            from github import put_secret

            msg += '\n\n' + put_secret('ALIYUN', token)
            print(msg)
            WeChat().send(app, msg)
        else:
            print(f'{msg}\n\n{token}')
            setcfg('aliyun.cfg', token)
    except Exception:
        pass


def run():
    main()


if __name__ == '__main__':
    main()
