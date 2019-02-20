from __future__ import unicode_literals
from django.db import models
from django.db.models import Count, Sum
import calendar
import requests
import json
from .config import *

# 与eccrc同步的累计积分 和 每日积分明细
# 运营单位趋势积分表


def is_weekday(start_day, chose_day):
    url = 'http://www.fynas.com/workday/count'
    datas = 'start_date=%s&end_date=%s' % (str(start_day)[0:10], str(chose_day)[0:10])
    request = requests.post(url, headers=weekday_headers, data=datas)
    result = int(json.loads(request.content)['data']['workday'])
    return result


def real_yesterday(y_day):
    for i in range(8):
        if is_weekday(y_day, y_day) == 0:
            y_day = y_day - d_time.timedelta(1)
        else:
            break
    return y_day


def first_and_last(*check_date):
    if not check_date:
        yesterday = now_day - d_time.timedelta(1)
        check_date = real_yesterday(yesterday)
    else:
        check_date = check_date[0]
    lastday = str(calendar.monthrange(check_date.year, check_date.month)[1])
    month_firstday = datetime.strptime(datetime.strftime(check_date, '%Y-%m') + '-01', '%Y-%m-%d')
    month_lastday = datetime.strptime(datetime.strftime(check_date, '%Y-%m') + '-' + lastday, '%Y-%m-%d')
    return [month_firstday, month_lastday]


class AllManager(models.Manager):
    # 运营单位趋势图的表内容
    # 始终选择一个月的样本，无需过滤运营单位
    """选取部分天数的积分作为更新到运营单位趋势表的凭据"""
    def get_co_trade(self):
        last_month_day = first_and_last()[0] - d_time.timedelta(1)
        query_day_score = self.get_queryset().filter(deadline_date__gte=last_month_day,
                                                     deadline_date__lte=first_and_last()[1])\
            .values('op_unit_name', 'deadline_date').annotate(today_score=Sum('today_score'))\
            .values('op_unit_name', 'deadline_date', 'today_score').order_by("deadline_date")
        return query_day_score

    # 始终选择一个月的样本，需过滤运营单位
    def get_dp_trade(self, unit_name, check_date):
        """选取部分天数的积分作为更新用"""
        query_day_score = self.get_queryset().filter(op_unit_name__contains=unit_name,
                                                     deadline_date__gte=first_and_last(check_date)[0],
                                                     deadline_date__lte=check_date)\
            .values('op_unit_name', 'db', 'deadline_date').annotate(today_score=Sum('today_score'))\
            .values('op_unit_name', 'db', 'today_score', 'deadline_date').order_by('deadline_date', 'db')
        return query_day_score

    # 大部人数&月度总积分 过滤运营单位，总是显示前一天的状态
    def get_dp_reach_all(self, unit_name, check_date):  # 如何将历史数据按照月份统计内容
        """大部积分明细 de 人数，月度总积分"""
        query = self.get_queryset().filter(deadline_date=check_date, op_unit_name__contains=unit_name).values('db')\
            .annotate(man_num=Count('sale_name'), this_month_score=Sum('this_month_score'),
                      today_score=Sum('today_score'))\
            .values('op_unit_name', 'db', 'man_num', 'this_month_score', 'today_score')
        return query

    # 大部每日可用积分
    def get_dp_vaild(self, unit_name, db, check_date):
        query = self.get_queryset().filter(deadline_date=check_date, op_unit_name__contains=unit_name, db=db)\
            .values('db').annotate(vaild_rank=Sum('his_all_score')-Sum('his_cost_score')).values('db', 'deadline_date',
                                                                                                 'vaild_rank')
        return query

    # 小部人数，月度总积分
    def get_sp_reach_all(self, unit_name, check_date):
        """小部积分明细之人数，月度总积分"""
        query = self.get_queryset().filter(deadline_date=check_date, op_unit_name__contains=unit_name)\
            .values('xb', 'db', 'op_unit_name').annotate(man_num=Count('sale_name'),
                                                         this_month_score=Sum('this_month_score'))\
            .values('xb', 'db', 'op_unit_name', 'man_num', 'this_month_score')
        return query

    def get_sp_vaild(self, unit_name, xb, check_date):
        query = self.get_queryset().filter(deadline_date=check_date, op_unit_name__contains=unit_name, xb=xb)\
            .values('xb').annotate(vaild_rank=Sum('his_all_score')-Sum('his_cost_score'))\
            .values('xb', 'deadline_date', 'vaild_rank')
        return query


