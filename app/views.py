from django.shortcuts import render
from django.views.decorators.cache import cache_page
from django_redis import cache
from .models import *
from .config import *
import json


# 返回 大部小部 人员数和 运营单位月目标积分，
def dp_goal_num(op_unit_name, chose_date):
    goal_date = datetime.strptime(datetime.strftime(chose_date, '%Y-%m') + '-01', '%Y-%m-%d')
    lastday = str(calendar.monthrange(chose_date.year, chose_date.month)[1])
    end_date = datetime.strptime(datetime.strftime(chose_date, '%Y-%m') + '-' + str(lastday).zfill(2), '%Y-%m-%d')
    now_weekday = is_weekday(goal_date, chose_date)
    month_weekday = is_weekday(goal_date, end_date)
    remain_day = month_weekday - now_weekday
    time_rate = round(float(now_weekday) * 100 / float(month_weekday), 1) if month_weekday > 0 else 0

    # avg goal score of every month
    person_goal = now_person_goal(op_unit_name, goal_date)
    avg_score_goal = person_goal.avg_score_goal if person_goal else 0

    # 大部，大部人数；小部，小部人数；整个运营单位的人均月目标；到当前的工作日，一个月的工作日
    goal_dict = {'person_goal': avg_score_goal, 'now_weekday': now_weekday, 'month_weekday': month_weekday,
                 'remain_day': remain_day, 'time_rate': time_rate}
    return goal_dict


# 获取当前使用的月人均目标，无该月人均目标是沿用上月目标
def now_person_goal(op_unit_name, now_goal_date):
    person_goal = MonthGoal.objects.filter(op_unit_name__contains=op_unit_name, goal_date=now_goal_date).first()
    if not person_goal:
        if now_goal_date.month == 1:
            recent_goal_date = str(now_goal_date.year-1) + '-' + str(now_goal_date.month+11).zfill(2)+'-01'
        else:
            recent_goal_date = str(now_goal_date.year) + '-' + str(now_goal_date.month-1).zfill(2)+'-01'
        person_goal = MonthGoal.objects.filter(op_unit_name__contains=op_unit_name).first()
    return person_goal


# 首页刷新缓存：大部积分明细/小部积分/个人积分的计算存入数据库 + 运营单位每月每日积分趋势的计算和显示
def home_page(request):
    this_month_day = int(calendar.monthrange(yesterday.year, yesterday.month)[1])
    this_month_day_list = [datetime.strftime(yesterday, '%Y-%m') + '-' +
                           str(d).zfill(2) for d in range(1, this_month_day + 1)]
    lastmonth_finalday = str(first_and_last(yesterday)[0]-d_time.timedelta(1))[0:10]
    this_month_day_list.insert(0, lastmonth_finalday)
    invite_log = Log.objects.all()
    invite_men = len(invite_log) if invite_log else 0
    unit_trade = All.orm_objects.get_co_trade()

    if not unit_trade:
        return render(request, 'all_co.html', {
            "trade": None,
            "unit_list": None,
            "this_month": this_month_day_list,
            "invite_men": invite_men
        })

    unit_list = []
    for value in unit_trade.iterator():
        if value['op_unit_name'] not in unit_list:
            unit_list.append(value['op_unit_name'])
    # {'运营单位':[分数列表],'运营单位2':[分数列表]}
    trade_value = {}
    for unit in unit_list:
        trade_value[unit] = this_month_day_list[:]
        for obj in unit_trade:
            if unit != obj['op_unit_name']:
                continue
            else:
                for i in range(this_month_day):
                    if trade_value[unit][i] == datetime.strftime(obj['deadline_date'], '%Y-%m-%d'):
                        trade_value[unit][i] = obj['today_score']

        for i in range(len(trade_value[unit])):
            if not isinstance(trade_value[unit][i], float):
                trade_value[unit][i] = 0

    unit_list = json.dumps(unit_list)

    return render(request, 'all_co.html', {
        "trade": trade_value,
        "unit_list": unit_list,
        "this_month": this_month_day_list,
        "invite_men": invite_men
        })


