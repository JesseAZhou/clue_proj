#coding:utf8
from django import template
register = template.Library()

@register.filter(name= 'add_value')
def add_value(value,key):
    value_sum = 0
    for a_value in value:
        value_sum += a_value[key]
    return value_sum

@register.filter(name='two_more')
def two_more(value,key_one):
    return value,key_one

@register.filter(name= 'add_average')
def add_average(value,key_two):
    value_list,key_one = value
    value_one_sum = 0
    value_two_sum = 0
    for obj in value_list:
        value_one_sum += obj[key_one]
        value_two_sum += obj[key_two]
    value_average = round(float(value_one_sum)*100/float(value_two_sum),1) if  value_two_sum > 0 else 0
    return  value_average