class DailyManager(models.Manager):
    # 大部明细积分
    def get_dp_detail(self, unit_name, check_date):
        yester_mon_firstday = datetime.strptime(datetime.strftime(real_yesterday(check_date),
                                                                  '%Y-%m')+'-01', '%Y-%m-%d')
        query_detail = self.get_queryset().filter(op_unit_name__contains=unit_name, check_date__lte=check_date,
                                                  check_date__gte=yester_mon_firstday)\
            .values('db').annotate(man=Count('sale_name'), newadd_num=Sum('newadd_num'),
                                   newadd_score=Sum('newadd_score'), pay_num=Sum('pay_num'), pay_score=Sum('pay_score'),
                                   supple_num=Sum('supple_num'), supple_score=Sum('supple_score'),
                                   supple_ph_num=Sum('supple_ph_num'), supple_ph_score=Sum('supple_ph_score'),
                                   chang_ph_num=Sum('chang_ph_num'), chang_ph_score=Sum('chang_ph_score'),
                                   chang_other_num=Sum('chang_other_num'), chang_other_score=Sum('chang_other_score'),
                                   abandon_ph_num=Sum('abandon_ph_num'), abandon_ph_score=Sum('abandon_ph_score'),
                                   chang_trade_num=Sum('chang_trade_num'), chang_trade_score=Sum('chang_trade_score'))\
            .values('man', 'newadd_num', 'newadd_score', 'pay_num', 'pay_score', 'supple_num', 'supple_score',
                    'supple_ph_num', 'supple_ph_score', 'chang_ph_num', 'chang_ph_score', 'chang_other_num',
                    'chang_other_score', 'abandon_ph_num', 'abandon_ph_score', 'chang_trade_num', 'chang_trade_score',
                    'db')\
            .all().order_by('db')
        return query_detail

    # 小部当月明细积分和
    def get_sp_detail(self, unit_name, check_date):
        yester_mon_firstday = datetime.strptime(datetime.strftime(real_yesterday(check_date),
                                                                  '%Y-%m')+'-01', '%Y-%m-%d')
        query_detail = self.get_queryset()\
            .filter(op_unit_name__contains=unit_name, check_date__lte=check_date, check_date__gte=yester_mon_firstday)\
            .values('xb').annotate(man=Count('sale_name'), newadd_num=Sum('newadd_num'),
                                   newadd_score=Sum('newadd_score'),
                                   pay_num=Sum('pay_num'), pay_score=Sum('pay_score'), supple_num=Sum('supple_num'),
                                   supple_score=Sum('supple_score'), supple_ph_num=Sum('supple_ph_num'),
                                   supple_ph_score=Sum('supple_ph_score'), chang_ph_num=Sum('chang_ph_num'),
                                   chang_ph_score=Sum('chang_ph_score'), chang_other_num=Sum('chang_other_num'),
                                   chang_other_score=Sum('chang_other_score'), abandon_ph_num=Sum('abandon_ph_num'),
                                   abandon_ph_score=Sum('abandon_ph_score'), chang_trade_num=Sum('chang_trade_num'),
                                   chang_trade_score=Sum('chang_trade_score'))\
            .values('man', 'newadd_num', 'newadd_score', 'pay_num', 'pay_score', 'supple_num', 'supple_score',
                    'supple_ph_num', 'supple_ph_score', 'chang_ph_num', 'chang_ph_score', 'chang_other_num',
                    'chang_other_score', 'abandon_ph_num', 'abandon_ph_score', 'chang_trade_num', 'chang_trade_score',
                    'db', 'xb').order_by('xb')
        return query_detail

    # 某人明细积分和
    def get_per_detail(self, unit_name, check_date, sale_name):
        mon_firstday = datetime.strptime(datetime.strftime(check_date, '%Y-%m')+'-01', '%Y-%m-%d')
        query_detail = self.get_queryset()\
            .filter(op_unit_name__contains=unit_name, sale_name=sale_name, check_date__lte=check_date,
                    check_date__gte=mon_firstday)\
            .values('sale_name').annotate(newadd_num_mon=Sum('newadd_num'), pay_num_mon=Sum('pay_num'),
                                          supple_num_mon=Sum('supple_num'), supple_ph_num_mon=Sum('supple_ph_num'),
                                          chang_ph_num_mon=Sum('chang_ph_num'),
                                          chang_other_num_mon=Sum('chang_other_num'),
                                          abandon_ph_num_mon=Sum('abandon_ph_num'),
                                          chang_trade_num_mon=Sum('chang_trade_num'))\
            .values('sale_name', 'newadd_num_mon', 'pay_num_mon', 'supple_num_mon', 'supple_ph_num_mon',
                    'chang_ph_num_mon', 'chang_other_num_mon', 'abandon_ph_num_mon', 'chang_trade_num_mon', 'db', 'xb')\
            .order_by('xb')
        return query_detail

    # 个人某日积分明细
    def get_per_detail_day(self, unit_name, check_date, sale_name):
        query_detail = self.get_queryset()\
            .filter(op_unit_name__contains=unit_name, check_date=check_date, sale_name=sale_name)\
            .all().order_by('xb')
        return query_detail

    # 小部日积分明细
    def get_detail_day_xb(self, unit_name, check_date, xb):
        query_detail = self.get_queryset()\
            .filter(op_unit_name__contains=unit_name, xb=xb, check_date=check_date).all()
        return query_detail

    # 小部月积分明细
    def get_detail_xb(self, unit_name, check_date, xb):
        mon_firstday = datetime.strptime(datetime.strftime(check_date, '%Y-%m') + '-01', '%Y-%m-%d')
        query_detail = self.get_queryset()\
            .filter(op_unit_name__contains=unit_name, xb=xb, check_date__lte=check_date, check_date__gte=mon_firstday)\
            .values('sale_name').annotate(newadd_num_mon=Sum('newadd_num'), pay_num_mon=Sum('pay_num'),
                                          supple_num_mon=Sum('supple_num'), supple_ph_num_mon=Sum('supple_ph_num'),
                                          chang_ph_num_mon=Sum('chang_ph_num'),
                                          chang_other_num_mon=Sum('chang_other_num'),
                                          abandon_ph_num_mon=Sum('abandon_ph_num'),
                                          chang_trade_num_mon=Sum('chang_trade_num'))\
            .values('sale_name', 'newadd_num_mon', 'pay_num_mon', 'supple_num_mon', 'supple_ph_num_mon',
                    'chang_ph_num_mon', 'chang_other_num_mon', 'abandon_ph_num_mon', 'chang_trade_num_mon', 'db', 'xb')
        return query_detail

    # 新增线索统计
    def get_new_add_count(self, unit_name, check_date):
        query_detail = self.get_queryset()\
            .filter(op_unit_name__contains=unit_name, check_date__gte=first_and_last(check_date)[0],
                    check_date__lte=check_date)\
            .values('db').annotate(new_count=Sum('newadd_num')).values('db', 'new_count')
        query_detail = tuple(query_detail)
        return query_detail


