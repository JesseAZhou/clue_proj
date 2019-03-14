from datetime import datetime
import datetime as d_time

# 各区数据缓存时间
CACHE_TIL = 10

now_day = datetime.now().date()
yesterday = now_day-d_time.timedelta(1)

remark = '定向申领'

'''工作日API接口'''
weekday_headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
    'Connection': 'keep-alive',
    'Content-Length': '41',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Cookie': 'Hm_lvt_0fa7b8c467469bd8f2eaddd5dc1d440d=1498116104; Hm_lpvt_0fa7b8c467469bd8f2eaddd5dc1d440d=1498116142',
    'Host': 'www.fynas.com',
    'Origin': 'http://www.fynas.com',
    'Referer': 'http://www.fynas.com/workday',
    'User-Agent': '/para/saleSetForOppres_query.action',
    'X-Requested-With': 'XMLHttpRequest'
}