# 大部小部积分明细,大部趋势
# @cache_page(60*60, cache='default',key_prefix='detail')
# @cache_page(CACHE_TIL)
def detail_score(request):
    check_date = datetime.strptime(request.GET.get('check_date'), '%Y-%m-%d').date() \
        if request.GET.get('check_date') else yesterday
    check_date = real_yesterday(check_date)
    # 查看分区的记录
    remote_addr = request.META['REMOTE_ADDR']
    log_time = datetime.now()
    op_unit_name = request.GET.get("unit")
    import logging
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(message)s',
                        datefmt='%a, %d %b %Y %H:%M:%S',
                        filename='invite_log.log',
                        filemode='w')
    message = 'IP地址:' + remote_addr + ',' + '查看分区:' + op_unit_name
    logging.info(message)
    invite_log = Log(remote_addr=remote_addr, invite_time=log_time, invite_area=op_unit_name)
    invite_log.save()

    this_month_day = int(calendar.monthrange(check_date.year, check_date.month)[1])
    this_month_day_list = [datetime.strftime(check_date, '%Y-%m') + '-' + str(d).zfill(2) for d in
                           range(1, this_month_day + 1)]

    # 大部趋势数据
    """大部趋势图数据"""
    dp_trade = All.orm_objects.get_dp_trade(op_unit_name, check_date)
    trade_value = {}
    part_list = []  # 大部列表
    for i in dp_trade:
        if not i['db'] in part_list:
            part_list.append(i['db'])
        else:
            continue

    # trade_value:{"广州":[1,2,3,4,5,67,...],"深圳":[2,32,43,545,65,234,12,123,34]}
    for dp in part_list:
        trade_value[dp] = this_month_day_list[:]
        for obj in dp_trade:
            if dp != obj['db']:
                continue
            else:
                for i in range(len(trade_value[dp])):
                    if trade_value[dp][i] == datetime.strftime(obj['deadline_date'], '%Y-%m-%d'):
                        trade_value[dp][i] = obj['today_score']
        for i in range(len(trade_value[dp])):
            if not isinstance(trade_value[dp][i], float):
                trade_value[dp][i] = 0

    """ 部门驳回占比情况"""
    # day表获取新增线索数据，check_count 获取驳回量
    count_list = sorted(part_list)
    part_list = json.dumps(part_list)
    count = {}  # count:{A:{新增:3,驳回:1...}}

    # 新增驳回数/
    new_sum = Daily.orm_objects.get_new_add_count(op_unit_name, check_date)
    back_count = CheckCount.orm_objects.get_back_num(op_unit_name, check_date)
    change_sum = ChangeCheck.orm_objects.get_count(op_unit_name, check_date)
    for dp in count_list:
        count[dp] = {}
        if not back_count:
            count[dp]['create_back_num'] = 0
            count[dp]['change_back_num'] = 0
        else:
            for value in back_count:
                if value['db'] == dp:
                    count[dp]['create_back_num'] = value['add_sum']
                    count[dp]['change_back_num'] = value['chang_sum']
        if not new_sum:
            count[dp]['create_num'] = 0
        else:
            for value in new_sum:
                if value['db'] == dp:
                    count[dp]['create_num'] = value['new_count']

        change_list = []
        for value in change_sum:
            if value['db'] == dp:
                change_list.append(value['change_id'])

        count[dp]['change_num'] = len(change_list) if change_list else 0
        count[dp]['create_percent'] = round(float(count[dp]['create_back_num'])*100/float(count[dp]['create_num']), 1) \
            if 'create_num' in count[dp] and ('create_back_num' in count[dp]) and count[dp]['create_num'] > 0 else 0
        count[dp]['change_percent'] = round(float(count[dp]['change_back_num'])*100/float(count[dp]['change_num']), 1) \
            if count[dp]['change_num'] > 0 else 0

    ''' 小部积分明细 '''
    # 大部，大部人数；小部，小部人数；整个运营单位的人均月目标；到当前的工作日，一个月的工作日
    # goal_dict = {'dp_man_nums':set[{db:A,man:4},{db:B,man:10}],'sp_man_nums':set[{xb:A1,man:4},
    # {xb:B1,man:10}],'person_goal':person_goal,'now_weekday':now_weekday,'month_weekday':month_weekday,
    # remain_day:13,time_rate:21.8%}
    goal_dict = dp_goal_num(op_unit_name, check_date)
    man_goal = goal_dict['person_goal']  # 该运营单位的月人均目标
    sp_detail = Daily.orm_objects.get_sp_detail(op_unit_name, check_date)
    for sp in sp_detail:
        # real_man = Daily.objects.filter(op_unit_name__contains=op_unit_name, check_date=check_date, xb=sp['xb'])
        real_man = Daily.objects.filter(op_unit_name__contains=op_unit_name, xb=sp['xb'])
        sp['man'] = len(real_man) if real_man else 0
        back_sp_set = CheckCount.orm_objects.get_back_spart(op_unit_name, sp['xb'], check_date)
        sp['new_back_num'] = back_sp_set[0]
        sp['other_back_num'] = back_sp_set[1]
        sp['supp_back_num'] = back_sp_set[2]

    sp_man_real = All.orm_objects.get_sp_reach_all(op_unit_name, check_date)  # 小部人数 当月积分
    sp_summary = []
    for summary in sp_man_real:
        man_num = summary['man_num']
        man_reach = All.objects.filter(op_unit_name__contains=op_unit_name, this_month_score__gte=man_goal,
                                       xb=summary['xb']).all() if man_goal > 0 else {}
        sp = dict()
        sp['dpart'] = summary['db']
        sp['spart'] = summary['xb']
        sp['man_num'] = man_num
        sp['reach_rate'] = round(float(len(man_reach))*100/float(man_num), 1) if man_num > 0 else 0
        sp['comp_rate'] = round(float(summary['this_month_score'])*100/float(man_goal*man_num), 1)\
            if man_goal*man_num > 0 else 0
        sp['vaild'] = All.orm_objects.get_sp_vaild(op_unit_name, summary['xb'], check_date)[0]['vaild_rank']
        sp['month_goal'] = summary['man_num'] * man_goal
        sp['month_score'] = summary['this_month_score']
        sp_summary.append(sp)
    # 今日的小部积分数据 sp_score:{'xb1':{"":'',"":''}.'xb2':{"":''}}

    ''' 大部积分明细 '''
    dp_detail = Daily.orm_objects.get_dp_detail(op_unit_name, check_date)
    for dp in dp_detail:
        # real_man = Daily.objects.filter(op_unit_name__contains=op_unit_name, check_date=check_date, db=dp['db'])
        real_man = Daily.objects.filter(op_unit_name__contains=op_unit_name, db=dp['db'])
        # dp['man'] = real_man[0]['man']
        dp['man'] = len(real_man) if real_man else 0

    dp_sum_real = All.orm_objects.get_dp_reach_all(op_unit_name, check_date)
    dp_summary = []
    for summary in dp_sum_real:
        man_num = summary['man_num']
        man_reach = All.objects.filter(op_unit_name__contains=op_unit_name,
                                       this_month_score__gte=man_goal, deadline_date=check_date, db=summary['db'])\
            if man_goal > 0 else {}
        dp = dict()
        dp['dpart'] = summary['db']
        dp['man'] = man_num
        dp['reach_rate'] = round(float(len(man_reach))*100/float(man_num), 1) if man_num > 0 else 0
        dp['comp_rate'] = round(float(summary['this_month_score'])*100/float(man_goal*man_num), 1) \
            if man_goal*man_num > 0 else 0
        dp['vaild'] = All.orm_objects.get_dp_vaild(op_unit_name, summary['db'], check_date)[0]['vaild_rank']
        dp['month_goal'] = summary['man_num'] * man_goal
        dp['month_score'] = summary['this_month_score']
        # dp['today_score'] = summary['today_score']
        dp_summary.append(dp)
    all_dp_goal = sum([goal['month_goal'] for goal in dp_summary])
    all_dp_score = sum([goal['month_score'] for goal in dp_summary])
    # today_score = sum([goal['today_score'] for goal in dp_summary])
    proj_rate = round(float(all_dp_score) * 100 / float(all_dp_goal), 1) if all_dp_goal > 0 else 0

    # 每日公告栏
    note_day = NoticeDay.objects.filter(create_date=check_date, op_unit_name=op_unit_name).order_by('-id').first()
    return render(request, 'index.html', {
        'back_count': count,
        'dp_detailscore': dp_detail,
        'dp_summary': dp_summary,
        'sp_detailscore': sp_detail,
        'sp_summary': sp_summary,
        'db_trade': trade_value,
        'db_trade_part': part_list,
        'this_month': this_month_day_list,
        'remain_day': goal_dict['remain_day'],
        'time_rate': goal_dict['time_rate'],
        'proj_rate': proj_rate,
        # 'all_dp_score':all_dp_score,
        # 'today_score':today_score,
        'unit': op_unit_name,
        'notice_day': note_day,
        'check_date': check_date
        })