# 新增和增补的明细 及 被驳回的类型和对应的量
class CheckManager(models.Manager):
    # 啥都没有 只显示驳回，有日期显示所有，有日期姓名显示个人的所有
    def get_detail(self, unit_name, check_date, sale_name):  # op_unit_name
        if check_date and not sale_name:
            query_detail = self.get_queryset()\
                .filter(check_date=check_date, checking_result='驳回', op_unit_name__contains=unit_name)\
                .all().order_by('db', 'xb')
        elif check_date and sale_name:
            query_detail = self.get_queryset()\
                .filter(sale_name=sale_name, check_date=check_date, checking_result='驳回',
                        op_unit_name__contains=unit_name).all().order_by('db', 'xb')
        else:
            query_detail = {}
        return query_detail


# 变更单驳回的明细 及 被驳回的类型和对应的量
def count_day(a_time):
    # import datetime
    a_time = datetime.strptime(a_time, '%Y-%m-%d')
    day_start = a_time - d_time.timedelta(1)
    day_end = a_time + d_time.timedelta(1)
    day_end = datetime.date(day_end)
    day_start = datetime.date(day_start)
    day_cal = [day_start, day_end]
    return day_cal


class ChangeCheckManager(models.Manager):
    def get_detail(self, unit_name, check_date, sale_name):  # op_unit_name
        if check_date and not sale_name:
            query_detail = self.get_queryset()\
                .filter(check_time__gte=check_date, checking_result='驳回', op_unit_name__contains=unit_name)\
                .all().order_by('db')
        elif check_date and sale_name:
            query_detail = self.get_queryset().filter(
                sale_name=sale_name, check_time__gte=count_day(check_date)[0],
                check_time__lte=count_day(check_date)[1], checking_result='驳回',
                op_unit_name__contains=unit_name).all().order_by('db')
        else:
            query_detail = {}
        return query_detail

    #  变更单发起量
    def get_count(self, unit_name, check_date):  # op_unit_name
        query_detail = self.get_queryset().filter(
            op_unit_name__contains=unit_name, chang_time__gte=first_and_last(check_date)[0],
            chang_time__lte=check_date
        ).values('db').annotate(chang_sum=Count('change_id')).values('db', 'change_id')

        return query_detail


