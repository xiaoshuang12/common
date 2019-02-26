
import os
import json
import xlrd
from datetime import datetime
import traceback
import csv
import paramiko
from readConfig import ReadConfig
from common import configHttp
import re
import pymysql
from common.special import mgt_admin_id as mgt
from common.special import partner_admin_id as partner


linux_host = ReadConfig().get_linux_dir("host")
linux_port = ReadConfig().get_linux_dir('port')
linux_username = ReadConfig().get_linux_dir('username')
linux_password = ReadConfig().get_linux_dir('password')
linux_dir = ReadConfig().get_linux_dir('dir')

script_folder = ReadConfig().get_case("script_folder")
case_folder_name = ReadConfig().get_case('test_case_folder')
case_file = ReadConfig().get_case("filename")
case_file_sheet = ReadConfig().get_case("sheet")


def who_am_i():
    """在自定义函数内部获取当前函数的名称，此名称无类型"""
    return traceback.extract_stack()[-2][2]


def listdir(path, list_name, file_type):
    """筛选出某个路径（path）下特定类型（file_type）文件（不包括其子目录），并将所有此类型文件的路径放在一个列表中"""
    for file in os.listdir(path):
        file_path = os.path.join(path, file)
        if os.path.splitext(file_path)[1] == file_type:
            list_name.append(file_path)
    return list_name


# def listdir(path, list_name, file_type):
#     """筛选出某个路径（path）下特定类型（file_type）文件（包括其子目录），并将所有此类型文件的路径放在一个列表中"""
#     for file in os.listdir(path):
#         file_path = os.path.join(path, file)
#         if os.path.isdir(file_path):
#             listdir(file_path, list_name)
#         elif os.path.splitext(file_path)[1]==file_type:
#             list_name.append(file_path)


def read_csv(file_path):
    """
    输出csv文件中的所有的数据，格式为首行做key，从第二行开始做value，生成列表
    格式如下：[[(key,value), (key,value), (key,value)], [(key,value), (key,value), (key,value)]]，下面是具体例子
    OrderedDict([('versionName', '1.0.0'), ('versionCode', '41'), ('machineModel', 'V1s-G'), ('msn', 'VS0517CM00667')])
     类型
     <class 'collections.OrderedDict'>
    """
    csv_file = open(file_path, 'r', encoding='utf-8')
    data = csv.DictReader(csv_file)
    rows = [row for row in data]
    csv_file.close()
    return rows


# ************************************** case参数文件处理 ******************************************

def response_deal(data):
    """
    在excel表格单元格格式为整数时，【小数点后值为0的浮点数】与【整数】写法一致，都显示为整数形式，即1.00与1都显示为整数1
    读取后实际为浮点数，即单元格格式为整数时数字都以浮点数类型存储，经过下面get_case函数读取后，【小数点后值为0的浮点数】转换为整数

    如果请求响应结果断言值为【小数点后值为0的浮点数】，则需要将其转换为整数类型。这样导致的结果是正真浮点数断言验证不严谨，需知悉！
    现有接口暂时无浮点型数字返回，为防止此情况出现，对【小数点后值为0的浮点数】做整数处理
    """
    # if type(data) is float and data % 1 == 0:  # 浮点数x.0，x.00，-x.000等等浮点数存储为x.0，而x.x000存储为x.x
    #     data = int(data)
    data = str(data)  # 将响应结果及case验证value都转化为字符型
    data = data.replace('\'', '\"')
    return data


def resp_result(res):
    """响应结果response处理"""
    if res is not None:
        res = eval('res.text')
    return res


def data_deal(data):
    """
    在字符串中有反斜线的地方多加一个反斜线，例如'\\abv\\\\\ab\e\'变为'\\abv\\\\\\ab\\e\\'
    此方法暂未使用
    """
    one = []
    fish = []
    for n in range(len(data)):  # 索引号
        if data[n] == "\\":
            one.append(n)
    new_list = one + [0]
    for i in range(len(one)):
        if new_list[i] + 1 == new_list[i+1]:
            fish.append(new_list[i])
    for i in fish:
        one.remove(i)
    g = list(data)
    for m in one:
        g[m] += '\\'
    new_one = ''.join(g)
    return new_one


def dir_script(script_folder_name=script_folder):
    """默认返回test_file文件夹路径，父路径固定为当前文件所在文件夹路径的父路径"""
    pro_dir = os.path.split(os.path.realpath(__file__))[0]  # 当前文件的路径
    prr = os.path.abspath(os.path.dirname(pro_dir) + os.path.sep + ".")  # 当前文件夹父路径
    file_path = os.path.join(prr, script_folder_name)  # script文件所在文件夹路径
    return file_path


