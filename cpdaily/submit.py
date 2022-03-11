# 负责每天签到的主程序，调用一次填报一次

import sys
import hashlib
import requests
import urllib.parse
from utils import log, getModAuthCas, config, user, deviceID
from encrypt import coordinateOffset, DESEncrypt, encrypt_BodyString
# import oss2
sys.path.append('..')
from common import WeChat, isCloud

# ###########配置############
Cookies = {
    'acw_tc': '',
    'MOD_AUTH_CAS': user['MOD_AUTH_CAS'],
}
sessionToken = user['Token']
# CpdailyInfo = user['CpdailyInfo']
host = user['host']
api = f'https://{host}/wec-counselor-collector-apps/stu/collector/'
lon = coordinateOffset(user['lon'])
lat = coordinateOffset(user['lat'])
ua = 'Mozilla/5.0 (Linux; Android 11; M2012K11AC Build/RKQ1.200826.002; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/92.0.4515.131 Mobile Safari/537.36 cpdaily/9.0.14 wisedu/9.0.14'
# ###########配置############

# 全局
session = requests.session()
session.cookies = requests.utils.cookiejar_from_dict(Cookies)

# Cpdaily-Extension
extension = {
    'lon': lon,
    'lat': lat,
    'model': 'M2012K11AC',
    'appVersion': '9.0.14',
    'systemVersion': '11',
    'userId': user['username'],
    'systemName': 'android',
    'deviceId': deviceID,
}

# 提交表单规范
submitDataFormat = {
    'lon': lon,
    'lat': lat,
    'version': 'first_v3',
    'calVersion': 'firstv',
    'deviceId': deviceID,
    'userId': user['username'],
    'systemName': 'android',
    'bodyString': 'bodyString',
    'systemVersion': '11',
    'appVersion': '9.0.14',
    'model': 'M2012K11AC',
}


# md5加密
def strHash(str_: str, hash_type, charset='utf-8'):
    """计算字符串哈希"""
    hashObj = hashlib.md5()
    bstr = str_.encode(charset)
    hashObj.update(bstr)
    return hashObj.hexdigest()


# 生成表单中sign
def signAbstract(submitData: dict, key='SASEoK4Pa5d4SssO'):
    """表单中sign项目生成"""
    abstractKey = [
        'appVersion',
        'bodyString',
        'deviceId',
        'lat',
        'lon',
        'model',
        'systemName',
        'systemVersion',
        'userId',
    ]
    abstractSubmitData = {k: submitData[k] for k in abstractKey}
    abstract = urllib.parse.urlencode(abstractSubmitData) + '&' + key
    abstract_md5 = strHash(abstract, 5)
    return abstract_md5


# 查询表单
def queryForm():
    data = {'sessionToken': sessionToken}
    getModAuthCas(data)
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'User-Agent': ua,
        'content-type': 'application/json',
        'Accept-Encoding': 'gzip,deflate',
        'Accept-Language': 'zh-CN,en-US;q=0.8',
        'Content-Type': 'application/json;charset=UTF-8',
    }
    queryCollectWidUrl = f'{api}queryCollectorProcessingList'
    res = session.post(queryCollectWidUrl, headers=headers, json={'pageSize': 20, 'pageNumber': 1}).json()
    # if len(res['datas']['rows']) < 1:
    if res['datas']['totalSize'] == 0:
        return False

    collectWid = res['datas']['rows'][0]['wid']
    instanceWid = res['datas']['rows'][0]['instanceWid']
    formWid = res['datas']['rows'][0]['formWid']

    detailCollector = f'{api}detailCollector'
    res = session.post(detailCollector, headers=headers, json={'collectorWid': collectWid, 'instanceWid': instanceWid})
    schoolTaskWid = res.json()['datas']['collector']['schoolTaskWid']

    getFormFields = f'{api}getFormFields'
    res = session.post(
        getFormFields,
        headers=headers,
        json={'pageSize': 100, 'pageNumber': 1, 'formWid': formWid, 'collectorWid': collectWid},
    )
    form = res.json()['datas']['rows']

    return {
        'collectWid': collectWid,
        'instanceWid': instanceWid,
        'formWid': formWid,
        'schoolTaskWid': schoolTaskWid,
        'form': form,
    }


