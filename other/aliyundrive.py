# ==============================================================================
# Author       : Courser
# Date         : 2023-03-18 16:15:01
# LastEditTime : 2023-03-28 19:40:38
# Description  : 阿里云盘签到
# ==============================================================================

import requests
from sys import path

path.append('..')
from common import runtime, WeChat, getcfg, setcfg, isCloud
from github import put_secret

app = '阿里云盘签到'


class SignIn:
    def __init__(self, refresh_token):
        """签到类

        Args:
            refresh_token (str): 云盘token
        """
        self.refresh_token = refresh_token
        self.hide_refresh_token = self._hide_refresh_token()
        self.new_token = ''

    def _hide_refresh_token(self):
        """隐藏 refresh_token"""
        return self.refresh_token[:4] + '*' * len(self.refresh_token[4:-4]) + self.refresh_token[-4:]

    def _get_access_token(self):
        """获取 access_token"""
        data = requests.post(
            'https://auth.aliyundrive.com/v2/account/token',
            json={'grant_type': 'refresh_token', 'refresh_token': self.refresh_token},
        ).json()
        # print(data)

        if 'code' in data and data['code'] in ['RefreshTokenExpired', 'InvalidParameter.RefreshToken']:
            self.error = f'[{self.hide_refresh_token}] 获取 access token 失败, 可能是 refresh token 无效.'
            return

        try:
            self.nick_name = data['nick_name']
            self.access_token = data['access_token']
            self.new_token = data['refresh_token']
        except KeyError:
            self.error = f'[{self.hide_refresh_token}] 获取 access token 失败, 参数缺失: {data}'
            return

        return True

    def _sign_in(self):
        """签到"""
        data = requests.post(
            'https://member.aliyundrive.com/v1/activity/sign_in_list',
            params={'_rx-s': 'mobile'},
            headers={'Authorization': f'Bearer {self.access_token}'},
            json={'isReward': True},
        ).json()
        # print(data)

        if 'success' not in data:
            self.error = f'[{self.nick_name}] 签到失败, 错误信息: {data}'
            return

        current_day = None
        for i, day in enumerate(data['result']['signInLogs']):
            if day['status'] == 'miss':
                current_day = data['result']['signInLogs'][i - 1]
                break

        reward = (
            '\n无奖励'
            if not current_day['isReward']
            else f'''\n今日获得: {current_day['reward']['name']} {current_day['reward']['description']}'''
        )

        count = data['result']['signInCount']

        return f'[{self.nick_name}] 签到成功, 本月累计签到 {count} 天{reward}' if count else f'[{self.nick_name}] 签到失败'

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
        result.append(SignIn(i).run())

    msg = '\n\n'.join([i['msg'] for i in result])
    token = '\n'.join([i['token'] for i in result])

    try:
        if isCloud:
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