def dir_file(test_file_name=case_folder_name):
    """默认返回test_case文件夹路径，父路径固定为当前文件所在文件夹路径的父路径"""
    pro_dir = os.path.split(os.path.realpath(__file__))[0]  # 当前文件的路径
    prr = os.path.abspath(os.path.dirname(pro_dir) + os.path.sep + ".")  # 当前文件夹父路径
    file_path = os.path.join(prr, test_file_name)  # case文件所在文件夹路径
    return file_path


def folder_case_file_path(folder_path=dir_file(), case_file_string=case_file):
    """folder_path文件夹下，名称为case_name的文件所在路径，组成列表，例子如下：
    'c:\dre\tr' ,'re.xlsx,sre.xlsx'生成路径列表['c:\dre\tr\re.xlsx','c:\dre\tr\sre.xlsx']
    默认为配置文件的参数"""
    if case_file_string is (None or ''):  # 文件名称字符串（case_file_string）为空，输出folder_path文件夹下excel文件路径列表
        excel_path_list = listdir(folder_path, [], '.xlsx')
    else:  # 文件名称字符串（case_file_string）不为空，输出folder_path文件夹下涉及到的case_file_string文件路径列表
        excel_path_list = []
        for item in case_file_string.split(','):
            excel_path_list.append(folder_path + '/' + item)
    return excel_path_list


def case_file_sheet_list(str_sheet=case_file_sheet):
    """将字符串格式的sheet标签值转换为列表，格式如下：

    '[23,tr,r4],[54,54d.xlsx,re],[8re,5e,1a]'转换为[['23','tr','r4'],['54','54d.xlsx',re],['8re','5e','1a']]
    默认为获取到配置文件中CASEFILE项下sheet的值并转换为列表"""
    sheet_list = []
    lis = str_sheet.strip(']').split('],')  # 去掉字符串结尾的中括号符号']'，再将字符串转换为列表
    for item in lis:
        item = str(item).strip('[').split(',')  # 列表中的字符串项，去掉中括号符号'['，再转换为列表
        sheet_list.append(item)
    return sheet_list


def case_list(case_file_string=case_file, sheet_page=case_file_sheet):
    """获取到folder_path文件夹下指定的某个或者所有的xlsx格式的excel文件的的名称，及其sheet页名称，并将他们生成键值对
       默认读取配置文件的路径，因此folder_path不在case_list函数中做参数
    """
    excel_name_list = []
    if case_file_string is (None or '') or sheet_page is (None or ''):
        sheet_name_list = []
        for excel in folder_case_file_path(folder_path=dir_file(), case_file_string=case_file_string):
            excel_name = str(excel[:-5]).replace('\\', '/').split('/')[-1]  # 从excel文件路径列表中获取到excel文件的名称（去掉后缀）
            excel_name_list.append(excel_name)  # excel文件名称组成列表
            excel_open = xlrd.open_workbook(excel)
            sheet_name = excel_open.sheet_names()  # 获取excel文件的所有sheet页名称组的列表
            sheet_name_list.append(sheet_name)
    else:  # 默认读取config.ini文件的配置参数，可自定义excel文件列表及其sheet页名称
        for excel in folder_case_file_path(folder_path=dir_file(), case_file_string=case_file_string):
            excel_name = str(excel[:-5]).replace('\\', '/').split('/')[-1]
            excel_name_list.append(excel_name)  # excel文件名称组成列表
        sheet_name_list = case_file_sheet_list(str_sheet=sheet_page)
    dicts = dict(zip(excel_name_list, sheet_name_list))  # excel名称与excel的sheet页名称列表组成键值对
    return dicts


def get_sheet_case_name(file_path, sheet_name):
    """获取一个excel文件下一个sheet中首列的所有值"""
    case_name_list = []
    file = xlrd.open_workbook(file_path)
    sheet_page = file.sheet_by_name(sheet_name)
    num_rows = sheet_page.nrows
    for i in range(1, num_rows):
        case_name_list.append(sheet_page.row_values(i)[0])
    return case_name_list


