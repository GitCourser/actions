# ==============================================================================
# Author       : Courser
# Date         : 2021-12-07 19:54:45
# LastEditTime : 2022-01-05 23:40:07
# Description  : 超星学习通签到
# ==============================================================================

import requests
from lxml import etree
import base64
import sys
import re
sys.path.append('..')
from common import runtime, UA, WeChat, getcfg, isCloud


app = '超星学习通签到'
api = 'https://mobilelearn.chaoxing.com/'
notify = WeChat()
course_dict = {}


def login(username, password):
    """登录学习通

    Args:
        username (str): 用户名
        password (str): 密码
    """

    url = 'http://passport2.chaoxing.com/fanyalogin'
    headers = {
        'User-Agent': UA,
        'Referer': 'http://passport2.chaoxing.com/login?fid=&newversion=true&refer=http%3A%2F%2Fi.chaoxing.com'
    }
    data = {
        'fid': -1,
        'uname': username,
        'password': base64.b64encode(password.encode()).decode(),
        'refer': 'http%253A%252F%252Fi.chaoxing.com',
        't': True,
        'forbidotherlogin': 0
    }
    session.post(url, headers=headers, data=data)
    # print(res.cookies)


def getclass():
    """读取课程"""

    url = 'http://mooc1-2.chaoxing.com/visit/courses'
    headers = {'User-Agent': UA, 'Referer': 'http://i.chaoxing.com/'}
    res = session.get(url, headers=headers)
    # print(res.text)

    if res.status_code == 200:
        class_HTML = etree.HTML(res.text)
        print('已开通的课程：')

        for class_item in class_HTML.xpath('''/html/body/div/div[2]/div[3]/ul/li[@class='courseItem curFile']'''):
            # courseid=class_item.xpath('''./input[@name='courseId']/@value''')[0]
            # classid=class_item.xpath('''./input[@name='classId']/@value''')[0]
            try:
                class_item_name = class_item.xpath('./div[2]/h3/a/@title')[0]
                # 等待开课的课程由于尚未对应链接，所以缺少a标签。
                print(class_item_name)
                course_dict[class_item_name] = f'''https://mooc1-2.chaoxing.com{class_item.xpath('./div[1]/a[1]/@href')[0]}'''
            except Exception():
                pass
        print('—' * 35)
    else:
        print('课程读取失败')


def qiandao(currClass, url, address):
    """课程签到

    Args:
        currClass (str): 课程名
        url (str): 课程地址
        address (str): 签到地址
    """

    courseid = re.findall(r'courseid=(.*?)&', url)[0]
    clazzid = re.findall(r'clazzid=(.*?)&', url)[0]
    url = f'{api}widget/pcpick/stu/index?courseId={courseid}&jclassId={clazzid}'
    headers = {'User-Agent': UA}
    res = session.get(url, headers=headers)
    # print(res.text)
    tree = etree.HTML(res.text)
    # fid=tree.xpath('/html/body/input[4]/@value')
    activeDetail = tree.xpath('/html/body/div[2]/div[2]/div/div/div/@onclick')
    if not activeDetail:
        print(f'{currClass}------暂无签到活动')
    else:
        print()
        print(f'{currClass}------检测到：{len(activeDetail)} 个活动')
        msg = ''

        for activeID in activeDetail:
            id = re.findall(r'activeDetail\((.*?),', activeID)[0]
            enc = ''
            data = session.get(f'{api}v2/apis/sign/refreshQRCode?activeId={id}').json()['data']
            if data is not None:
                enc = data['enc']
            # print(enc)

            url = f'{api}pptSign/stuSignajax?activeId={id}&clientip=&latitude=-1&longitude=-1&appType=15&fid=0&enc={enc}&address={address}'
            res = session.get(url, headers=headers)
            # url='https://mobilelearn.chaoxing.com//widget/sign/pcStuSignController/checkSignCode?activeId={id}&signCode={signcode}'.format(id=id,signcode=1236)
            # res=session.get(url,headers=headers)
            print(res.text)
            if '非签到活动' in res.text:
                continue
            if res.text == 'success':
                print(f'{currClass}: 签到成功')
                msg += f'{currClass}: 签到成功\n'
            elif res.text == '您已签到过了':
                print(f'{currClass}: 您已签到过了')
            else:
                print(f'{currClass}: 签到失败\n{res.text}')
                msg += f'{currClass}: 签到失败\n{res.text}\n'

        if msg and isCloud:
            notify.send(app, msg)
        print()


@runtime(app)
def main():
    userinfo = getcfg('chaoxing', 'chaoxing.cfg')
    username = userinfo['user']
    password = userinfo['pwd']
    address = userinfo['addr']

    global session
    session = requests.Session()

    login(username, password)
    getclass()

    # print(course_dict)
    for i in course_dict.keys():
        qiandao(i, course_dict[i], address)


def run():
    main()


if __name__ == '__main__':
    run()