class CountManager(models.Manager):
    # 被驳回的新增量，变更量，增补
    def get_back_spart(self, unit_name, xp, check_date):
        query_sum = self.get_queryset()\
            .filter(check_date__gte=first_and_last(check_date)[0], check_date__lte=check_date,
                    op_unit_name__contains=unit_name, xb=xp).all()
        add_sum = chang_sum = supple_sum = 0
        for obj in query_sum:
            add_sum += obj.newadd_down_num
            chang_sum += obj.other_down_num
            supple_sum += obj.supp_down_num
        count = [add_sum, chang_sum, supple_sum]
        return count

    def get_back_num(self, unit_name, check_date):  # op_unit_name
        query_sum = self.get_queryset()\
            .filter(check_date__gte=first_and_last(check_date)[0], check_date__lte=check_date,
                    op_unit_name__contains=unit_name)\
            .values('db').annotate(add_sum=Sum('newadd_down_num'), chang_sum=Sum('other_down_num'))\
            .values('db', 'add_sum', 'chang_sum')
        query_sum = tuple(query_sum)
        return query_sum


class NoticeDay(models.Model):
    objects = models.Manager()
    id = models.AutoField(primary_key=True)
    op_unit_name = models.CharField(max_length=20, choices=(('广州', '广州'), ('上海', '上海'),
                                                            ('深', '深圳'), ('东莞', '东莞')))
    create_date = models.DateField(auto_now_add=True)
    note = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return u'%s  %s  %s' % (self.op_unit_name, self.create_date, self.note)

    class Meta:
        db_table = "clue_notice_day"
        verbose_name = '每日公告栏'
        verbose_name_plural = '每日公告栏'


