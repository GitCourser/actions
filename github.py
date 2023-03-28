# ==============================================================================
# Author       : Courser
# Date         : 2023-03-27 19:43:04
# LastEditTime : 2023-03-28 19:34:53
# Description  : 操作 GitHub Secrets
# ==============================================================================

from os import environ
from base64 import b64encode
from requests import Session
from nacl import encoding, public

repos = environ['GITHUB_REPOS']
token = environ['PUBLIC_REPO_TOKEN']
api = f'https://api.github.com/repos/{repos}/actions/secrets/'
headers = {
    'Accept': 'application/vnd.github+json',
    'Authorization': f'Bearer {token}',
    'X-GitHub-Api-Version': '2022-11-28',
}


def encrypt(public_key, secret_value):
    """
    Encrypt a Unicode string using the public key.

    :param public_key: The public key to use for encryption.
    :param secret_value: The secret value to encrypt.
    :return: The encrypted secret value.
    """
    public_key = public.PublicKey(public_key.encode('utf-8'), encoding.Base64Encoder)
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode('utf-8'))
    return b64encode(encrypted).decode('utf-8')


def get_key(s):
    """获取 repo 公钥"""
    r = s.get(f'{api}public-key').json()
    return r['key'], r['key_id']


def get_secret(name: str):
    """获取 secret

    Args:
        name (str): secret 名称
    """

    with Session() as s:
        s.headers = headers
        r = s.get(f'{api}{name}').json()
        print(r)


def put_secret(name: str, value: str):
    """创建或更新 secret

    Args:
        name (str): secret 名称
        value (str): secret 值

    Returns:
        str: 更新结果
    """

    with Session() as s:
        s.headers = headers
        try:
            key, key_id = get_key(s)
        except KeyError:
            return 'github token 错误'
        r = s.put(f'{api}{name}', json={'encrypted_value': encrypt(key, value), 'key_id': key_id})
        if r.status_code == 204:
            return f'更新 {name} 成功'
        elif r.status_code == 201:
            return f'创建 {name} 成功'
        else:
            return f'更新 {name} 失败. {r.status_code}'
