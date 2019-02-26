from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image
import os


def report_image(url):
    """截取简要测试报告的页面生成图片，并对图片进行裁剪处理，然后将新图片保存在result文件夹下，返回路径"""
    pro_dir = os.path.split(os.path.realpath(__file__))[0]
    father_path = os.path.abspath(os.path.dirname(pro_dir) + os.path.sep + ".")  # 当前文件夹父路径
    report_path = os.path.join(father_path, "result")  # 报告文件所在文件夹路径

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    driver = webdriver.Chrome(chrome_options=chrome_options)
    if 'http://' not in url:  # 本地html文件url地址修改
        url = 'file:///' + url
    driver.get(url)
    driver.set_window_size(1500, 700)
    image_dir = "report.png"
    driver.save_screenshot(image_dir)  # 只能对屏幕进行截图

    im = Image.open(image_dir)
    box = (0, 0, 1500, 600)  # 元组参数包含四个值，分别代表矩形四条边的距离X轴或者Y轴的距离，矩形边顺序是(左，顶，右，底)
    region = im.crop(box)  # 对图片进行截取
    new_image = report_path + '/new.png'
    region.save(new_image)
    os.remove(image_dir)  # 删除selenium中使用save_screenshot方法生成的截图
    return new_image


def html_summary_content(pass_count, fail_count, error_count, start_time, duration):
    """简要的html格式测试报告的内容"""
    repo = f'''
<html version="1.0" encoding="UTF-8"?>
<head>
    <meta charset="utf-8">
    <script type="text/javascript" src="https://cdn.bootcss.com/echarts/4.2.0-rc.1/echarts.js"></script>
    <h1>商米API简要测试报告</h1>
</head>
<body>
    <div id="main" style="height:300px;padding:5px;"></div> 
    <script>
        var myChart = echarts.init(document.getElementById("main"))		
        var option ={{
            title: {{  // 标题展示
                text: '用例执行结果状态',
                top:'10%',
                left:'10',
                textStyle:{{
                    fontWeight:'normal',
                    fontSize:23,
                }}
            }},
            tooltip: {{  //提示框组件
                trigger: 'axis',
                axisPointer : {{            // 坐标轴指示器，坐标轴触发有效
                    type : 'shadow'        // 默认为直线，可选为：'line' | 'shadow'
                }}
            }},
            legend: {{	//图例组件				
                data: ['Pass', 'Fail', 'Error',], //数据
                orient: 'horizontal',  // 图例列表的布局朝向，vertical 纵向  horizontal 横向
                top: '60%',  //图例组件离容器上侧的距离 	
                left: '2%',  //图例组件离容器左侧的距离
                //right: '1%',  //图例组件离容器右侧的距离
                itemGap: 10,  //图例每项之间的间隔。横向布局时为水平间隔，纵向布局时为纵向间隔。
                itemWidth: 50,  //图例标记的图形宽度
                itemHeight: 20,  //图例标记的图形高度				 
            }},
            grid: {{  // 条状图的各个参数,距离左边框、右边框，底部的距离及高度
                left: '2%',
                right: '20',
                top: '35%',
                height:'30%',
                width: '87%',
                containLabel: true
            }},
            xAxis: {{     // x轴
                type: 'value',  // 数值轴
                show: false,
                max: {pass_count+fail_count+error_count},
            }},
            yAxis: {{     // y轴
                type: 'category',  // 类目轴
                show: false
            }},
            series: [  //系列列表，每个系列通过 type 决定自己的图表类型
                {{
                    name: 'Pass',
                    type: 'bar',
                    stack: '总量',
                    itemStyle: {{ // 图型属性
                        color: '#32cd32',  //绿色#  00FF00   32cd32
                        borderColor: '#333',  //边框颜色
                        borderWidth: 0.8,  //边框宽度
                        borderType: 'solid',  //边框类型 
                    }}, 
                    label: {{  // 标签文本属性
                        show: true,
                        position: 'top',
                        rotate:90,  //标签旋转。从 -90 度到 90 度。正值是逆时针
                        offset:[-15,-10],  //[30, 40] 表示文字在横向上偏移 30，纵向上偏移 40。
                        //fontSize: 13
                    }},
                    data: [{pass_count}] //具体数据
                }},
                {{
                    name: 'Fail',
                    type: 'bar',
                    stack: '总量',
                    label: {{
                        show: true,
                        position: 'top',
                        //rotate:-45,
                        offset:[0,-10],
                    }},
                    itemStyle: {{ 
                        color: '#E87C25',  
                        borderColor: '#333',
                        borderWidth: 0.8,
                        borderType: 'solid',
                    }}, 
                    data: [{fail_count}],
                }},
                {{
                    name: 'Error',
                    type: 'bar',
                    stack: '总量',
                    label: {{
                        show: true,
                        position: 'top',
                        rotate:90,
                        offset:[15,-10],	
                    }},
                    itemStyle: {{ 
                        color: '#FF0000',  
                        borderColor: '#333',
                        borderWidth: 0.8,
                        borderType: 'solid',
                    }},	
                    data: [{error_count}],					
                }}
            ]
        }}
        myChart.setOption(option);
        window.onresize = myChart.resize;  //自适应窗口大小
    </script>
    <table border="1" width="90%">
    <thead>
        <tr>
            <td colspan="3" style="text-align:left;font-weight:bold;font-size:25px;background:#DDDDDD;">表格统计信息</td>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td rowspan="8" style="text-align:center;font-weight:bold;font-size:20px;background:#CCCCCC;">汇总</td>

            <td style="text-align:center;font-weight:normal;font-size:15px;background:#CCCCCC;">用例总数</td>

            <td style="text-align:center;font-weight:normal;font-size:15px;background:#CCCCCC;">{pass_count+fail_count+error_count}</td>
        </tr>
        <tr>
            <td style="text-align:center;font-weight:normal;font-size:15px;background:#CCCCCC;">通过数量</td>

            <td style="text-align:center;font-weight:normal;font-size:15px;background:#00FF00;">{pass_count}</td>
        </tr>
        <tr>
            <td style="text-align:center;font-weight:normal;font-size:15px;background:#CCCCCC;">失败数量</td>

            <td style="text-align:center;font-weight:normal;font-size:15px;background:#E87C25;">{fail_count}</td>
        </tr>
        <tr>
            <td style="text-align:center;font-weight:normal;font-size:15px;background:#CCCCCC;">错误数量</td>

            <td style="text-align:center;font-weight:normal;font-size:15px;background:#FF0000;">{error_count}</td>
        </tr>
        <tr>
            <td style="text-align:center;font-weight:normal;font-size:15px;background:#CCCCCC;">开始时刻(GMT+08:00)</td>

            <td style="text-align:center;font-weight:normal;font-size:15px;background:#CCCCCC;">{start_time}</td>
        </tr>
        <tr>
            <td style="text-align:center;font-weight:normal;font-size:15px;background:#CCCCCC;">执行时长</td>

            <td style="text-align:center;font-weight:normal;font-size:15px;background:#CCCCCC;">{duration}</td>
        </tr>
    </tbody>
    </table>    
</body>
</html> 
    '''
    return repo


def html_report_path(report_path):
    """详细API测试报告的路径"""
    repo = f'''
<html encoding="UTF-8"?>	
<h2>
<br> 
点击可查看：<a style="color:red" href="{report_path}">商米API详细测试报告</a> 
</h2>
</html>
    '''
    return repo