# 个人当前积分排名
def person_rank(request):
    unit = request.GET.get('unit') if request.GET.get('unit') else ''
    deadline_date = datetime.strptime(request.GET.get('deadline_date'), '%Y-%m-%d').date() \
        if request.GET.get('deadline_date') else ''
    sale_name = request.GET.get('sale_name')
    lowest_score = int(request.GET.get('lowest_score')) if request.GET.get('lowest_score') else 50000
    if not deadline_date:
        per_rank = All.objects.filter(op_unit_name__contains=unit, deadline_date=yesterday)\
            .all().order_by('-this_month_score')
    else:
        per_rank = All.objects.filter(op_unit_name__contains=unit, deadline_date=deadline_date)\
            .all().order_by('-this_month_score')
    num_index = 1
    rank = []
    check_rank = {}
    for obj in per_rank:
        if obj.this_month_score > lowest_score:
            continue
        i_rank = dict()
        i_rank['index'] = num_index
        i_rank['xb'] = obj.xb
        i_rank['sale_name'] = obj.sale_name
        i_rank['this_month_score'] = obj.this_month_score
        if obj.deadline_date == deadline_date and obj.sale_name == sale_name:
            check_rank = i_rank
        num_index += 1
        rank.append(i_rank)
    if check_rank:
        rank = [check_rank]

    return render(request, 'person_rank.html', {
        'per_rank': rank,
        'unit': unit
        })


