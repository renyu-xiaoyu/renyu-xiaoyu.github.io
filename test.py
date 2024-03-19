import json
import os
import re
import time  # 事件库，用于硬性等待
import urllib

import logging
import cv2
import requests
from numpy import random
from selenium.webdriver import ActionChains
from selenium.webdriver.support import expected_conditions as EC

from selenium import webdriver  # 导入selenium的webdriver模块
from selenium.webdriver.common.by import By  # 引入By类选择器
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options

# 创建Chrome WebDriver对象
# driver = webdriver.Chrome()

# 启用无头模式模拟阿水 AI 签到操作。

# 启用无头模式
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument('--disable-gpu')
driver = webdriver.Chrome(options=chrome_options)

# 设置日志文件的路径
log_dir = "/opt/log"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
# 配置日志
logging.basicConfig(filename=log_dir + "/mylog.log", level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


# 封装的计算图片距离的算法
def get_pos(imageSrc):
    # 读取图像文件并返回一个image数组表示的图像对象
    image = cv2.imread(imageSrc)
    # GaussianBlur方法进行图像模糊化/降噪操作。
    # 它基于高斯函数（也称为正态分布）创建一个卷积核（或称为滤波器），该卷积核应用于图像上的每个像素点。
    blurred = cv2.GaussianBlur(image, (5, 5), 0, 0)
    # Canny方法进行图像边缘检测
    # image: 输入的单通道灰度图像。
    # threshold1: 第一个阈值，用于边缘链接。一般设置为较小的值。
    # threshold2: 第二个阈值，用于边缘链接和强边缘的筛选。一般设置为较大的值
    canny = cv2.Canny(blurred, 0, 100)  # 轮廓
    # findContours方法用于检测图像中的轮廓,并返回一个包含所有检测到轮廓的列表。
    # contours(可选): 输出的轮廓列表。每个轮廓都表示为一个点集。
    # hierarchy(可选): 输出的轮廓层次结构信息。它描述了轮廓之间的关系，例如父子关系等。
    contours, hierarchy = cv2.findContours(canny, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    # 遍历检测到的所有轮廓的列表
    for contour in contours:
        # contourArea方法用于计算轮廓的面积
        area = cv2.contourArea(contour)
        # arcLength方法用于计算轮廓的周长或弧长
        length = cv2.arcLength(contour, True)
        # 如果检测区域面积在5025-7225之间，周长在300-380之间，则是目标区域
        if 5025 < area < 7225 and 300 < length < 380:
            # 计算轮廓的边界矩形，得到坐标和宽高
            # x, y: 边界矩形左上角点的坐标。
            # w, h: 边界矩形的宽度和高度。
            x, y, w, h = cv2.boundingRect(contour)
            print("计算出目标区域的坐标及宽高：", x, y, w, h)
            # 在目标区域上画一个红框看看效果
            # cv2.rectangle(image, (x, y), (x+w, y+h), (0, 0, 255), 2)
            # cv2.imwrite("111.jpg", image)
            return x
    return 0


try:
    # 打开阿水 AI 登录页
    driver.get("https://ai.ashuiai.com/login")
    print(driver.title)  # 打印页面的标题
    # 等待 3 秒加载页面
    time.sleep(3)
    # 获取账号密码组件并赋值
    userInput = driver.find_element(By.XPATH,
                                    '//*[@id="app"]/div/div[1]/div/div[1]/div/div[2]/div/main/form/div[1]/div[1]/div/div[1]/div/input')
    userInput.send_keys("shazishazi2022@163.com")
    passInput = driver.find_element(By.XPATH,
                                    '//*[@id="app"]/div/div[1]/div/div[1]/div/div[2]/div/main/form/div[2]/div[1]/div/div[1]/div[1]/input')
    passInput.send_keys("abcd1234")
    # 输入账号密码后等待 1 秒后点击验证按钮
    time.sleep(1)
    # 使用浏览器的F12开发者工具，使用copy xpath获取该元素的XPATH路径。点击验证按钮
    passClick = driver.find_element(By.XPATH,
                                    '//*[@id="app"]/div/div[1]/div/div[1]/div/div[2]/div/main/form/div[3]/div[1]/div/button/span[2]')
    passClick.click()
    # 等待 2 秒加载滑动验证码的图片
    time.sleep(2)
    # 此时需要切换到弹出的滑块区域，需要切换frame窗口
    driver.switch_to.frame("tcaptcha_iframe_dy")
    # 等待滑块验证图片加载后，再做后面的操作
    WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.ID, 'slideBg')))
    # 获取滑块验证图片下载路径，并下载到本地
    bigImage = driver.find_element(By.ID, "slideBg")
    s = bigImage.get_attribute("style")  # 获取图片的style属性
    # 设置能匹配出图片路径的正则表达式
    p = 'background-image: url\(\"(.*?)\"\);'
    # 进行正则表达式匹配，找出匹配的字符串并截取出来
    bigImageSrc = re.findall(p, s, re.S)[0]  # re.S表示点号匹配任意字符，包括换行符
    print("滑块验证图片下载路径:", bigImageSrc)
    # 下载图片至本地
    urllib.request.urlretrieve(bigImageSrc, '/opt/bigImage.png')
    # 计算缺口图像的x轴位置
    dis = get_pos('/opt/bigImage.png')
    # 获取小滑块元素，并移动它到上面的位置
    smallImage = driver.find_element(By.XPATH, '//*[@id="tcOperation"]/div[6]')
    # 小滑块到目标区域的移动距离（缺口坐标的水平位置距离小滑块的水平坐标相减的差）
    # 新缺口坐标=原缺口坐标*新画布宽度/原画布宽度
    newDis = int(dis * 340 / 672 - smallImage.location['x'])
    driver.implicitly_wait(5)  # 使用浏览器隐式等待5秒
    # 按下小滑块按钮不动
    ActionChains(driver).click_and_hold(smallImage).perform()
    # 移动小滑块，模拟人的操作，一次次移动一点点
    i = 0
    moved = 0
    while moved < newDis:
        x = random.randint(3, 10)  # 每次移动3到10像素
        moved += x
        ActionChains(driver).move_by_offset(xoffset=x, yoffset=0).perform()
        # print("第{}次移动后，位置为{}".format(i, smallImage.location['x']))
        i += 1
    # 移动完之后，松开鼠标
    ActionChains(driver).release().perform()
    logging.info("滑动成功")
    # 验证完后等待两秒后再点击登录按钮
    time.sleep(3)
    print("点击之前")

    # 切回主元素
    driver.switch_to.default_content()
    print("切回主元素")

    # 获取登录按钮并点击登录
    loginButton = driver.find_element(By.XPATH,
                                      '//*[@id="app"]/div/div[1]/div/div[1]/div/div[2]/div/main/form/button/span')
    loginButton.click()
    print("点击登录了")

    # 登录成功加载页面
    time.sleep(5)
    print("登录成功了")

    # 获取响应头中的 token
    localStorage = driver.execute_script('return localStorage.getItem("_token_");')
    loads = json.loads(localStorage)
    print("localStorage：", loads["data"])

    # 定义请求头，替换 YOUR_TOKEN_HERE 为实际的 token 值
    headers = {
        'Authorization': 'Bearer ' + loads["data"],
    }

    # 定义请求的 URL 和要发送的数据
    url = 'https://api.xiabb.chat/chatapi/marketing/signin'  # 替换为实际的 API 接口 URL

    # 发送 POST 请求
    response = requests.post(url, headers=headers)

    # 打印响应内容
    print(response.text)

finally:
    # 关闭浏览器
    driver.quit()
