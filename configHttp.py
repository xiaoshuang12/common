import requests
import readConfig
from common import encrypt
from common import common
import ast

localReadConfig = readConfig.ReadConfig()

scheme = localReadConfig.get_http("scheme")
port = localReadConfig.get_http("port")
timeout = localReadConfig.get_http("timeout")
web_header = localReadConfig.get_webheader()
app_header = localReadConfig.get_appheader()

headers = {}
params = {}
data = {}
files = {}

method_get = "get"
method_post = "post"


def full_url(url):
    if "http://" not in url:
        url = "http://" + url
    return url


def env_url(url, env=1):
    """不同测试环境下url修改，1为uat，0为test，2为release"""
    url = full_url(url)
    list_url = url.split('.', 1)
    if env == 0:  # test环境
        if 'uat' in list_url[0]:
            list_url[0] = list_url[0][:-3] + 'test'
        elif 'api' in list_url[0] or 'webapi' in list_url[0]:
            list_url[0] = list_url[0][:7] + 'test.' + list_url[0][7:]
        url = '.'.join(list_url)
    elif env == 1:  # uat环境
        if 'test' in list_url[0]:
            list_url[0] = list_url[0].replace('test', 'uat')
        elif 'api' in list_url[0] or 'webapi' in list_url[0]:
            list_url[0] = list_url[0][:7] + 'uat.' + list_url[0][7:]
        url = '.'.join(list_url)
    elif env == 2:  # 线上环境
        if 'uat' in list_url[0]:
            list_url[0] = list_url[0].replace('uat', '')
        elif 'test' in list_url[0]:
            list_url[0] = list_url[0].replace('test', '')
        url = list_url[0] + list_url[1]
    elif env == 3:  # 原始url
        url = url
    return url


def get(url, param, env=1):
    if "webapi" in url:
        headers_one = web_header
    else:
        headers_one = app_header
    try:
        resp = requests.get(url=env_url(url, env=env), headers=headers_one, params=param, timeout=float(timeout))
        # resp.raise_for_status()
        return resp
    except TimeoutError:
        print("Time out!")
        return None


def post(url, param, post_data, env=1, is_encrypt=True):
    """不同测试环境下post请求，1为uat，0为test，2为release，默认为uat环境，默认为加密状态"""
    url = env_url(url, env)  # 补全url，并将url修改为对应环境下的地址
    if "webapi" in url.split('/')[2]:
        header_one = web_header
    else:
        header_one = app_header
    try:
        if env == 0:  # test环境无加密处理
            post_data = ast.literal_eval(post_data)  # 将str转化为dict（字典）类型
            # post_data = encrypt.encrypt_long(post_data, False, env)  # test环境加密
        elif env == 1:  # uat环境
            if is_encrypt is True:
                if 'webapi' in url.split('/')[2]:  # 服务器地址中包含'webapi'
                    post_data = encrypt.encrypt_long(post_data, True)  # 原始参数加密处理
                else:
                    post_data = encrypt.encrypt_long(post_data, False)
            else:
                post_data = ast.literal_eval(post_data)
        elif env == 2:  # 线上环境加密处理
            if 'webapi' in url.split('/')[2]:
                post_data = encrypt.encrypt_long(post_data, True)  # 原始参数加密处理
            else:
                post_data = encrypt.encrypt_long(post_data, False)
        elif env == 3:  # 不修改url，按照url中的地址决定是否对参数post_data做加密
            list_url = url.split('.', 1)
            if is_encrypt is True and 'uat' in list_url[0] or list_url[1][:5] == 'sunmi':
                if 'webapi' in url.split('/')[2]:
                    post_data = encrypt.encrypt_long(post_data, True)  # 原始参数加密处理
                else:
                    post_data = encrypt.encrypt_long(post_data, False)
            else:
                post_data = ast.literal_eval(post_data)
        resp = requests.post(url=url, headers=header_one, params=param, data=post_data, timeout=float(timeout))
        return resp
    except TimeoutError:
        print("Time out!")
        return None
    except BaseException as e:
        print(f"报错信息：\n【{e}】")


def post_or_get(method, url, param, old_data=None, env=1, is_encrypt=True):
    """不同测试环境下post请求，1为uat，0为test，2为release，默认为uat环境，默认为加密"""
    if method == 'get':
        resp = get(url=url, param=param, env=env)
    elif method == 'post':
        resp = post(url=url, param=param, post_data=old_data, env=env, is_encrypt=is_encrypt)
    else:
        return print('请使用post或者get请求方法，并填写正确的名称')
        # self.assertIn(method, ['get', 'post'], "请使用post或者get请求参数，并填写正确的请求方法名称")
    if resp is not None:
        resp.encoding = resp.apparent_encoding  # 将返回结果的编码方式与真实的返回结果编码方式保持一致
    return resp


# include upload file
def postWithFile(url, headers, files, data):  # web端文件上传
    weburl = scheme + '://' + url
    try:
        resp = requests.post(url=weburl, headers=headers, data=data, files=files, timeout=float(timeout))
        return resp
    except TimeoutError:
        print("Time out!")
        return None