# 个人积分明细
def person_detail(request):
    unit = request.GET.get('unit') if request.GET.get('unit') else ''
    check_date = datetime.strptime(request.GET.get('check_date'), '%Y-%m-%d').date() \
        if request.GET.get('check_date') else None
    sale_name = request.GET.get('sale_name') if request.GET.get('sale_name') else None
    xb = request.GET.get('xb')
    deadline_date = check_date if check_date else real_yesterday(yesterday)
    xb_list = All.objects.filter(op_unit_name__contains=unit, deadline_date=deadline_date)\
        .values('xb').annotate(today_sum=Sum('today_score')).values('xb')
    avg_score_goal = 0
    if check_date:
        goal_date = datetime.strptime(datetime.strftime(check_date, '%Y-%m') + '-01', '%Y-%m-%d')
        # person_goal = monthGoal.objects.filter(op_unit_name__contains = unit, goal_date = goal_date).all()
        person_goal = now_person_goal(unit, goal_date)
        avg_score_goal = person_goal.avg_score_goal if person_goal else 0

    if not check_date:
        per_day_detail = {}
        per_mon_detail = {}
    elif xb and not sale_name:
        per_day_detail = Daily.orm_objects.get_detail_day_xb(unit, check_date, xb)
        per_mon_detail = Daily.orm_objects.get_detail_xb(unit, check_date, xb)
    else:
        per_day_detail = Daily.orm_objects.get_per_detail_day(unit, check_date, sale_name)
        per_mon_detail = Daily.orm_objects.get_per_detail(unit, check_date, sale_name)

    for person in per_day_detail:
        for mon in per_mon_detail:
            if mon['sale_name'] == person.sale_name:  # and mon[sale_num]==person[sale_num]
                person.newadd_num_mon = mon['newadd_num_mon']
                person.pay_num_mon = mon['pay_num_mon']
                person.supple_num_mon = mon['supple_num_mon']
                person.supple_ph_num_mon = mon['supple_ph_num_mon']
                person.chang_ph_num_mon = mon['chang_ph_num_mon']
                person.chang_other_num_mon = mon['chang_other_num_mon']
                person.abandon_ph_num_mon = mon['abandon_ph_num_mon']
                person.chang_trade_num_mon = mon['chang_trade_num_mon']
                all_data = All.objects.filter(op_unit_name__contains=unit, sale_name=person.sale_name,
                                              deadline_date=check_date).first()
                person.score_month = all_data.this_month_score
                person.goal = avg_score_goal
                person.over_percent = round(float(person.score_month)*100/float(avg_score_goal), 1) \
                    if avg_score_goal > 0 else 0
                person.history_score = all_data.his_all_score-all_data.his_cost_score
                person.today_score = all_data.today_score
    return render(request, 'person_detail.html', {
        'per_detail': per_day_detail,
        'unit': unit,
        'xb_list': xb_list
        })