def get_case(exl_name, sheet_name, case_name):
    """
    利用excel表格的sheet页中某一行首列的字段值，获取到此行的所有字段值，去掉字符串前后的空格，并做相应处理后输出成列表格式

    直接读取excel存储的数字（单元格格式为数字）时，输出结果为【数字一律按浮点型输出，日期输出成一串小数，布尔型输出0或1】，
    下面代码做了相应的处理后，可得到原始输入值，但对数字存储格式有相应要求，对excel存储数字的单元格格式要求如下：
    【整数】、【浮点数】及【日期】，在excel单元格中将其以数字（number）的格式存储
    【字符串格式的数字】，在excel单元格中将其以文本（string）的格式或者数字格式但在数字左边加上引号存储
    【布尔值】，在excel单元格中将其以布尔值（boolean）的格式存储
    所以在验证http请求响应结果的值时，在excel表格中按照上面的要求以相应格式存储预期结果的数字值
    另，【excel单元格默认格式为数字】
    """
    cls = []
    # open xls file
    file = xlrd.open_workbook(exl_name)
    # get sheet by name
    sheet_page = file.sheet_by_name(sheet_name)
    # get one sheet's rows
    num_rows = sheet_page.nrows
    for i in range(num_rows):
        if sheet_page.row_values(i)[0] == case_name:
            len_list = len(sheet_page.row_values(i))
            for j in range(len_list):
                cell_type = sheet_page.cell(i, j).ctype  # ctype：0 empty,1 string, 2 number, 3 date, 4 boolean, 5 error
                cell = sheet_page.cell(i, j).value
                if cell_type == 1:  # 去掉字符串两边的空格
                    cell = cell.strip(" ")
                elif cell_type == 2 and cell % 1 == 0:
                    # 整型数据,浮点型整数值与整数相等，为了接口测试报告中与接口返回的整数值一致，做整数处理
                    cell = int(cell)
                elif cell_type == 3:  # 日期类型数据
                    year, month, day, hour, minute, second = xlrd.xldate_as_tuple(cell, 0)  # (2015, 12, 10, 17, 47, 34)
                    date = datetime(year, month, day, hour, minute, second)
                    cell = date.strftime('%Y-%d-%m %H:%M:%S')
                elif cell_type == 4:  # 布尔型数据
                    cell = True if cell == 1 else False
                cls.append(cell)
    return cls


def get_response(excel_name, sheet_name, case_name, env=1, is_encrypt=True, *args):
    """
    根据excel文档的名称，sheet页名称，及sheet页中case名称获取http请求返回结果中response的特定key的value值

    # 可变参数args中数据会组装为元组，args参数写作格式：'data', 5, 'appName'，自动组装为('data', 5, 'appName')
    默认参数值需要填写，保证可变参数的传参是正确的,
    {
    'code': 1,
    'data':
    [
    {'btId': '510', 'appName': '集成测试打印支付', 'appComName': 'com.jichengtest', 'type': '1', 'updateTime': '2018-11-19 07:24:25'},
    {'btId': '377', 'appName': '无用数据', 'appComName': '无用数据', 'type': '1', 'updateTime': '2018-11-19 07:24:14'},
    {'btId': '509', 'appName': '集成测试打印支付', 'appComName': 'com.jichengtest', 'type': '1', 'updateTime': '2018-11-18 07:23:33'},
    {'btId': '508', 'appName': '集成测试打印支付', 'appComName': 'com.jichengtest', 'type': '1', 'updateTime': '2018-11-17 07:23:04'},
    {'btId': '507', 'appName': '集成测试打印支付', 'appComName': 'com.jichengtest', 'type': '1', 'updateTime': '2018-11-16 11:01:31'},
    {'btId': '506', 'appName': '集成测试打印支付', 'appComName': 'com.jichengtest', 'type': '1', ': '1', 'updateTime': '2018-11-15 07:20:59'}
    ],
    'msg': ''
    }
    responses.json()的结果类似如上，要查看btId值为506的appName，代码格式如下：responses.json()['data'][5]['appName']
    调用response时，在excel表格中写作格式如下：responses("bigdat","data","test_01_generaldeal",1,True,"data")
    """
    if '.xlsx' in excel_name:
        excel_path = dir_file() + '/' + excel_name
    else:
        excel_path = dir_file() + '/' + excel_name + '.xlsx'
    case_data = get_case(excel_path, sheet_name, case_name)
    new_data = replace_string(case_data[5], env, case_data[3])
    new_data = eval(f"f'{new_data}'")  # eval使内层f-string（f''）有效
    # new_data = common.replace_str(new_data)
    responses = configHttp.post_or_get(case_data[2], case_data[3], case_data[4], new_data,
                                       env=env, is_encrypt=is_encrypt)
    try:
        res = responses.json()
        for i in args:  # 可变参数args可代表任意多个参数，最终拿到response中的key对应的value值,args为空值时遍历结果为response本身
            # if responses[i] is not (dict or list):
            #     return print(f'参数{i}')
            res = res[i]
        res = str(res)  # 将res转换为str类型
        res.replace('\"', '\'')  # 将str类型数据中双引号转换为单引号，保证case中response(...)的相应结果不会与原始参数引号冲突
        return res  # 结果类型
    except json.decoder.JSONDecodeError as e:
        print("响应结果不是json格式，报错信息如下：\n", e)
    except BaseException as e:
        return print(f"报错信息【{e}】，请检查response函数中的参数内容！\n"
                     f"response函数：\n【response({excel_name},{sheet_name},{case_name},{env},{is_encrypt})】\n"
                     f"response函数的请求响应结果：\n【{responses.text}】\n"
                     f"请仔细检查response函数【{is_encrypt}】参数后的内容【{','.join(args)}】，此内容应当与响应中key值对应\n")


