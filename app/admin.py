from django.contrib import admin
from app import models
# 用于 admin 后台管理，分别对应model的表名
admin.site.register(models.NoticeDay)    # 每日公告栏
admin.site.register(models.All)          # 累计积分汇总表
admin.site.register(models.Daily)        # 每日积分明细
admin.site.register(models.MonthGoal)    # 每月人均积分明细
admin.site.register(models.CreateCheck)  # 新增质检明细
admin.site.register(models.ChangeCheck)  # 变更质检表
admin.site.register(models.SuppleCheck)  # 增补质检表
admin.site.register(models.CheckCount)   # 质检量统计
admin.site.register(models.Log)          # 网站访问记录
admin.site.register(models.OrderStatus)  # 申领状态
