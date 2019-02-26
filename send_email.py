import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.mime.image import MIMEImage
from common import common
import readConfig
from common import report_template
readconfig = readConfig.ReadConfig()

mail_host = readconfig.get_email("mail_host")
mail_port = readconfig.get_email("mail_port")
mail_user = readconfig.get_email('mail_user')
mail_pwd = readconfig.get_email('mail_pwd')
sender = readconfig.get_email('sender')  # 邮件发送者
receivers = readconfig.get_email('receiver')  # 邮件接收者列表
mail_subject = readconfig.get_email('subject')  # 邮件标题


# receivers = ['zhanggaoxia@sunmi.com', 'guhaitao@sunmi.com']  # 邮件接收者列表
# mail_user = 'guhaitao@sunmi.com'
# mail_pwd = 'Gu2016'
# mail_subject = "API接口测试结果"  # 邮件的标题

# proDir = os.path.split(os.path.realpath(__file__))[0]  # 当前文件所在文件夹路径
# father_path = os.path.abspath(os.path.dirname(proDir) + os.path.sep + ".")  # 当前文件夹父路径
# report_Path = os.path.join(proDir, "result")  # 报告文件所在文件夹路径
#
# pat= r'C:\Users\Administrator\PycharmProjects\api_test\result'
# lis = []
# type_file = '.html'
# list = listdir(pat, lis, type_file)
# html = newest_file(list)


def send_email(upload_report=True, remote_path=None, result_path=None, summary_path=None, att=False):
    if summary_path is None:
        summary_path = common.new_html('summary')
    if result_path is None:
        result_path = common.new_html('result')  # 最新的详细测试结果文件路径

    email_html_content = '<html><body><img src="cid:img1" alt="图片文字说明"></body></html>'
    email_html_path = report_template.html_report_path(remote_path)
    if upload_report is True:  # 报告上传到服务器成功，在邮件中展示服务器路径
        mail_context = email_html_content + email_html_path
    else:  # 报告上传到服务器失败，邮件不展示服务器路径
        mail_context = email_html_content

    message = MIMEMultipart()  # 引入邮件函数方法
    context = MIMEText(mail_context, 'html', 'utf-8')
    message.attach(context)  # 将html格式内容添加到邮件内容中
    image_path = report_template.report_image(summary_path)  # 通过简要测试报告生成的图片路径
    file = open(image_path, "rb")  # 打开简要测试报告生成的图片
    img_content = file.read()  # 读取图片内容，并赋值给变量保存
    file.close()  # 关闭图片文件
    os.remove(image_path)  # 关闭图片内容后，删除简要测试报告生成的图片
    img = MIMEImage(img_content)
    img.add_header('Content-ID', 'img1')  # 将图片内嵌到邮件中，通过Content-ID的值img1去引用
    message.attach(img)  # 将图片添加到邮件正文内容中

    # message['From'] = Header("谷海涛", 'utf-8')     # 发送者名字修改
    # message['To'] = Header("张高贤", 'utf-8')        # 接收者名字修改

    message['From'] = sender     # 发送者，字符串格式
    message['To'] = receivers    # 接收者列表，字符串格式，逗号分隔
    message['Subject'] = Header(mail_subject, 'utf-8')  # 邮件标题

    # 构造附件1
    att1 = MIMEText(open(result_path, 'rb').read(), 'base64', 'utf-8')
    att1["Content-Type"] = 'application/octet-stream'

    # # 这里的filename可以任意写，写什么名字，邮件中显示什么名字，附件名称非中文时的写法
    # att1["Content-Disposition"] = 'attachment; filename="ota.html"'

    # 附件名称为中文时的写法
    att1.add_header("Content-Disposition", "attachment", filename=("utf-8", "", "商米API详细测试结果.html"))
    if att is True:
        message.attach(att1)

    try:
        email = smtplib.SMTP_SSL(mail_host, mail_port)
        # smtpObj.set_debuglevel(1)  # 打log
        email.connect(mail_host, mail_port)
        email.login(mail_user, mail_pwd)
        email.sendmail(sender, receivers.split(','), message.as_string())  # 将字符串格式收件人转化为列表格式
        email.quit()
        if att is True:
            print("\n附件为测试报告，邮件发送成功！")
        else:
            print("\n无附件邮件发送成功！")
    except smtplib.SMTPException as e:
        print(e)