# 填写form
def fillForm(form):
    sort = 1
    for formItem in form:
        # 只处理必填项
        if formItem['isRequired'] == 1:
            default = config['cpdaily']['defaults'][sort - 1]['default']
            if formItem['title'] != default['title']:
                log(f'第{sort}个默认配置不正确，请检查')
                log(formItem['title'], default['title'])
                return False
            # 文本直接赋值
            if formItem['fieldType'] == '1':
                formItem['value'] = default['value']
            # 单选框需要删掉多余的选项
            if formItem['fieldType'] == '2':
                # 填充默认值
                formItem['value'] = default['value']
                fieldItems = formItem['fieldItems']
                for i in range(0, len(fieldItems))[::-1]:
                    if fieldItems[i]['content'] != default['value']:
                        del fieldItems[i]
            # 多选需要分割默认选项值，并且删掉无用的其他选项
            if formItem['fieldType'] == '3':
                fieldItems = formItem['fieldItems']
                defaultValues = default['value'].split(' ')
                for i in range(0, len(fieldItems))[::-1]:
                    flag = True
                    for j in range(0, len(defaultValues))[::-1]:
                        if fieldItems[i]['content'] == defaultValues[j]:
                            # 填充默认值
                            formItem['value'] += defaultValues[j] + ' '
                            flag = False
                    if flag:
                        del fieldItems[i]
            # 图片需要上传到阿里云oss
            if formItem['fieldType'] == '4':
                pass
                # fileName = uploadPicture(default['value'])
                # formItem['value'] = getPictureUrl(fileName)
            item = f'''必填问题{sort}：{formItem['title']}: {formItem['value']}'''
            if not isCloud:
                log(item)
            sort += 1
    return form


# 上传图片到阿里云oss
def uploadPicture(image):
    url = f'{api}getStsAccess'
    res = session.post(url, headers={'content-type': 'application/json'}, json={})
    datas = res.json().get('datas')
    fileName = datas.get('fileName')
    accessKeyId = datas.get('accessKeyId')
    accessSecret = datas.get('accessKeySecret')
    securityToken = datas.get('securityToken')
    endPoint = datas.get('endPoint')
    bucket = datas.get('bucket')
    bucket = oss2.Bucket(oss2.Auth(access_key_id=accessKeyId, access_key_secret=accessSecret), endPoint, bucket)
    with open(image, 'rb') as f:
        data = f.read()
    bucket.put_object(key=fileName, headers={'x-oss-security-token': securityToken}, data=data)
    res = bucket.sign_url('PUT', fileName, 60)
    # log(res)
    return fileName


# 获取图片上传位置
def getPictureUrl(fileName):
    url = f'{api}previewAttachment'
    data = {'ossKey': fileName}
    res = session.post(url, headers={'content-type': 'application/json'}, json=data)
    photoUrl = res.json().get('datas')
    return photoUrl


# 提交表单
def submitForm(formWid, address, collectWid, schoolTaskWid, instanceWid, form):
    headers = {
        'User-Agent': ua,
        'CpdailyStandAlone': '0',
        'extension': '1',
        'Cpdaily-Extension': DESEncrypt(extension),
        'Content-Type': 'application/json; charset=utf-8',
        # 请注意这个应该和配置文件中的host保持一致
        'Host': host,
        'Connection': 'Keep-Alive',
        'Accept-Encoding': 'gzip',
    }

    # 默认正常的提交参数json
    params = {
        'formWid': formWid,
        'address': address,
        'collectWid': collectWid,
        'schoolTaskWid': schoolTaskWid,
        'uaIsCpadaily': True,
        'latitude': lat,
        'longitude': lon,
        'instanceWid': instanceWid,
        'form': form,
    }
    # print(params)
    bodyString = encrypt_BodyString(params)
    submitDataFormat['bodyString'] = bodyString
    submitDataFormat['sign'] = signAbstract(submitDataFormat)
    submitUrl = f'{api}submitForm'
    r = session.post(submitUrl, headers=headers, json=submitDataFormat)
    return r.json()['message']


def main():
    try:
        if isCloud:
            log('当前用户：xxxxxx')
        else:
            log('当前用户：' + user['username'])
        log('脚本开始执行')
        log('正在查询最新待填写问卷')
        params = queryForm()
        assert params, '获取最新待填写问卷失败，可能是辅导员还没有发布'

        log('查询最新待填写问卷成功')
        log('正在自动填写问卷')
        form = fillForm(params['form'])
        assert form, '填写配置错误'

        log('填写问卷成功')
        log('正在自动提交')
        result = submitForm(
            params['formWid'],
            user['address'],
            params['collectWid'],
            params['schoolTaskWid'],
            params['instanceWid'],
            form,
        )
        if result == 'SUCCESS':
            msg = '提交成功！'
            log(msg)
        elif result == '该收集已填写无需再次填写':
            log('今日已提交！')
        else:
            msg = f'提交失败: {result}'
            log(msg)
    except AssertionError as e:
        msg = e
        log(msg)
    except Exception as e:
        msg = repr(e)
        print(msg)

    if isCloud:
        notify = WeChat()
        notify.send('今日校园填报', msg)


if __name__ == '__main__':
    main()