class Log(models.Model):
    objects = models.Manager()
    id = models.AutoField(primary_key=True)
    remote_addr = models.CharField(max_length=50, null=False)
    invite_time = models.DateTimeField(null=False)
    invite_area = models.CharField(max_length=20, null=False)

    def __unicode__(self):
        return u'%s__%s__%s' % (self.remote_addr, self.invite_area, self.invite_time)

    class Meta:
        db_table = 'clue_log'
        verbose_name = '访问记录'
        verbose_name_plural = '访问记录'


class All(models.Model):
    objects = models.Manager()
    id = models.BigAutoField(primary_key=True)
    op_unit_name = models.CharField(max_length=255, blank=True, null=True)
    db = models.CharField(db_column='DB', max_length=255, blank=True, null=True)  # Field name made lowercase.
    xb = models.CharField(db_column='XB', max_length=255, blank=True, null=True)  # Field name made lowercase.
    sale_name = models.CharField(max_length=255, blank=True, null=True)
    sale_num = models.CharField(max_length=255, blank=True, null=True)
    deadline_date = models.DateField(max_length=10, blank=True, null=True)
    his_all_score = models.FloatField(blank=True, null=True)
    his_cost_score = models.FloatField(blank=True, null=True)
    today_score = models.FloatField(blank=True, null=True)
    today_cost_score = models.FloatField(blank=True, null=True)
    score_balance = models.FloatField(blank=True, null=True)
    this_month_score = models.FloatField(blank=True, null=True)
    this_month_cost_score = models.FloatField(blank=True, null=True)
    g_pdate = models.CharField(max_length=10, blank=True, null=True)
    orm_objects = AllManager()

    class Meta:
        db_table = "clue_all"
        verbose_name = "累计积分汇总表（同步）"


class Daily(models.Model):
    objects = models.Manager()
    id = models.BigAutoField(primary_key=True)
    op_unit_name = models.CharField(max_length=255, blank=True, null=True)
    db = models.CharField(db_column='DB', max_length=255, blank=True, null=True)  # Field name made lowercase.
    xb = models.CharField(db_column='XB', max_length=255, blank=True, null=True)  # Field name made lowercase.
    sale_name = models.CharField(max_length=255, blank=True, null=True)
    sale_num = models.CharField(max_length=255, blank=True, null=True)
    check_date = models.DateField(max_length=10, blank=True, null=True)
    newadd_num = models.FloatField(blank=True, null=True)
    newadd_score = models.FloatField(blank=True, null=True)
    pay_num = models.FloatField(blank=True, null=True)
    pay_score = models.FloatField(blank=True, null=True)
    supple_num = models.FloatField(blank=True, null=True)
    supple_score = models.FloatField(blank=True, null=True)
    supple_ph_num = models.FloatField(blank=True, null=True)
    supple_ph_score = models.FloatField(blank=True, null=True)
    chang_ph_num = models.FloatField(blank=True, null=True)
    chang_ph_score = models.FloatField(blank=True, null=True)
    chang_other_num = models.FloatField(blank=True, null=True)
    chang_other_score = models.FloatField(blank=True, null=True)
    abandon_ph_num = models.FloatField(blank=True, null=True)
    abandon_ph_score = models.FloatField(blank=True, null=True)
    chang_trade_num = models.FloatField(blank=True, null=True)
    chang_trade_score = models.FloatField(blank=True, null=True)
    today_score = models.FloatField(blank=True, null=True)
    g_pdate = models.CharField(max_length=10, blank=True, null=True)
    orm_objects = DailyManager()

    class Meta:
        db_table = "clue_daily"
        verbose_name = "每日积分明细(同步)"


