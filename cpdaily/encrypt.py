# 加密/解密工具类
import json
import math
import random
import base64
from Crypto.Cipher import AES
from pyDes import des, CBC, PAD_PKCS5


# DES加密
def DESEncrypt(s, key='XCE927=='):
    if type(s) == dict:
        s = json.dumps(s)
    iv = b"\x01\x02\x03\x04\x05\x06\x07\x08"
    k = des(key, CBC, iv, pad=None, padmode=PAD_PKCS5)
    encrypt_str = k.encrypt(s)
    return base64.b64encode(encrypt_str).decode()


# DES解密
def DESDecrypt(s, key='XCE927=='):
    s = base64.b64decode(s)
    iv = b"\x01\x02\x03\x04\x05\x06\x07\x08"
    k = des(key, CBC, iv, pad=None, padmode=PAD_PKCS5)
    return k.decrypt(s)


# 获取随机字符串
def getRandomString(length):
    chs = 'ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678'
    result = ''
    for i in range(0, length):
        result += chs[(math.floor(random.random() * len(chs)))]
    return result


# AES加密
def EncryptAES(s, key, iv='1' * 16, charset='utf-8'):
    key = key.encode(charset)
    iv = iv.encode(charset)
    BLOCK_SIZE = 16
    pad = lambda s: (s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * chr(BLOCK_SIZE - len(s) % BLOCK_SIZE))
    raw = pad(s)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(bytes(raw, encoding=charset))
    return str(base64.b64encode(encrypted), charset)


# AES解密
def DecryptAES(s, key, iv='1' * 16, charset='utf-8'):
    key = key.encode(charset)
    iv = iv.encode(charset)
    unpad = lambda s: s[:-ord(s[len(s) - 1:])]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypt = unpad(cipher.decrypt(base64.b64decode(s)))
    return str(decrypt, charset)


# 金智的AES加密过程
def AESEncrypt(data, key):
    return EncryptAES(getRandomString(64) + data, key, key)


# 金智的AES解密过程
def AESDecrypt(data, key):
    return DecryptAES(data, key)[64:]


# form表单BodyString加密
def encrypt_BodyString(text, key=b'SASEoK4Pa5d4SssO'):
    """BodyString加密"""
    iv = b'\x01\x02\x03\x04\x05\x06\x07\x08\t\x01\x02\x03\x04\x05\x06\x07'
    cipher = AES.new(key, AES.MODE_CBC, iv)
    text = json.dumps(text)
    text = pkcs7padding(text)  # 填充
    text = text.encode('utf-8')  # 编码
    text = cipher.encrypt(text)  # 加密
    text = base64.b64encode(text).decode('utf-8')  # Base64编码
    return text


def coordinateOffset(val):
    """坐标微偏移"""
    try:
        val = float(val)
        val += random.uniform(-0.000003, 0.000003)
    except ValueError:
        return None
    return str(round(val, 6))


def pkcs7padding(text: str):
    """明文使用PKCS7填充"""
    remainder = 16 - len(text.encode("utf-8")) % 16
    return str(text + chr(remainder) * remainder)
