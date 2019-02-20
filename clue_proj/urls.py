"""clue_proj URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# from django.contrib import admin
# from django.urls import path
# from ..app import views
#
# urlpatterns = [
#     path('admin/', admin.site.urls),
#     # ex: /polls/
#     path('/results/', views.results, name='index'),
#
# ]

from django.conf.urls import url
from django.contrib import admin
from app import views
# from app import view_order
# urlpatterns = [
#    url(r'^admin/', admin.site.urls),
# ]


urlpatterns = [
    url(r'^$', views.home_page),
    url(r'^admin/', admin.site.urls),             # 后台站点
    url(r'^detail/', views.detail_score),          # 各区明细
    url(r'^person_detail/', views.person_detail),  # 个人明细
    url(r'^person_rank/', views.person_rank),      # 个人积分排名
    url(r'^reject_detail/', views.reject_detail),  # 驳回明细
    url(r'^reject_count/', views.reject_count),    # 驳回统计

    # url(r'^order/',view_order.order),            # 申领
    # url(r'^order_result/',view_order.orderResult), # 申领结果
    # url(r'^order_query/',view_order.orderQuery), # 申领查询
    ]
