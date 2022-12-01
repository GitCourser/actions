# ==============================================================================
# Author       : Courser
# Date         : 2022-11-30 21:27:13
# LastEditTime : 2022-11-30 22:19:32
# Description  : 本地疫情速报
# ==============================================================================

import sys
sys.path.append('..')
import re
from playwright.sync_api import sync_playwright
from common import runtime, WeChat, isCloud

app = '本地疫情速报'


def getinfo():
    with sync_playwright() as p:
        url = 'https://wjw.hubei.gov.cn/bmdt/dtyw'
        browser = p.webkit.launch()
        page = browser.new_page()
        page.goto(url)
        resp = page.inner_html('#share')
        # print(resp)
        if result := re.search(r'href=".(.+)" title="\d+年\d+月\d+日湖北省新冠肺炎疫情情况"', resp):
            url = f'{url}{result.group(1)}'
            # print(url)
        page.goto(url)
        # print(page.title())
        resp = page.inner_text('//*[@id="article-box"]/div[1]/p[1]')
        page.screenshot(path="example.png")
        browser.close()
    return resp


@runtime(app)
def main():
    txt = getinfo()
    msg = re.search(r'(\d+月\d+日.+时)，', txt).group(1)
    msg += '新增\n【湖北】\n'
    if foo := re.search(r'全省新增本土确诊病例(\d+)例.+新增本土无症状感染者(\d+)例（武汉市(\d+)例，.+荆州市(\d+)例，', txt):
        msg += f'确　诊：{foo.group(1)}\n无症状：{foo.group(2)}\n武　汉：{foo.group(3)}\n荆　州：{foo.group(4)}'
    if isCloud:
        notify = WeChat()
        notify.send(app, msg)
    else:
        print(msg)


def run():
    main()


if __name__ == '__main__':
    run()
