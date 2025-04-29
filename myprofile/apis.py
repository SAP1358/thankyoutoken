from django.shortcuts import render, HttpResponse
from myprofile.models import User as User2
from myprofile.models import UserTokens, UserPraise, UserNotices, UserComment

from django.db.models import Q
from django.db.models import QuerySet
from django.db.models.query import RawQuerySet

from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
import json
from django.core import serializers
from django.db.models import Count
import pandas as pd
from django.http import JsonResponse

import requests
import time
import random

import hashlib
import hmac
import base64
import datetime
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Max


@csrf_exempt
def myprofile_modify(request):
    print('## [API] myprofile_modify called ###')
    
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':        
        for key, value in request.POST.items():
            print('### [INPUT] ', key, value)
            
        #-------------
        # 업무로직
        #-------------

        #-------------
        # 출력내용 SET
        #-------------
        ResultData = {
            'status' : '200',
            'value' : '0'
        }

        # json으로 변환
        json_data = json.dumps(ResultData)
        print("### [OUTPUT] JSON = ",json_data)   

        return HttpResponse(json_data, content_type="application/json") 

    #######################################
    # POST 수신아닌 경우
    #######################################    
    ResultData = {
        'status' : '404',
        'error' : '요청 데이터가 없습니다.'
    }
    
    # json으로 변환
    json_data = json.dumps(ResultData)
    print("### [OUTPUT] JSON = ",json_data)   
    
    return HttpResponse(json_data, content_type="application/json") 


@csrf_exempt
def myprofile_praise_recive_list(request):
    print('### [API] myprofile_praise_recive_list called ###')
    
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':        
        for key, value in request.POST.items():
            print('### [INPUT] ', key, value)
            
        #-------------
        # 업무로직
        #-------------

        #-------------
        # 출력내용 SET
        #-------------
        ResultData = {
            'status' : '200',
            'value' : '0'
        }

        # json으로 변환
        json_data = json.dumps(ResultData)
        print("### [OUTPUT] JSON = ",json_data)   

        return HttpResponse(json_data, content_type="application/json") 

    #######################################
    # POST 수신아닌 경우
    #######################################    
    ResultData = {
        'status' : '404',
        'error' : '요청 데이터가 없습니다.'
    }
    
    # json으로 변환
    json_data = json.dumps(ResultData)
    print("### [OUTPUT] JSON = ",json_data)   
    
    return HttpResponse(json_data, content_type="application/json") 

@csrf_exempt
def myprofile_praise_send_list(request):
    print('### [API] myprofile_praise_send_list called ###')
    
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':        
        for key, value in request.POST.items():
            print('### [INPUT] ', key, value)
            
        #-------------
        # 업무로직
        #-------------

        #-------------
        # 출력내용 SET
        #-------------
        ResultData = {
            'status' : '200',
            'value' : '0'
        }

        # json으로 변환
        json_data = json.dumps(ResultData)
        print("### [OUTPUT] JSON = ",json_data)   

        return HttpResponse(json_data, content_type="application/json") 

    #######################################
    # POST 수신아닌 경우
    #######################################    
    ResultData = {
        'status' : '404',
        'error' : '요청 데이터가 없습니다.'
    }
    
    # json으로 변환
    json_data = json.dumps(ResultData)
    print("### [OUTPUT] JSON = ",json_data)   
    
    return HttpResponse(json_data, content_type="application/json") 


@csrf_exempt
def myprofile_praise_detail(request):
    print('### [API] myprofile_praise_detail called ###')
    
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':        
        for key, value in request.POST.items():
            print('### [INPUT] ', key, value)
            
        #-------------
        # 업무로직
        #-------------

        #-------------
        # 출력내용 SET
        #-------------
        ResultData = {
            'status' : '200',
            'value' : '0'
        }

        # json으로 변환
        json_data = json.dumps(ResultData)
        print("### [OUTPUT] JSON = ",json_data)   

        return HttpResponse(json_data, content_type="application/json") 

    #######################################
    # POST 수신아닌 경우
    #######################################    
    ResultData = {
        'status' : '404',
        'error' : '요청 데이터가 없습니다.'
    }
    
    # json으로 변환
    json_data = json.dumps(ResultData)
    print("### [OUTPUT] JSON = ",json_data)   
    
    return HttpResponse(json_data, content_type="application/json") 


@csrf_exempt
def myprofile_praise_modify(request):
    print('### [API] myprofile_praise_modify called ###')
    
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':        
        for key, value in request.POST.items():
            print('### [INPUT] ', key, value)
            
        #-------------
        # 업무로직
        #-------------

        #-------------
        # 출력내용 SET
        #-------------
        ResultData = {
            'status' : '200',
            'value' : '0'
        }

        # json으로 변환
        json_data = json.dumps(ResultData)
        print("### [OUTPUT] JSON = ",json_data)   

        return HttpResponse(json_data, content_type="application/json") 

    #######################################
    # POST 수신아닌 경우
    #######################################    
    ResultData = {
        'status' : '404',
        'error' : '요청 데이터가 없습니다.'
    }
    
    # json으로 변환
    json_data = json.dumps(ResultData)
    print("### [OUTPUT] JSON = ",json_data)   
    
    return HttpResponse(json_data, content_type="application/json") 

