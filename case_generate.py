import os
import readConfig
from common import common
ReadConfig = readConfig.ReadConfig()

py_start_text = """
import unittest
from common import configHttp
from common import common
from common.common import get_response as response
from common.special import mgt_admin_id as mgt
from common.special import partner_admin_id as partner

"""

py_end_text = '''

if __name__ == "__main__":
    unittest.main() 
'''


def class_text(class_name):
    """class类的文件"""
    new_sheet_doc = ReadConfig.get_sheet_doc()  # 读取class类说明内容生成数据类型为字典，赋值给新的变量
    if class_name not in new_sheet_doc:
        new_sheet_doc[class_name] = ''
    text = f'''  
class {class_name.title()}(unittest.TestCase):  # class_name.title()方法为字符串首字母大写
    """{new_sheet_doc[class_name]}"""
    def setUp(self):
        print("\\ncase start!\\n")

    def tearDown(self):
        print("\\ncase end!\\n"
              "*****************************************************************************")
        pass
    '''
    return text


def fun_text(file_path, sheet_page, case_name, env=1, is_encrypt=True):
    """函数的文档内容，env值代表不同测试环境下post请求，1为uat，0为test，2为release，默认为uat环境"""
    case_data = common.get_case(file_path, sheet_page, case_name)
    text = f'''
    def {case_name}(self):
        """{case_data[1]}"""
        case_data = common.get_case(r"{file_path}",
                                    r"{sheet_page}",
                                    r"{case_name}")  
        new_data = common.replace_string(case_data[5], {env}, case_data[3])
        new_data = new_data.replace('\\\\', '\\\\\\\\')
        new_data = eval(f"f'{{new_data}}'")  # eval使内层f-string（f''）有效
        # 请求方法get或者post判断
        responses = configHttp.post_or_get(case_data[2], case_data[3], case_data[4], new_data, 
                                           env={env}, is_encrypt={is_encrypt})
        # case相关参数 
        common.show_results(case_data[1], case_data[2], case_data[3], case_data[4], common.resp_result(responses),
                            case_data[6], case_data[7], new_data, {env})  # case_data[5]为原始参数，new_data为实际传入参数
        # 响应结果的断言，保存先判断相应结果不为空，再判断预期与实际结果是否一致
        self.assertFalse(responses is None, "响应结果为空！")  # 如果断言失败，之后的代码不再执行
        self.assertTrue(responses.text[0] == '{{' and responses.text[-1] == '}}', "响应结果不是json格式！")
        self.assertEqual(common.response_deal(responses.json()[case_data[6]]),
                         common.response_deal(case_data[7]), 
                         "预期与实际结果不一致！")  # 将字符串中所有单引号变成双引号，字符串比较时去除单双引号的影响
        # 输出结果
        print("接口响应结果与预期一致，测试通过！")        
    '''
    return text

# 读取整个文件夹下的测试用例


def script_generate(config_filename=True, config_sheet=True, delete_old_script=True, env=3, is_encrypt=True):
    """config_filename=True为读取配置文件中的filename内容，config_sheet=True为读取配置文件中的sheet内容
    都为false则读取配置文件中已写明的文件夹下所有excel文件的内容
    delete_old_script为True则在生成py文件前，先删除同名文件
    env值代表不同测试环境下post请求，1为uat，0为test，2为release，默认为uat环境
    """
    script_folder = common.dir_script()  # 脚本文件夹路径
    if config_filename is False:  # 不引入配置文件的case文件名称，即读取case文件夹下所的case文件
        path_list = common.folder_case_file_path(case_file_string=None)
        file_sheet_dict = common.case_list(case_file_string=None)
    elif config_filename is True and config_sheet is False:  # 读取配置文件下的case文件，但不读取配置文件下的sheet列表数据
        path_list = common.folder_case_file_path()
        file_sheet_dict = common.case_list(sheet_page=None)
    else:  # 读取配置文件的case名称及sheet列表，即完全按照配置文件的参数创建脚本文件
        path_list = common.folder_case_file_path()
        file_sheet_dict = common.case_list()

    for path in path_list:
        py_filename = str(path[:-5]).replace('\\', '/').split('/')[-1]  # 文件名称无后缀
        script_path = script_folder + '/' + 'test_' + py_filename + '.py'  # 脚本文件路径
        if delete_old_script is False and os.path.exists(script_path):  # 存在老的脚本文件则不再生成此文件
            continue
        file_script = open(script_path, 'w', encoding='utf-8')
        print(f'case文件【{path}】，开始生成脚本【test_{py_filename}.py】')
        file_script.write(py_start_text)
        for sheet in file_sheet_dict[py_filename]:
            file_script.write(class_text(sheet))
            print(f'已生成unittest类【{sheet}】')
            for case in common.get_sheet_case_name(path, sheet):
                file_script.write(fun_text(path, sheet, case, env, is_encrypt))
                print(f'已生成【{sheet}】类的自定义函数【{case}】')
        file_script.write(py_end_text)
        print(f'已生成脚本文件【test_{py_filename}.py】的unittest执行部分')
        file_script.close()
        print(f'脚本文件【test_{py_filename}.py】生成成功，所在路径【{script_folder}】')
    return print('所有脚本文件已生成！')