# 新增质检明细
class CreateCheck(models.Model):
    objects = models.Manager()
    id = models.BigAutoField(primary_key=True)
    op_unit_name = models.CharField(max_length=255, blank=True, null=True)
    db = models.CharField(db_column='DB', max_length=255, blank=True, null=True)  # Field name made lowercase.
    xb = models.CharField(db_column='XB', max_length=255, blank=True, null=True)  # Field name made lowercase.
    sale_name = models.CharField(max_length=255, blank=True, null=True)
    pg_cust_id = models.CharField(max_length=255, blank=True, null=True)
    full_info = models.CharField(max_length=255, blank=True, null=True)
    pg_cust_type = models.CharField(max_length=255, blank=True, null=True)
    pg_cust_status = models.CharField(max_length=255, blank=True, null=True)
    hint_src_id_1 = models.CharField(max_length=255, blank=True, null=True)
    city_id = models.CharField(max_length=255, blank=True, null=True)
    create_post_id = models.CharField(max_length=255, blank=True, null=True)
    create_user_id = models.CharField(max_length=255, blank=True, null=True)
    create_time = models.DateTimeField(blank=True, null=True)
    audit_time = models.DateTimeField(blank=True, null=True)
    audit_result_id = models.CharField(max_length=255, blank=True, null=True)
    audit_result_value = models.CharField(max_length=255, blank=True, null=True)
    protect_time = models.DateTimeField(blank=True, null=True)
    un_protect_time = models.DateTimeField(blank=True, null=True)
    newadd_type = models.CharField(max_length=255, blank=True, null=True)
    pos_name = models.CharField(max_length=255, blank=True, null=True)
    checkornot = models.CharField(max_length=255)
    checking_result = models.CharField(max_length=255)
    whyturndown = models.CharField(max_length=255)
    check_man = models.CharField(max_length=255)
    check_date = models.DateField(max_length=255)
    remark = models.CharField(max_length=255, blank=True, null=True)
    g_pdate = models.DateField(max_length=10)
    orm_objects = CheckManager()

    class Meta:
        db_table = "clue_create_check"
        verbose_name = "新增驳回明细(同步)"


# 变更单之间明细
class ChangeCheck(models.Model):
    objects = models.Manager()
    id = models.BigAutoField(primary_key=True)
    op_unit_name = models.CharField(max_length=255, blank=True, null=True)
    db = models.CharField(db_column='DB', max_length=255, blank=True, null=True)  # Field name made lowercase.
    xb = models.CharField(db_column='XB', max_length=255, blank=True, null=True)  # Field name made lowercase.
    sale_name = models.CharField(max_length=255, blank=True, null=True)
    change_id = models.TextField(blank=True, null=True)
    change_type = models.TextField(blank=True, null=True)
    pg_cust_id = models.TextField(blank=True, null=True)
    change_item = models.TextField(blank=True, null=True)
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    whychange = models.TextField(blank=True, null=True)
    changeremark = models.TextField(blank=True, null=True)
    checkingremark = models.TextField(blank=True, null=True)
    pos_id = models.TextField(blank=True, null=True)
    pos_name = models.TextField(blank=True, null=True)
    chang_time = models.DateField(blank=True, null=True)
    checking_result = models.TextField(blank=True, null=True)
    check_pos = models.TextField(blank=True, null=True)
    check_man_pos = models.TextField(blank=True, null=True)
    check_time = models.DateTimeField(blank=True, null=True)
    supple_ph = models.SmallIntegerField(blank=True, null=True)
    chang_ph = models.SmallIntegerField(blank=True, null=True)
    chang_other = models.SmallIntegerField(blank=True, null=True)
    abandon_ph = models.SmallIntegerField(blank=True, null=True)
    check_man = models.TextField(blank=True, null=True)
    g_pdate = models.DateField(max_length=10, blank=True, null=True)
    orm_objects = ChangeCheckManager()

    class Meta:
        db_table = "clue_other_modify"
        verbose_name = "变更单驳回明细(同步)"


