import time
import random
import base64
from pyDes import *
import hashlib
from urllib import parse

isEncrypted = 1
language = 'zh_CH'
region = 'CN'
timeZone = 'GMT 08:00'
version = '4.0.0'


def encrypt_long(first, web_api=False, env=1):  # 长参数
    """env的值1为uat和线上环境，0为dev和test环境"""
    deliver_key = des_vi = des_key = 0
    if env == 1:
        deliver_key = "Jihewobox15"
        des_vi = "98765432"
        des_key = "jihexxkj"
    elif env == 0:
        deliver_key = "Woyouxinxi666"
        des_vi = "12345678"
        des_key = "wywmxxkj"
    else:
        print(f'encrypt_long函数接受的env值为1或者0，当前env值为【{env}】，请重新输入！')
    time_stamp = int(time.time())
    random_num = random.randint(100000, 999999)
    k = des(des_key, CBC, des_vi, pad=None, padmode=PAD_PKCS5)  # DES加密方法
    first = first.encode()  # pyDes加密处理时，需要encoded strings，不能使用Unicode
    encrypt_str = k.encrypt(first)
    params = base64.b64encode(encrypt_str).decode()  # 字节转换为字符串
    if web_api is True:
        params = parse.quote(params)  # 做urlencode转换，webapi接口需要多做一次转换
    sign = str(params) + str(isEncrypted) + str(time_stamp) + str(random_num) + hashlib.md5(deliver_key.encode(encoding='UTF-8')).hexdigest()
    sign = hashlib.md5(sign.encode(encoding='UTF-8')).hexdigest()  # 转换为16进制
    if env == 1:
        parm = {'isEncrypted': env, 'language': language, 'region': region, 'timeZone': timeZone, 'version': version,
                'timeStamp': time_stamp, 'randomNum': random_num, 'sign': sign, 'params': params}
        return parm
    elif env == 0:
        parm = {'isEncrypted': env, 'lang': 'zh', 'timeZone': timeZone, 'version': version, 'timeStamp': time_stamp,
                'randomNum': random_num, 'sign': sign, 'params': first}
        return parm


# print(encrpyt(r'"{\"deviceInfo\":11}"'))  # kv参数格式示例


def encrypt_params(params, env=1):
    """对params加密处理，env的值1为uat和线上环境，0为dev和test环境"""
    des_vi = des_key = 0
    if env == 1:
        des_vi = "98765432"
        des_key = "jihexxkj"
    elif env == 0:
        des_vi = "12345678"
        des_key = "wywmxxkj"
    else:
        print(f'encrypt_params函数接受的env值为1或者0，当前env值为【{env}】，请重新输入！')
    k = des(des_key, CBC, des_vi, pad=None, padmode=PAD_PKCS5)  # DES加密方法
    params = params.encode()  # pyDes加密处理时，需要encoded strings，不能使用Unicode
    encrypt_str = k.encrypt(params)
    params = base64.b64encode(encrypt_str).decode()  # 字节转换为字符串
    return params


def encrypt_mgt(password, username):
    """mgt登录密码加密处理，用户名与密码为字符串格式，密码以这种加密方式存于数据库中"""
    pwd_key = 'Woyouwaimai76'
    md = hashlib.md5((password+username).encode(encoding='UTF-8')).hexdigest()
    md = hashlib.md5((md+pwd_key).encode()).hexdigest()
    return md

