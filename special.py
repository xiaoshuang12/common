from common import encrypt
from common.configHttp import post_or_get
import json

code = ''
admin_id = ''
partner_id = ''


def mgt_admin_id(username, password, env=1):
    """
    对mgt平台登录接口做请求会返回adminId，有效期为24小时，对mgt平台下其他接口做请求时，需要传入adminId做校验

    重复请求mgt平台下的登录接口会返回不同的adminId，但在实际业务场景下登录成功后24小时内adminId是固定不变的，
    因此在脚本一次性请求多个mgt接口时，只给出一个固定有效的adminId
    """
    global code, admin_id
    if env not in (0, 1):
        return print(f'env值为1，mgt_admin_id函数访问的是uat及线上环境；'
                     f'env值为0，mgt_admin_id函数访问的是test环境，当前env值为【{env}】!')
    if code == '' or admin_id == '':
        password = encrypt.encrypt_params(password, env)
        resp = post_or_get('post',
                           r'http://uat.webapi.sunmi.com/webapi/sunmisso/web/sunmisso/1.0/',
                           r'service=OAuth.authorizeLogin',
                           f'{{"clientId":"sm5bee3f7394136","userName":"{username}","password":"{password}","type":"1","lang":"CN"}}',
                           env,
                           True)
        try:
            code = resp.json()['data']['code']  # 获取到code值传递到下一个接口
            res = post_or_get('post',
                              r'http://uat.webapi.sunmi.com/webapi/manage/web/manage/1.0/',
                              r'service=Manage.login',
                              f'{{"code":"{code}","adminId":""}}',
                              env,
                              True)
            admin_id = res.json()['data']['uId']  # 获取到adminId值
            return admin_id
        except json.decoder.JSONDecodeError as e:
            print("报错信息如下：\n", e)
    return admin_id


def partner_admin_id(username, password, env=1):
    """
    对partner平台登录接口做请求会返回partner_id，有效期为24小时，对partner平台下其他接口做请求时，需要传入partner_id做校验

    重复请求partner平台下的登录接口会返回不同的partner_id，但在实际业务场景下登录成功后partner_id是固定不变的，
    因此在脚本一次性请求多个partner接口时，只给出一个固定有效的partner_id
    """
    global partner_id
    if env not in (0, 1):
        return print(f'env值为1，partner_admin_id函数访问的是uat及线上环境；'
                     f'env值为0，partner_admin_id函数访问的是test环境，当前env值为【{env}】!')
    if partner_id == '':
        password = encrypt.encrypt_params(password, env)  # des方法加密处理
        res = post_or_get('post',
                          r'http://uat.webapi.sunmi.com/webapi/partners/web/developers/1.2/',
                          r'service=PartnerUser.login',
                          f'{{"userName":"{username}","passWord":"{password}"}}',
                          env,
                          True)
        partner_id = res.json()['data']['dId']
    return partner_id