# 驳回明细
def reject_detail(request):
    unit_name = request.GET.get('unit') if request.GET.get('unit') else ''
    # 根据返回的时间和人名返回所有或个人的三种明细
    check_date = request.GET.get("reject_date") if request.GET.get("reject_date") else ''
    sale_name = request.GET.get("sale_name") if request.GET.get("sale_name") else ''
    create_check = CreateCheck.orm_objects.get_detail(unit_name, check_date, sale_name)
    change_check = ChangeCheck.orm_objects.get_detail(unit_name, check_date, sale_name)
    supple_check = SuppleCheck.orm_objects.get_detail(unit_name, check_date, sale_name)

    return render(request, 'reject_de.html', {
        "create_check": create_check,
        "change_check": change_check,
        "supple_check": supple_check,
        "unit": unit_name
        })


# 驳回统计-员工驳回数量统计
def reject_count(request):
    unit_name = request.GET.get('unit') if request.GET.get('unit') else ''
    check_date = request.GET.get('reject_date') if request.GET.get("reject_date") else ''
    if not check_date:
        back_per_set = {}
    else:
        mon_firstday = datetime.strptime(check_date[:-3] + '-01', '%Y-%m-%d')
        # back_per_set = checkCount.objects.filter(op_unit_name__contains = unit_name, check_date__lte = check_date,
        # check_date__gte = mon_firstday).all().order_by('-newadd_down_num','-other_down_num','-supp_down_num','xb')
        back_per_set = CheckCount.objects\
            .filter(check_date__gte=mon_firstday, check_date__lte=check_date, op_unit_name__contains=unit_name)\
            .values('sale_num').annotate(newadd_down_num=Sum('newadd_down_num'), other_down_num=Sum('other_down_num'),
                                         supp_down_num=Sum('supp_down_num')).values('db', 'xb', 'sale_name',
                                                                                    'sale_num', 'newadd_down_num',
                                                                                    'other_down_num', 'supp_down_num')\
            .order_by('-newadd_down_num', '-other_down_num', '-supp_down_num', 'xb')

    return render(request, 'reject_co.html', {
        'back_count': back_per_set,
        "unit": unit_name
    })