# 增补质检明细
class SuppleCheck(models.Model):
    objects = models.Manager()
    id = models.BigAutoField(primary_key=True)
    op_unit_name = models.CharField(max_length=255, blank=True, null=True)
    db = models.CharField(db_column='DB', max_length=255, blank=True, null=True)  # Field name made lowercase.
    xb = models.CharField(db_column='XB', max_length=255, blank=True, null=True)  # Field name made lowercase.
    sale_name = models.CharField(max_length=255, blank=True, null=True)
    pg_cust_id = models.CharField(max_length=255, blank=True, null=True)
    full_info = models.CharField(max_length=255, blank=True, null=True)
    full_info_status = models.CharField(max_length=255, blank=True, null=True)
    contact_type = models.CharField(max_length=255, blank=True, null=True)
    pg_cust_type = models.CharField(max_length=255, blank=True, null=True)
    pg_cust_status = models.CharField(max_length=255, blank=True, null=True)
    city_id = models.CharField(max_length=255, blank=True, null=True)
    cust_create_post_id = models.CharField(max_length=255, blank=True, null=True)
    cust_create_pos_name = models.CharField(max_length=255, blank=True, null=True)
    cust_create_time = models.DateTimeField(blank=True, null=True)
    cust_create_user_id = models.CharField(max_length=255, blank=True, null=True)
    full_info_create_time = models.DateTimeField(blank=True, null=True)
    full_info_create_user_id = models.CharField(max_length=255, blank=True, null=True)
    full_info_create_pos_name = models.CharField(max_length=255, blank=True, null=True)
    pdate = models.DateField(max_length=10, blank=True, null=True)
    checkornot = models.CharField(max_length=255)
    checking_result = models.CharField(max_length=255)
    whyturndown = models.CharField(max_length=255)
    check_man = models.CharField(max_length=255)
    check_date = models.DateField(max_length=255, blank=True, null=True)
    remark = models.CharField(max_length=255, blank=True, null=True)
    g_pdate = models.DateField(max_length=10)
    orm_objects = CheckManager()

    class Meta:
        db_table = "clue_supple_check"
        verbose_name = "批量增补驳回明细(同步)"


# 质检量统计
class CheckCount(models.Model):
    objects = models.Manager()
    id = models.BigAutoField(primary_key=True)
    op_unit_name = models.CharField(max_length=255, blank=True, null=True)
    db = models.CharField(db_column='DB', max_length=255, blank=True, null=True)  # Field name made lowercase.
    xb = models.CharField(db_column='XB', max_length=255, blank=True, null=True)  # Field name made lowercase.
    sale_name = models.CharField(max_length=255, blank=True, null=True)
    sale_num = models.CharField(max_length=255, blank=True, null=True)
    check_date = models.DateField(max_length=10, blank=True, null=True)
    newadd_down_num = models.FloatField("新增驳回量", null=True)
    other_down_num = models.FloatField("变更单驳回量", null=True)
    supp_down_num = models.FloatField("增补驳回量", null=True)
    orm_objects = CountManager()

    class Meta:
        db_table = "clue_check_count"
        verbose_name = "质检量统计"


class MonthGoal(models.Model):
    objects = models.Manager()
    id = models.BigAutoField(primary_key=True)
    op_unit_name = models.CharField("运营单位", max_length=20, null=True)
    city_id = models.CharField(max_length=10, blank=True, null=True)
    goal_date = models.DateField("积分日期", null=True)
    avg_score_goal = models.FloatField("人月目标积分", null=True)
    g_pdate = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "clue_month_goal"
        verbose_name = "月度人均目标积分(同步)"


# 凡申领获取的资源都作保存记录，在一段时间外的进行删除，剩余的分成功申领和申领失败留作下次继续
class OrderStatus(models.Model):
    objects = models.Manager()
    sale_id = models.CharField("销售id", max_length=20, null=False)
    opp_id = models.CharField("商业资源id", max_length=50, null=False)
    create_time = models.DateTimeField("申领时间", null=False)
    status = models.BooleanField("申领状态", default=0)

    class Meta:
        db_table = "clue_order"
        verbose_name = "申领状态"