response = get_response


def replace_string(data, env=1, url='.'):
    """
    替换字符串中的特定字符，为f-string方式的方法引用做准备
    特殊的引用函数修改其env的值
    one = 'response\(.*?\)'  # 引号内容代指字符串'response(...)'，(...)中包含空格在内的字符数量不定
    """
    list_url = url.split('.', 1)
    data = data.replace('{', '{{')
    data = data.replace('}', '}}')
    call_func = ReadConfig().get_callback()['function']
    call_list = call_func.split(',')
    for item in call_list:
        one = item + r'\(.*?\)'
        lis = re.findall(one, data)  # 搜索到data中所有匹配字符串one格式的字符串，组成列表
        lis = list(set(lis))  # 去掉列表中重复元素
        for i in lis:
            li = i.split(',')
            if 'response' in li[0]:
                if env == 3:
                    if list_url[1][:5] == 'sunmi':
                        env = 2
                    elif 'uat' in list_url[0]:
                        env = 1
                    elif 'test' in list_url[0]:
                        env = 0
                    else:
                        print(f'env的值为3，response函数根据url内容访问相应环境！\nurl为【{url}】,无法判断要访问的环境！')
                li[3] = str(env)
                t = ','.join(li)
                data = data.replace(i, '"{' + t + '}"')
            elif 'mgt' in li[0]:
                if env == 3:
                    if list_url[1][:5] == 'sunmi' or 'uat' in list_url[0]:
                        env = 1
                    elif 'test' in list_url[0]:
                        env = 0
                    else:
                        print(f'env的值为3，mgt函数需要根据url内容访问相应环境！\nurl为【{url}】,无法判断要访问的环境！')
                elif env == 2:
                    env = 1
                li[2] = str(env) + ')'
                t = ','.join(li)
                data = data.replace(i, '"{' + t + '}"')
            elif 'partner' in li[0]:
                if env == 3:
                    if list_url[1][:5] == 'sunmi' or 'uat' in list_url[0]:
                        env = 1
                    elif 'test' in list_url[0]:
                        env = 0
                    else:
                        print(f'env的值为3，partner函数需要根据url内容访问相应环境！\nurl为【{url}】,无法判断要访问的环境！')
                elif env == 2:
                    env = 1
                li[2] = str(env) + ')'
                t = ','.join(li)
                data = data.replace(i, '"{' + t + '}"')
    return data


def replace_str(data):
    """去掉大括号及中括号外的双引号"""
    data = data.replace('"{', '{')
    data = data.replace('}"', '}')
    data = data.replace('"[', '[')
    data = data.replace(']"', ']')
    data = data.replace('\'', '\"')
    return data


# ***************************************将html报告文件上传到服务器****************************************


def upload_file(file_name):
    """使用sftp协议将本地文件上传文件到Linux系统"""
    transport = paramiko.Transport((linux_host, int(linux_port)))
    transport.connect(username=linux_username, password=linux_password)
    sftp = paramiko.SFTPClient.from_transport(transport)  # 建立连接
    remote_path = linux_dir + '/' + file_name  # 远程服务器路径
    local_path = dir_result() + '/' + file_name  # 结果报告文件路径
    try:
        i = 1
        if i < 4:
            sftp.put(local_path, remote_path)  # 将本地的文件上传至服务器
            # sftp.get('/root/Linux.txt', 'Linux.txt')  # 将Linux上的/root/Linux.txt下载到本地
            if file_name not in sftp.listdir(linux_dir):  # 判断文件是否在上传路径下
                print(f"第{i}次上传文件失败！")
                i += 1
                if i == 4:
                    print('尝试上传已失败三次，不再继续尝试！')
                    return False
            else:
                print('文件上传成功！')
                return True
    except Exception as e:
        print(e)
        return False
    transport.close()  # 关闭连接


# ******************************************html报告文件处理展示***************************************


def find_word(file, word):
    """查找文件file文件中的字符串word内容"""
    n = 1
    read_list = open(file, 'rb').readlines()  # 以byte方式读取文件
    for line in read_list:
        if word.encode() in line:  # 将word内容转换为byte类型，进行校验
            return True
        else:
            n += 1
    if n > len(read_list):
        return False


def show_results(case_doc, method, url, params, responses, response_key, expected_value, data=None, env=1):
    """输出请求及响应的参数值"""
    url = configHttp.env_url(url, env=env)
    if method == 'get':
        print("接口具体请求参数与响应结果如下：\n"
              "【请求参数】\n"
              f"url: {url}\n"
              f"method: {method}\n"
              f"params: {params}\n"
              "【响应结果】\n"
              f"response:\n{responses}\n")
    elif method == 'post':
        print("接口具体请求参数与响应结果如下：\n"
              "【请求参数】\n"
              f"url: {url}\n"
              f"method: {method}\n"
              f"params: {params}\n"
              f"data: {data}\n"
              "【响应结果】\n"
              f"response:\n{responses}\n")
    print(f"用例【{case_doc}】，预期接口响应字段【{response_key}】的值为【{expected_value}】\n")


def dir_result():
    """返回result文件夹路径"""
    pro_dir = os.path.split(os.path.realpath(__file__))[0]  # 当前文件所在文件夹路径，非执行文件路径
    prr = os.path.abspath(os.path.dirname(pro_dir) + os.path.sep + ".")  # 当前文件夹父路径
    result_path = os.path.join(prr, "result")  # 报告文件所在文件夹路径
    return result_path


def newest_file(list_name):
    """根据日期及时间数字获取最新文件"""
    lis = []
    for file in list_name:
        stri = ''
        for i in file:
            if i in '1234567890':
                stri += i
        lis.append(int(stri))
    ind = lis.index(max(lis))
    return list_name[ind]


def new_html(name):
    """获取到最新的html文件的路径"""
    report_path = dir_result()  # 获取到result文件夹路径
    lis = []
    type_file = name + '.html'
    file_list = listdir(report_path, lis, type_file)
    return newest_file(file_list)


# ****************************** SQL ********************************

def db_config(env=1, *args):
    """根据环境配置数据库"""
    if env == 1:  # uat环境数据库
        host = ReadConfig().get_db_uat("host")
        username = ReadConfig().get_db_uat("username")
        password = ReadConfig().get_db_uat("password")
        port = ReadConfig().get_db_uat("port")
        return [host, username, password, int(port)]
    elif env == 0:  # test环境数据库
        host = ReadConfig().get_db_test("host")
        username = ReadConfig().get_db_test("username")
        password = ReadConfig().get_db_test("password")
        port = ReadConfig().get_db_test("port")
        return [host, username, password, int(port)]
    elif env == 3:  # 自定义数据库
        host = args[0]
        username = args[1]
        password = args[2]
        port = args[3]
        return [host, username, password, int(port)]


def db_select(database, table, select_key, key, val, env=1, *args):
    """
    查询uat环境partners库中某一张表中的字段值

    数据库pymysql.connect方法参数：
                 host=None, user=None, password="",
                 database=None, port=0, unix_socket=None,
                 charset='', sql_mode=None,
                 read_default_file=None, conv=None, use_unicode=None,
                 client_flag=0, cursorclass=Cursor, init_command=None,
                 connect_timeout=10, ssl=None, read_default_group=None,
                 compress=None, named_pipe=None,
                 autocommit=False, db=None, passwd=None, local_infile=False,
                 max_allowed_packet=16*1024*1024, defer_connect=False,
                 auth_plugin_map=None, read_timeout=None, write_timeout=None,
                 bind_address=None, binary_prefix=False, program_name=None,
                 server_public_key=None
    """
    config = db_config(env, args)
    connect = pymysql.connect(config[0], config[1], config[2], database, config[3])
    cursor = connect.cursor()
    sql = f"SELECT {select_key} FROM {table} WHERE {key} = '{val}';"
    cursor.execute(sql)
    result = cursor.fetchone()

    connect.close()
    return result
