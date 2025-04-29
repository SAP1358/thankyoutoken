####################################################################
# 업무제목 : 땡큐토큰 home/view 업무
# 프로그램 : view.py
# ------------------------------------------------------------------
# 2023-12-11 김대영 최초개발
# 2023-12-14 김대영 관리자 순위그룹 개발, 소속장이상 거래가능
# 2023-12-21 김대영 관리자 계열사별 데이터현황 개발
# 2023-12-22 김대영 관리자 순위조회시 운영자는 제외처리
# 2023-12-27 김대영 관리자 칭찬카드 (새해) 구분추가
# 2024-01-02 김대영 관리자 데이터현황 기준변경 (월별 -> 누적)
# 2024-01-03 김대영 관리자 데이터현황 우리은행 피어그룹 실적자료 추가
# 2024-01-29 윤준영 위비 카드 추가
# 2024-02-05 윤준영 설날 카드 추가
# 2024-02-07 윤준영 답장 및 상단 검색 기능 추가 및 변경
# 2024-03-01 윤준영 My땡큐
# 2024-04-11 윤준영 칭찬시 분기처리
# 2024-04-21 윤준영 토큰 받을 때 무조건 20개 세팅 문제 개선
# 2024-05-20 윤준영 땡큐주간 신설
# 2024-06-05 윤준영 땡큐토큰 UC메신저 적용에 따른 대응개발
# 2024-06-20 윤준영 칭찬시에 어플 푸쉬알림 문제시 null 오류 해결
# 2024-07-01 윤준영 중복칭찬 가능 포인트가산 제외 남은토큰 차감
# 2024-09-14 윤준영 updateUserPraise.chg_date = datetime.now()
# 2024-12-03 VTI   add reply function into thankyouTalk()
# 2024-12-10 VTI   compress image when upload
# 2024-12-17 VTI   decrease limit items in search screen
# 2024-12-18 VTI   integrate feature upload image to CDN
# 2024-12-24 VTI   fix point accumulation incorrect
# 2024-12-25 VTI   refactor and add new functions of home, search, tk_list, rankList
####################################################################
from django.shortcuts import render, HttpResponse, redirect
from myprofile.models import User as User2

from myprofile.models import UserTokens, UserPraise, UserNotices, UserComment, UserImages
from myprofile.models import ManageTokens, UserLike, ManageDept, ManagePosi, ManageTokensGroup, AccessLog, ManageThankyouWeeks, BefInsUcmsg

from django.db.models import ExpressionWrapper, fields
from django.db.models.functions import TruncDate

from django.db.models import Q
from django.db.models import QuerySet
from django.db.models.query import RawQuerySet
from django.db.models import Max

from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
import json
from django.core import serializers
from datetime import datetime
import requests
import random

from django.db.models.expressions import Case
from django.db.models.query import When

import hashlib
import hmac
import base64
import pandas as pd
from django.db.models import F,Value
from django.db.models.functions import Concat

from django.conf import settings
from django.core.files.storage import FileSystemStorage

from django.core.files.base import ContentFile
from PIL import Image
from io import BytesIO
import os
import re
from collections import Counter

#from textblob import TextBlob
#import nltk
#nltk.download('punkt')

#from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import time


from datetime import date
from django.utils.html import strip_tags

from django.db.models import Count
from django.db.models import Sum

from summarizer import Summarizer    # pip install bert-extractive-summarizer


from konlpy.tag import Okt
# from gensim.summarization.summarizer import summarize

import hashlib
from cryptography.fernet import Fernet
#pip install pycryptodome
#import Crypto
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import binascii
import base64

import json
from datetime import datetime, timedelta  # timedelta를 import 추가

from django.db.models.functions import Coalesce, Cast
from django.db.models import OuterRef, Subquery
from django.db.models import CharField
from django.db.models import F, Window
from django.db.models.functions import RowNumber
from django.db.models import Max, Value, DateTimeField, Case, Exists #2024.02 my땡큐 마이땡큐
from django.db import connection, transaction


#엑셀 업로드 2024.05.20
import openpyxl
import csv
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.utils import timezone
from .forms import UploadFileForm
from .decorators import measure_execution_time
from .utils import process_excel_data, compress_image, upload_to_cdn
import emoji
from .services.rankList import get_active_tokens, process_praise_tags
from .services.tk_list import get_unprocessed_messages, process_single_message
# from .forms import ExcelUploadForm




# Okt 객체를 전역으로 선언하여 재사용
okt = Okt()
text = "thankyou"
nouns = okt.nouns(text)

# Summarizer 객체 생성
summarizer = Summarizer()

def result(request):
    return render(request, 'result.html')

@login_required(login_url='/accounts/signin/')
@measure_execution_time
def home_new(request):
    # ==========================
    # 2024-12-25 refactor and add new functions of home, search, tk_list, rankList
    # ==========================

    # First, create a subquery to check if any records exist in the first condition
    exist_todaythanks = UserPraise.objects.filter(
        is_active='Y',
        todaythanks_showyn='Y'
    ).exists()

    # # Get list of liked compliment_ids
    # liked_compliments = UserLike.objects.filter(
    #     user_id=request.user.id,
    #     is_active='Y'
    # ).values_list('compliment_id', flat=True)
    
    # # Get 1 record with todaythanks_showyn
    # today_thanks = UserPraise.objects.filter(
    #     is_active='Y',
    #     todaythanks_showyn='Y'  # Ensure todaythanks_showyn has value
    # ).select_related('praise', 'images', 'user')\
    #     .annotate(
    #         praise_employee_name=F('praise__employee_name'),
    #         praise_employee_id=F('praise__employee_id'),
    #         praise_department_name=F('praise__department_name'),
    #         praise_position_name=F('praise__position_name'),
    #         praise_company_name=F('praise__company_name'),
    #         praise_image_yn=F('praise__image_yn'),
    #         praise_image=F('praise__image'),
    #         user_employee_name=F('user__employee_name'),
    #         user_employee_id=F('user__employee_id'),
    #         user_department_name=F('user__department_name'),
    #         user_position_name=F('user__position_name'),
    #         user_company_name=F('user__company_name'),
    #         user_image_yn=F('user__image_yn'),
    #         user_image=F('user__image'),
    #         image_path=F('images__image_path'),
    #         like_yn=Case(
    #             When(compliment_id__in=liked_compliments, then=1),
    #             default=0,
    #         )       
    #     ).order_by('-reg_date')[:1]

    # # Get 5 records ordered by reg_date
    # regular_posts = UserPraise.objects.filter(
    #     Q(todaythanks_showyn='N') | Q(todaythanks_showyn__isnull=True),  # Exclude records with todaythanks_showyn
    #     is_active='Y',
    # ).select_related('praise', 'images', 'user')\
    #     .annotate(
    #         praise_employee_name=F('praise__employee_name'),
    #         praise_employee_id=F('praise__employee_id'),
    #         praise_department_name=F('praise__department_name'),
    #         praise_position_name=F('praise__position_name'),
    #         praise_company_name=F('praise__company_name'),
    #         praise_image_yn=F('praise__image_yn'),
    #         praise_image=F('praise__image'),
    #         user_employee_name=F('user__employee_name'),
    #         user_employee_id=F('user__employee_id'),
    #         user_department_name=F('user__department_name'),
    #         user_position_name=F('user__position_name'),
    #         user_company_name=F('user__company_name'),
    #         user_image_yn=F('user__image_yn'),
    #         user_image=F('user__image'),
    #         image_path=F('images__image_path'),
    #         like_yn=Case(
    #             When(compliment_id__in=liked_compliments, then=1),
    #             default=0,
    #         )       
    #     ).order_by('-reg_date')[:5]

    # # Combine the results
    # selectUserPraise = list(today_thanks) + list(regular_posts)

    # # Process content
    # for post in selectUserPraise:
    #     post.content = post.content.replace('\r\n', '<br>').replace('\r', '<br>').replace('\n', '<br>')
    
    # Get all active and public images
    selectUserImages = UserImages.objects\
        .filter(is_open='Y', is_active='Y')\
        .order_by('-reg_date')
                
    return render(
        request, 
        'home/main.html',  
        {
            # 'posts': selectUserPraise, 
            'exist_todaythanks': 'Y' if exist_todaythanks else 'N', 
            'images': selectUserImages, 
            'addPage': 'Y'
        }
    )

@login_required(login_url='/accounts/signin/')
@measure_execution_time
def home(request):
    # print("### [VIEW] home ####################################################")
    
    #-------------
    # 업무로직
    #-------------
    
    result = UserLike.objects.filter(
        user_id = request.user.id,
        is_active = 'Y',
    ).values_list('compliment_id', flat=True)
    
    #print("### result.values_list('compliment_id', flat=True) ", result.values_list('compliment_id', flat=True))
    
    selectUserPraise = UserPraise.objects.filter(is_active='Y')\
        .select_related('praise', 'images').annotate(
            praise_employee_name=F('praise__employee_name'),
            praise_employee_id=F('praise__employee_id'),
            praise_department_name=F('praise__department_name'),
            praise_position_name=F('praise__position_name'),
            praise_company_name=F('praise__company_name'),
            praise_image_yn=F('praise__image_yn'),
            praise_image=F('praise__image'),
            user_employee_name=F('user__employee_name'),
            user_employee_id=F('user__employee_id'),
            user_department_name=F('user__department_name'),
            user_position_name=F('user__position_name'),
            user_company_name=F('user__company_name'),
            user_image_yn=F('user__image_yn'),
            user_image=F('user__image'),
            image_path=F('images__image_path'),
            like_yn=Case(
                When(compliment_id__in=result, then=1),
                default=0,
            )       
        ).order_by('-todaythanks_showyn','-reg_date')
        
    #compliment_id_COUNT=Count('usercomment__compliment_id', filter=Q(usercomment__compliment_id__is_active='Y'))
    
    #print('### compliment_id_COUNT', compliment_id_COUNT)
    
    # for row in selectUserPraise.values():
    #    print(row)

    # 출력부 SET
    paginator = Paginator(selectUserPraise, 6)
    page = request.GET.get('page')
    posts = paginator.get_page(page)

    # 특수문자 개선
    for post in posts:
        #print('### before ', post.content )
        post.content = post.content.replace('\r\n', '<br>')
        post.content = post.content.replace('\r\n', '<br>')
        post.content = post.content.replace('\r', '<br>')
        post.content = post.content.replace('\n', '<br>')
        #print('### after ', post.content )
        # try:
        #     post.short_content = post.short_content[0:24]
        #     # print("chk : ", post.short_content)
        # except:
        #     pass
    
    #-------------
    # 이미지 출력SET
    #-------------
    selectUserImages = UserImages.objects.filter(is_open='Y', is_active='Y').order_by('-reg_date')
    
    paginator = Paginator(selectUserImages, 6)
    page = request.GET.get('page')
    images = paginator.get_page(page)
                
    return render(request, 'home/main.html',  {'posts':posts, 'images':images, 'addPage':'Y'})           
    
@login_required(login_url='/accounts/signin/')
@measure_execution_time
def search_new(request):
    # ==========================
    # 2024-12-25 refactor and add new functions of home, search, tk_list, rankList
    # ==========================

    # Only process POST requests, otherwise redirect to home
    if request.method != 'POST':
        return redirect('/')

    # Get search parameters
    user_id = request.POST.get('input_search')
    if not user_id:
        return redirect('/')

    # # Get active users matching search criteria
    # active_user_ids = User2.objects.filter(
    #     id=user_id,
    #     is_active=True
    # ).values_list('id', flat=True)

    # # Get current user's liked posts
    # liked_compliments = UserLike.objects.filter(
    #     user_id=request.user.id,
    #     is_active='Y'
    # ).values_list('compliment_id', flat=True)

    # # Main query for user praises with optimizations
    # selectUserPraise = UserPraise.objects.filter(
    #     Q(praise_id__in=active_user_ids) | 
    #     Q(user_id__in=active_user_ids),
    #     is_active='Y'
    # ).select_related(
    #     'praise', 
    #     'images', 
    #     'user'
    # ).annotate(
    #     # Annotate fields from related models
    #     praise_employee_name=F('praise__employee_name'),
    #     praise_employee_id=F('praise__employee_id'),
    #     praise_department_name=F('praise__department_name'),
    #     praise_position_name=F('praise__position_name'),
    #     praise_company_name=F('praise__company_name'),
    #     praise_image_yn=F('praise__image_yn'),
    #     praise_image=F('praise__image'),
    #     user_employee_name=F('user__employee_name'),
    #     user_employee_id=F('user__employee_id'),
    #     user_department_name=F('user__department_name'),
    #     user_position_name=F('user__position_name'),
    #     user_company_name=F('user__company_name'),
    #     user_image_yn=F('user__image_yn'),
    #     user_image=F('user__image'),
    #     image_path=F('images__image_path'),
    #     # Check if post is liked by current user
    #     like_yn=Case(
    #         When(compliment_id__in=liked_compliments, then=1),
    #         default=0,
    #     )       
    # ).order_by('-reg_date')[:6]  # Get only first 6 records

    # # Process content formatting
    # for post in selectUserPraise:
    #     post.content = post.content.replace('\r\n', '<br>').replace('\r', '<br>').replace('\n', '<br>')

    # Get active images
    selectUserImages = UserImages.objects.filter(
        is_open='Y', 
        is_active='Y'
    ).order_by('-reg_date')

    return render(
        request, 
        'home/main.html', 
        {
            # 'posts': selectUserPraise,
            'images': selectUserImages,
            'addPage': 'Y',
            'search_employee_name': user_id
        }
    )

@login_required(login_url='/accounts/signin/')
@measure_execution_time
def search(request):
    print("### [VIEW] search ####################################################")
    
    ##########################
    # POST 수신시
    ##########################
    if request.method == 'POST':
        
        for key, value in request.POST.items():
            print(key, value)
                
        #-------------
        # 업무로직
        #-------------
        
        user_id = request.POST['input_search'] # 2024.01 employee_name> user_id
        
        #Q(employee_name__icontains=employee_name), > id=employee_name, 2024.01 검색 방식 변경
        selectUser = User2.objects.filter(
                    id=user_id,
                    is_active=True
                ).order_by('-reg_date')\
                .values_list('id', flat=True)
        
        # print("### selectUser.values_list('compliment_id', flat=True) ", selectUser.values_list('id', flat=True))
        
        #for row in selectUser.values():
        #    print(row)
        
    
        result = UserLike.objects.filter(
            user_id = request.user.id,
            is_active = 'Y',
        ).values_list('compliment_id', flat=True)

        #print("### result.values_list('compliment_id', flat=True) ", result.values_list('compliment_id', flat=True))

        #input_search
        #selectUserPraise = UserPraise.objects.filter(is_active='Y')\
        selectUserPraise = UserPraise.objects.filter(
                Q(praise_id__in=selectUser.values_list('id', flat=True))|
                Q(user_id__in=selectUser.values_list('id', flat=True)),
                is_active='Y',
            )\
            .select_related('praise', 'images').annotate(
                praise_employee_name=F('praise__employee_name'),
                praise_employee_id=F('praise__employee_id'),
                praise_department_name=F('praise__department_name'),
                praise_position_name=F('praise__position_name'),
                praise_company_name=F('praise__company_name'),
                praise_image_yn=F('praise__image_yn'),
                praise_image=F('praise__image'),
                user_employee_name=F('user__employee_name'),
                user_employee_id=F('user__employee_id'),
                user_department_name=F('user__department_name'),
                user_position_name=F('user__position_name'),
                user_company_name=F('user__company_name'),
                user_image_yn=F('user__image_yn'),
                user_image=F('user__image'),
                image_path=F('images__image_path'),
                like_yn=Case(
                    When(compliment_id__in=result, then=1),
                    default=0,
                )       
            ).order_by('-reg_date')


        #compliment_id_COUNT=Count('usercomment__compliment_id', filter=Q(usercomment__compliment_id__is_active='Y'))

        #print('### compliment_id_COUNT', compliment_id_COUNT)

        #for row in selectUserPraise.values():
        #    print(row)

        # 출력부 SET
        # 특정 ID 목록
        specific_ids = [16106, 17242, 16610, 15952, 10055, 3157, 10328, 6932, 4772, 5094,
                        10919, 3733, 12828, 16535, 5899, 8427, 13905, 3763, 3743, 5042,
                        6111, 15523, 12417, 12474, 12438, 12464, 16431, 16496, 16409, 17037,
                        17046, 17035, 16688, 17211, 14531, 15683, 14024, 15357, 5931, 17316,
                        15495, 15712, 15645, 16652, 15464, 16539, 14511, 15558, 15776, 15726]

        # selectUser의 ID가 specific_ids에 포함되어 있는지 확인
        # if any(user_id in specific_ids for user_id in selectUser):
        #     paginator = Paginator(selectUserPraise, 1000)
        # else:
        #     paginator = Paginator(selectUserPraise, 200)

        #============
        # 2024-12-17: decrease limit items in search screen
        #============
        # if user_id == 15893: #회장님
        #     paginator = Paginator(selectUserPraise, 200)
        # else:
        #     paginator = Paginator(selectUserPraise, 1000)
        # paginator = Paginator(selectUserPraise, 200) #회장님 검색시 로딩 느려서 1000>6 변경 2024.03.17, 'addPage':'N' > 'Y'로 변경해서 return
        paginator = Paginator(selectUserPraise, 6)
        page = request.GET.get('page')
        posts = paginator.get_page(page)

        # 특수문자 개선
        for post in posts:
            #print('### before ', post.content )
            post.content = post.content.replace('\r\n', '<br>')
            post.content = post.content.replace('\r\n', '<br>')
            post.content = post.content.replace('\r', '<br>')
            post.content = post.content.replace('\n', '<br>')
            #print('### after ', post.content )

        #-------------
        # 이미지 출력SET
        #-------------
        selectUserImages = UserImages.objects.filter(is_open='Y', is_active='Y').order_by('-reg_date')

        paginator = Paginator(selectUserImages, 6)
        page = request.GET.get('page')
        images = paginator.get_page(page)

        return render(request, 'home/main.html', {'posts':posts, 'images':images, 'addPage':'Y', 'search_employee_name':user_id})
    
    ##########################
    # 조회하면(메인)
    ##########################
    
    return redirect('/')

@login_required(login_url='/accounts/signin/')
def dev(request):

    # print("### 1111111111")
    employee_name = "우리"

    #소속장 이상 제외 직위셋
    #reward_skip_users = ManagePosi.objects.filter(reward_skip_yn='Y').values_list('posi_id', flat=True)
    # print("### 1111111111")
    selectUser = User2.objects.filter(
        Q(employee_name__icontains=employee_name),
        is_active=True,
        ty=True,
        department_name__isnull=False,
        department_id__isnull=False,
    ).exclude(id=request.user.id).order_by('employee_name')
    # print("### 1111222111111")
    for user in selectUser:
        print(user.employee_name, user.position_id, user.company_id)

    
    # Add annotation for reward_skip_yn based on company_id and posi_id
    # ManagePosi 모델의 reward_skip_yn을 selectUser 쿼리셋에 추가
    selectUser = selectUser.annotate(
        reward_skip_yn=Coalesce(
            Subquery(
                ManagePosi.objects.filter(
                    company_id=OuterRef('company_id'),
                    posi_id=OuterRef('position_id')
                ).values('reward_skip_yn')[:1]
            ), Value('N')
        )
    )

    # print("### 1111333111111")
    # Now you can access the reward_skip_yn field in your queryset
    for user in selectUser:
        print(user.employee_name, user.position_name, user.reward_skip_yn)

    #-------------
    # 사용자 검증
    #-------------
    if request.user.is_superuser :
        print("### 관리자 접속")
    else :
        print("### 사용자 접속")
        error = "[101] 관리자 외 접속 불가합니다."
        return render(request, 'page_error.html', {'error': error})  
    
    return render(request, 'dev.html')

@login_required(login_url='/accounts/signin/')
def manageMain(request):
        
    ##########################
    # GET 수신시
    ##########################        
    if 'manage_token_id' in request.GET:
        manage_token_id = request.GET['manage_token_id']
        print('[VIEW][INPUT] manage_token_id ', manage_token_id)
    else : 
        manage_token_id = 0

    #--------------
    # 토큰기준
    #--------------
    today = datetime.now().strftime('%Y%m%d')
    baiscManageTokens = ManageTokens.objects.filter(
        Q(start_date__lte=today) & Q(end_date__gte=today)
    ).first()

    #-------------
    # 토큰발행여부 검증
    #-------------
    if not baiscManageTokens:
        print("### 토큰 정상필요")
        
        baiscManageTokens = ManageTokens.objects.filter(
            is_active='Y'
        ).order_by('-end_date').first()
        
        #error = "[안내] 관리자에게 문의 요청 드립니다. 발행된 토큰이 없습니다"
        #return render(request, 'page_error.html', {'error': error})
    
    # print('### baiscManageTokens.id', baiscManageTokens.id)
    
    if int(baiscManageTokens.id) == int(manage_token_id):
        manage_token_id = 0
        print('### chg manage_token_id', manage_token_id)
    
    if manage_token_id == 0:
        selectManageTokens = ManageTokens.objects.filter(
            Q(start_date__lte=today) & Q(end_date__gte=today),
            is_active = 'Y'
        ).first()
        
        if not selectManageTokens:
            print("### 토큰 정상필요 selectManageTokens")
            
            selectManageTokens = ManageTokens.objects.filter(
                is_active='Y'
            ).order_by('-end_date').first()
    else:
        selectManageTokens = ManageTokens.objects.filter(
            id=manage_token_id, is_active = 'Y'
        ).first()
        

    subquery_prev = ManageTokens.objects.filter(
        id__lt=selectManageTokens.id,
        is_active = 'Y'
    ).order_by('-id').first()

    subquery_next = ManageTokens.objects.filter(
        id__gt=selectManageTokens.id,
        is_active = 'Y'
    ).order_by('id').first()

    if subquery_prev:
        token_prev = subquery_prev.id
    else:
        token_prev = 0

    if subquery_next:
        token_next = subquery_next.id
    else:
        token_next = 0
    
    
    #-------------------------------------------------
    # 데이터 현황
    #-------------------------------------------------
    
    # 일자별 접속 건수 조회
    selectAccessLog = AccessLog.objects.filter(
        user_access_time__isnull=False
    ).annotate(
        access_date=TruncDate('user_access_time')
    ).values(
        'access_date'
    ).annotate(
        count=Count('access_id')
    ).order_by('-access_date')

    # 출력부 SET
    paginator = Paginator(selectAccessLog, 5)     
    page = request.GET.get('page')
    AccessLog_posts = paginator.get_page(page)
    
    #-------------------------------------------------
    # 사용자 검증
    #-------------------------------------------------
    if request.user.is_superuser :
        print("### 관리자 접속")
    else :
        print("### 사용자 접속")
        error = "[101] 관리자 외 접속 불가합니다."
        return render(request, 'page_error.html', {'error': error})  
    
    #-------------------------------------------------
    # 데이터 현황
    #-------------------------------------------------
    # 누적로그인 수
    login_count = User2.objects.filter(
        last_login__gt='2023-11-11 13:24:33.000',
        ty=1
    ).count()

    # user_tokens_count 누적 참여자수
    user_tokens_count = UserTokens.objects.filter(
        #token_id=selectManageTokens.id, # 대상건만 추출
        is_active = 'Y'
    ).values('user_id').distinct().count()
    
    # priase_tokens_count 누적 칭찬건수
    praise_tokens_count = UserTokens.objects.filter(
        #token_id=selectManageTokens.id, # 대상건만 추출
        is_active = 'Y'
    ).aggregate(Sum('received_tokens'))['received_tokens__sum']
    
    # send_10_count 월별 사용건수
    send_10_count = UserTokens.objects.filter(
        token_id=selectManageTokens.id,
        my_current_tokens=0,  # 모두 소진대상
        my_tot_tokens__lt=30  # 30 미만인 경우에 대한 조건 추가 (소속장 제외)
    ).select_related('user').annotate(
        reward_skip_yn=Coalesce(
            Subquery(
                ManagePosi.objects.filter(
                    is_active="Y",
                    company_id=OuterRef('user__company_id'),
                    posi_id=OuterRef('user__position_id'),
                    reward_skip_yn__isnull=False
                ).values('reward_skip_yn')[:1]
            ), Value('N')  # 기본값으로 'N' 사용
        )
    ).filter(
        reward_skip_yn='N'  # 서브쿼리의 reward_skip_yn 값이 'N'인 경우만 필터링
    ).values(
        'user__company_name',
        'user__department_name',
        'user__employee_name',
        'user__position_name',
        'user__employee_id',
        'reward_skip_yn'
    ).count()

    #print("누적 로그인 수:", login_count)
    #print("누적 참여자 수:", user_tokens_count)
    #print("누적 칭찬건 수:", priase_tokens_count)
    #print("땡큐토큰 10개 사용한 직원 수:", send_10_count)

    #-------------------------------------------------
    # 계열사별 칭찬건수
    #-------------------------------------------------
        
    selectCompanyUserTokens = UserTokens.objects.filter(
        #token_id=selectManageTokens.id, # 대상건만 추출
        is_active='Y'
    ).values(
        'user__company_id',
        'user__company_name'
    ).annotate(
        recev_point=Sum('received_tokens'),
        send_point=Sum('my_send_tokens'),
        company_count=Count('user', distinct=True)  # 중복되지 않는 유니크한 user_id를 기준으로 Count
    ).order_by('user__company_id')
		
		# 출력부 SET
    paginatorToken = Paginator(selectCompanyUserTokens, 100)
    pageToken      = request.GET.get('pageToken')
    postsToken     = paginatorToken.get_page(pageToken)
    
    #-------------------------------------------------
    # 2024-01-03 우리은행 피어별 칭찬건수
    #-------------------------------------------------
        
    selectPeerSubquery = UserTokens.objects.filter(
        is_active='Y',
        user__company_id="20"  # 추가된 조건
    ).select_related('user').annotate(
        peer_no=Coalesce(
            Subquery(
                ManageDept.objects.filter(
                    is_active="Y",
                    company_id=OuterRef('user__company_id'),
                    dept_id=OuterRef('user__department_id')
                ).values('peer_no')[:1]
            ), Value(' ')  # 기본값으로 'N' 사용
        )
    )
		
    # peer_no를 기준으로 그룹화
    selectPeerUserTokens = selectPeerSubquery.values('peer_no').annotate(
        recev_point=Sum('received_tokens'),
        send_point=Sum('my_send_tokens'),
        peer_count=Count('user__id', distinct=True)
    ).annotate(
        peer_no_as_int=Coalesce(Cast('peer_no', fields.IntegerField()), Value(0))
    ).order_by('peer_no_as_int')

    current_time = datetime.now()
    
		
		# 출력부 SET
    paginatorPeerToken = Paginator(selectPeerUserTokens, 100)
    pagePeerToken      = request.GET.get('pagePeerToken')
    postsPeerToken     = paginatorPeerToken.get_page(pagePeerToken)
    
    return render(request, 'manage/manageMain.html', {'AccessLog_posts':AccessLog_posts, 'login_count':login_count,'user_tokens_count':user_tokens_count, 'praise_tokens_count':praise_tokens_count,'send_10_count':send_10_count, 'manageToken':selectManageTokens, 'token_prev':token_prev,'token_next':token_next,'postsToken':postsToken,'postsPeerToken':postsPeerToken, 'current_time': current_time })

def apitest(request):
    print("### [VIEW] apitest ####################################################")
    
    #-------------
    # 사용자 검증
    #-------------
    if request.user.is_superuser :
        print("### 관리자 접속")
    else :
        print("### 사용자 접속")
        error = "[101] 관리자 외 접속 불가합니다."
        return render(request, 'page_error.html', {'error': error})  
    
    return render(request, 'apitest.html')

@login_required(login_url='/accounts/signin/')
def htmltest(request):
    print("### [VIEW] htmltest ####################################################")
    
    #-------------
    # 사용자 검증
    #-------------
    if request.user.is_superuser :
        print("### 관리자 접속")
    else :
        print("### 사용자 접속")
        error = "[101] 관리자 외 접속 불가합니다."
        return render(request, 'page_error.html', {'error': error})  
    
    #-------------
    # 업무로직
    #-------------
    selectUserPraise = UserPraise.objects.filter(is_active='Y')\
        .select_related('praise', 'images').annotate(
            praise_employee_name=F('praise__employee_name'),
            praise_image_yn=F('praise__image_yn'),
            praise_image=F('praise__image'),
            user_employee_name=F('user__employee_name'),
            user_image_yn=F('user__image_yn'),
            user_image=F('user__image'),
            image_path=F('images__image_path')
        ).order_by('-reg_date')

    
    #for row in selectUserPraise.values():
    #    print(row)
        
    #-------------
    # 출력부 SET
    #-------------
    paginator = Paginator(selectUserPraise, 10)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    
    return render(request, 'htmltest.html', {'posts':posts})

@login_required(login_url='/accounts/signin/')
def praiseList(request):
    print("### [VIEW] praiseList ####################################################")
    
    #-------------
    # 업무로직
    #-------------
    selectUserPraise = UserPraise.objects.filter(is_active='Y')\
        .select_related('praise', 'images').annotate(
            praise_employee_name=F('praise__employee_name'),
            praise_employee_id=F('praise__employee_id'),
            praise_department_name=F('praise__department_name'),
            praise_image_yn=F('praise__image_yn'),
            praise_image=F('praise__image'),
            user_employee_name=F('user__employee_name'),
            user_employee_id=F('user__employee_id'),
            user_department_name=F('user__department_name'),
            user_image_yn=F('user__image_yn'),
            user_image=F('user__image'),
            image_path=F('images__image_path')
        ).order_by('-reg_date')
    
    #for row in selectUserPraise.values():
    #    print(row)
            
    #-------------
    # 출력부 기본정보 SET
    #-------------
    paginator = Paginator(selectUserPraise, 10)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    
    #-------------
    # 출력부 이미지 SET
    #-------------
    selectUserImages = UserImages.objects.filter(is_open='Y', is_active='Y').order_by('-reg_date')
    
    paginator = Paginator(selectUserImages, 10)
    page = request.GET.get('page')
    images = paginator.get_page(page)
        
    return render(request, 'praiseList.html', {'posts':posts, 'images':images})
    
@login_required(login_url='/accounts/signin/')
def praiseDetail(request, compliment_id):
    print("### [VIEW] praiseDetail ####################################################")
    
    result = UserLike.objects.filter(
        user_id = request.user.id,
        is_active = 'Y',
    ).values_list('compliment_id', flat=True)
        
    #-------------
    # 업무로직
    #-------------
    selectUserPraise = UserPraise.objects.filter(is_active='Y', compliment_id=compliment_id)\
        .select_related('praise', 'images').annotate(
            praise_employee_name=F('praise__employee_name'),
            praise_employee_id=F('praise__employee_id'),
            praise_department_name=F('praise__department_name'),
            praise_position_name=F('praise__position_name'),
            praise_company_name=F('praise__company_name'),
            praise_image_yn=F('praise__image_yn'),
            praise_image=F('praise__image'),
            user_employee_name=F('user__employee_name'),
            user_employee_id=F('user__employee_id'),
            user_department_name=F('user__department_name'),
            user_position_name=F('user__position_name'),
            user_company_name=F('user__company_name'),
            user_image_yn=F('user__image_yn'),
            user_image=F('user__image'),
            image_path=F('images__image_path'),
            like_yn=Case(
                When(compliment_id__in=result, then=1),
                default=0,
            )  
        ).order_by('-reg_date').first()
    
    return render(request, 'praiseDetail.html', {'info':selectUserPraise})


@login_required(login_url='/accounts/signin/')
def praiseDelete(request, compliment_id):
    print("### [VIEW] praiseDelete ####################################################")
    
    selectUserPraise = UserPraise.objects.filter(compliment_id=compliment_id).first()
    #print('### selectUserPraise.user_id', selectUserPraise.user_id)
    
    #-------------
    # 사용자 검증
    #-------------
    if selectUserPraise:
        if selectUserPraise.user_id == request.user.id or request.user.is_superuser :
            print("### 본인 삭제")
        else :
            print("### 타인 삭제")
            error = "[101] 칭찬글 본인외 삭제 불가합니다."
            return render(request, 'page_error.html', {'error': error})  
    else :
        print("### 삭제")
        error = "[101] 존재하지 않습니다."
        return render(request, 'page_error.html', {'error': error})  
    #-------------
    # view 건수증가
    #-------------
    updateUserPraise = UserPraise.objects.get(compliment_id=compliment_id)
    updateUserPraise.is_active = 'N'
    updateUserPraise.chg_date = datetime.now()      
    updateUserPraise.save() 
        
        
    #------------------------------------
    # 토큰 insert & update
    #------------------------------------
    #################
    # 등록자 토큰감소
    #################

    # 토큰정보
    today = datetime.now().strftime('%Y%m%d')
    selectManageTokens = ManageTokens.objects.filter(
        Q(start_date__lte=today) & Q(end_date__gte=today)
    ).first()

    toeknYear    = selectManageTokens.year
    toeknQuarter = selectManageTokens.quarter
    toeknCount   = selectManageTokens.tokens

    selectUserTokens = UserTokens.objects.filter(
        user_id=updateUserPraise.user_id,
        year=toeknYear,
        quarter=toeknQuarter,
        is_active='Y'
    ).first()

    reg_date = selectUserPraise.reg_date.strftime('%Y%m%d')
    weekym = selectUserPraise.reg_date.strftime('%Y%m')
    selectThankyouWeeksYn = ManageThankyouWeeks.objects.filter(is_active='Y', weeks_ym = weekym, start_date__lte=reg_date, end_date__gte = reg_date).first()

    selectSameTotalCount = UserPraise.objects.filter(
                                is_active='Y', 
                                token_id = selectManageTokens.id,
                                user_id = updateUserPraise.user_id,
                                praise_id = updateUserPraise.praise_id,
                            ).count()
    
    selectSendUcCount = UserPraise.objects.filter(
                                is_active='Y', 
                                is_senduc='Y', 
                                token_id = selectManageTokens.id,
                                user_id = updateUserPraise.user_id,
                                praise_id = updateUserPraise.praise_id,
                            ).count()

    if selectUserTokens:
        # 데이터가 존재하는 경우
        
        #UC메신저 칭찬이 있을 때
        if selectSendUcCount > 0 :
                #땡큐주간에 등록된 칭찬은 토큰 2개 부여되어서 칭찬삭제시 토큰 +1 할 필요 없다.
                if selectSameTotalCount == 0:
                    selectUserTokens.my_send_tokens    -= 1

                selectUserTokens.chg_date = datetime.now()      
                selectUserTokens.save()  # 업데이트 수행
                # print('### my  1selectUserTokens.user_id   ', selectUserTokens.user_id)

        else : 
                #UC메신저 칭찬이 없을 때
                #땡큐주간에 등록된 칭찬은 토큰 2개 부여되어서 칭찬삭제시 토큰 +1 할 필요 없다.
                if selectThankyouWeeksYn is None :
                    selectUserTokens.my_current_tokens += 1

                if selectSameTotalCount == 0:
                    selectUserTokens.my_send_tokens    -= 1

                selectUserTokens.chg_date = datetime.now()      
                selectUserTokens.save()  # 업데이트 수행
                # print('### my  1selectUserTokens.user_id   ', selectUserTokens.user_id)

    else:
        print('### error user_id')

    ##################
    # 칭찬대상 토큰감소
    ##################
    selectUserTokens = UserTokens.objects.filter(
        user_id=updateUserPraise.praise_id,
        year=toeknYear,
        quarter=toeknQuarter,
        is_active='Y'
    ).first()

    if selectUserTokens:
        # 데이터가 존재하는 경우
        if selectSameTotalCount == 0:
            selectUserTokens.received_tokens -= 1
            
        selectUserTokens.chg_date = datetime.now()      
        selectUserTokens.save()  # 업데이트 수행
        # print('### you selectUserTokens.user_id   ', selectUserTokens.user_id)

    else:
        print('### error priase_od')
        
    return redirect('/')

def save_image(file, path, filename):
    print("### [MODULE] save_image ####################################################")
    
    ##########################
    # 2024-12-10 Reduce the image quality to about 30% & would not exceed 100KB
    # 2024-12-18 integrate feature upload image to CDN
    ##########################

    img = compress_image(file)
    file_path = upload_to_cdn(img, path, filename)
    img.close()

    return file_path

def openAi(requestData, sendUser, recvUser):
    print("### [MODULE] openAi called ",sendUser, recvUser)
    
    praiseText = requestData
    #print('### [MODULE][LOG] praiseText ### ', praiseText)
    
    #"summary" = 50자이내 문장으로 요약해서 종결어미를 붙여 작성,
    
    headers={"Authorization":"Bearer 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","Content-Type":"application/json"}
    link="https://api.openai.com/v1/chat/completions"

    messages=[        
        {"role": "system", "content": "assistant는 회사에서 칭찬을 전달하는 담당자 입이다."},
        {"role": "user", "content": f"""
		* 입력값은 '칭찬글' 이며 분석해서 반드시 요약글로 답변주세요, 분석결과는 'JSON' 형식으로 주세요. 특수문자(따음표, 콤마, 초성)는 답변에 사용하지 않습니다.
        
        * 입력값 = [
        '칭찬글' = [ {praiseText} ],
        'exclude_words' =  [ {sendUser},  {recvUser} ]
        ]
        
        * JSON 형식 = [
        "summary" = 20자 이하로 요약해서 반드시 종결어미를 붙여 작성하고 특수문자와 초성은 절대 사용하지 않습니다 그리고 입력값 길이보다 짧게 답변 주세요,
        "tag" = 반드시 주요tag 3개이며 2글자이상 10자이내로 작성해 주세요
		]
	 """}
    ]
    
    data={"model": "gpt-3.5-turbo", "messages": messages, "temperature": 0.2, "max_tokens": 300}
    
    print("### [MODULE][LOG] openAi messages ", messages)
    response=requests.post(link,data=json.dumps(data),headers=headers)
    
    print("### [MODULE][LOG] openAi response : ", response)
    message = response.json()['choices'][0]['message']['content']   
    print("### [MODULE][LOG] message : ", message)
    message = message.replace("'", "\"")

    # 응답이 {}로 시작하고 끝나는지 확인
    if not message.startswith("{")  :
        # {}로 감싸기
        message = "{" + message + "}"
        print("### [MODULE][LOG] message22 : ", message)
        
    # json 형태의 문자열 추출
    json_text = message[message.find("{"):message.rfind("}")+1]
    json_text = json_text.replace("'", "\"")
    
    # json으로 변환
    json_data = json.loads(json_text)
        
    #print("### [MODULE][LOG] openAi json_data ",json_data)   
    
    return json_data 

def ChwPushCall(pushId, TITLE, MESSAGE, URL):
    print('### [API] ChwPushCall #############')

		###################
    # 암호화
    ###################
    def EncryptByAES256(text, password):
        ue = "utf-8"

        # key 및 iv 설정 (동일한 크기 유지)
        pwdBytes = password.encode(ue)
        keyBytes = pwdBytes.ljust(32, b'\0')  # 키를 32 바이트로 맞춥니다.
        IVBytes = pwdBytes.ljust(16, b'\0')  # 초기화 벡터를 16 바이트로 맞춥니다.

        # 메시지 인코딩
        message = text.encode(ue)

        # 암호화 수행
        rijndael = AES.new(keyBytes, AES.MODE_CBC, IVBytes)
        padded_text = pad(message, AES.block_size)
        cipher_bytes = rijndael.encrypt(padded_text)

        # Base64로 인코딩
        base64_string = base64.b64encode(cipher_bytes).decode(ue)

        return base64_string

    # 패딩 함수 추가 (PKCS7 패딩 구현)
    def pad(data, block_size):
        padding = block_size - (len(data) % block_size)
        return data + bytes([padding] * padding)

    # 현재 시간 +5분
    #timestamp         = int((datetime.utcnow()).timestamp())
		# 서버의 시스템 시간을 얻습니다.
    server_now = datetime.now()

		# timestamp를 얻습니다.
    timestamp_server = int(server_now.timestamp())
    
    # 직원ID 추출
    selectUserPush    = User2.objects.get(id=pushId)
    push_employee_id  = selectUserPush.employee_id

    # empNo:timestamp를 콜론으로 결합
    Pushkey = f'{push_employee_id}:{timestamp_server}'
    password = 'ThankyouToken!@#'

    #print('### [API][LOG] server_now', server_now)
    #print('### [API][LOG] timestamp_server', timestamp_server)
    #print('### [API][LOG] Pushkey', Pushkey)

    encrypted_Key = EncryptByAES256(Pushkey, password)
    #print('### [API][LOG] encrypted_Key:', encrypted_Key)

		###################
		# PUSH CALL
		###################
    
    if settings.SERVER_NAME == 'TEST' :
        print('### SERVER_NAME PUSH API', settings.SERVER_NAME)
        url = "http://wbn.castware.co.kr:8080/r-api/v1/thankyoutoken/addPush" # 테스트 URL
    else : 
        url = "https://wbnadmin.wooriwbn.com/r-api/v1/thankyoutoken/addPush" # 운영 URL

    input_data = {
        "key": encrypted_Key,
        "title": TITLE,
        "message": MESSAGE,
        "url":URL
    }

    headers = {
        "Content-Type": "application/json"
    }
    
    #print("### [API] Push Called ###")
    try:
        response = requests.post(url, data=json.dumps(input_data), headers=headers)

        print("### [API] response.status_code ", response.status_code)
        #print('### [LOG] response.text', response.text)

        if response.status_code == 200:
            data = response.json()
            print("### [API] Push Call success")
            #print(data)
            status_code = response.status_code
            PushYN = 'Y'

        else:
            #print("### [API] Push Call status ERROR:", response.text)
            PushYN = 'N'
            status_code = response.status_code
    except:
            print("### [API] Push Call system ERROR:", response.text)
            PushYN = 'N'
            status_code = '999'


    return PushYN, status_code
    

@login_required(login_url='/accounts/signin/')
@measure_execution_time
def praiseRegedit(request):
    # print("### [VIEW] praiseRegedit ####################################################")
    
    ##########################
    # Get 수신시 R102401172924 답장 2024.01
    ##########################
    if 'userId' in request.GET:
        user_id = request.GET.get('userId', None)
        # print('user_id request.GET>> : ', user_id)
        
        # user_record = User2.objects.filter(id = user_id).first()
        user_record = User2.objects.filter(id=user_id).values('id', 'employee_name', 'company_name','department_name').first()

        if user_record:
            user_id = user_record['id']
            employee_name = user_record['employee_name']

            user_info = {'user_id': user_record['id'],
                       'employee_name': user_record['employee_name'],
                       'company_name': user_record['company_name'],
                       'department_name': user_record['department_name'],}

            # 이제 user_id와 employee_name을 사용할 수 있음
        else:
            # 해당 user_id에 대한 레코드가 없을 경우 처리
            pass

        # print('user_record ======= > ', user_record.id)
        # print('user_record ======= > ', user_record)

        # 토큰가능건수 체크
        today = datetime.now().strftime('%Y%m%d')
        selectManageTokens = ManageTokens.objects.filter(
            Q(start_date__lte=today) & Q(end_date__gte=today)
        ).first()

        toeknYear    = selectManageTokens.year
        toeknQuarter = selectManageTokens.quarter
        toeknCount   = selectManageTokens.tokens

        selectUserTokens = UserTokens.objects.filter(
            user_id=request.user.id,
            year=toeknYear,
            quarter=toeknQuarter,
            is_active='Y'
        ).first()
        
        if selectUserTokens is not None and selectUserTokens.my_current_tokens == 0:
            #-------------
            # 오류내용 SET
            #-------------
            error = "[300] 사용가능한 토큰건수가 없습니다."
            info = {'error': error,
                       'praise_id': request.POST.get('input_employee_id', ''),
                       'content': request.POST.get('input_Contents', ''),
                       'input_active': request.POST.get('input_active', '')}

            #-------------
            # 출력부 SET
            #-------------
            selectUserImages_All = UserImages.objects.filter(is_open='Y', is_active='Y').order_by('-reg_date')
            paginator0 = Paginator(selectUserImages_All, 100)
            page0 = request.GET.get('page0')
            posts_All = paginator0.get_page(page0)
            
            selectUserImages_1 = UserImages.objects.filter(card_code = '1', is_open='Y', is_active='Y').order_by('-reg_date')
            paginator1 = Paginator(selectUserImages_1, 100)
            page1 = request.GET.get('page1')
            posts_1 = paginator1.get_page(page1)
            
            selectUserImages_2 = UserImages.objects.filter(card_code = '2', is_open='Y', is_active='Y').order_by('-reg_date')
            paginator2 = Paginator(selectUserImages_2, 100)
            page2 = request.GET.get('page2')
            posts_2 = paginator2.get_page(page2)
            
            selectUserImages_3 = UserImages.objects.filter(card_code = '3', is_open='Y', is_active='Y').order_by('-reg_date')
            paginator3 = Paginator(selectUserImages_3, 100)
            page3 = request.GET.get('page3')
            posts_3 = paginator3.get_page(page3)
            
            selectUserImages_4 = UserImages.objects.filter(card_code = '4', is_open='Y', is_active='Y').order_by('-reg_date')
            paginator4 = Paginator(selectUserImages_4, 100)
            page4 = request.GET.get('page4')
            posts_4 = paginator4.get_page(page4)
            
            selectUserImages_5 = UserImages.objects.filter(card_code = '5', is_open='Y', is_active='Y').order_by('-reg_date')
            paginator5 = Paginator(selectUserImages_5, 100)
            page5 = request.GET.get('page5')
            posts_5 = paginator5.get_page(page5)

            selectUserImages_6 = UserImages.objects.filter(card_code = '6', is_open='Y', is_active='Y').order_by('-reg_date')
            paginator6 = Paginator(selectUserImages_6, 100)
            page6 = request.GET.get('page6')
            posts_6 = paginator6.get_page(page6) #2024.01.29 카드그룹관리 위비항목 추가

            selectUserImages_7 = UserImages.objects.filter(card_code = '7', is_open='Y', is_active='Y').order_by('-reg_date')
            paginator7 = Paginator(selectUserImages_7, 100)
            page7 = request.GET.get('page7')
            posts_7 = paginator7.get_page(page7) #2024.02.05 카드그룹관리 설날항목 추가

            return render(request, 'praiseRegedit.html', {'info':info,'posts_All':posts_All,'posts_1':posts_1,'posts_2':posts_2,'posts_3':posts_3, 'posts_4':posts_4,'posts_5':posts_5,'posts_6':posts_6,'posts_7':posts_7, 'token':selectUserTokens, 'manage':selectManageTokens, 'user_info':user_info })
        
        else:
            alarmChk = "get으로 접속 for 답장"
            info = {'alarmChk': alarmChk }
            
            #-------------
            # 출력부 SET
            #-------------
            selectUserImages_All = UserImages.objects.filter(is_open='Y', is_active='Y').order_by('-reg_date')
            paginator0 = Paginator(selectUserImages_All, 100)
            page0 = request.GET.get('page0')
            posts_All = paginator0.get_page(page0)
            
            selectUserImages_1 = UserImages.objects.filter(card_code = '1', is_open='Y', is_active='Y').order_by('-reg_date')
            paginator1 = Paginator(selectUserImages_1, 100)
            page1 = request.GET.get('page1')
            posts_1 = paginator1.get_page(page1)
            
            selectUserImages_2 = UserImages.objects.filter(card_code = '2', is_open='Y', is_active='Y').order_by('-reg_date')
            paginator2 = Paginator(selectUserImages_2, 100)
            page2 = request.GET.get('page2')
            posts_2 = paginator2.get_page(page2)
            
            selectUserImages_3 = UserImages.objects.filter(card_code = '3', is_open='Y', is_active='Y').order_by('-reg_date')
            paginator3 = Paginator(selectUserImages_3, 100)
            page3 = request.GET.get('page3')
            posts_3 = paginator3.get_page(page3)
            
            selectUserImages_4 = UserImages.objects.filter(card_code = '4', is_open='Y', is_active='Y').order_by('-reg_date')
            paginator4 = Paginator(selectUserImages_4, 100)
            page4 = request.GET.get('page4')
            posts_4 = paginator4.get_page(page4)
            
            selectUserImages_5 = UserImages.objects.filter(card_code = '5', is_open='Y', is_active='Y').order_by('-reg_date')
            paginator5 = Paginator(selectUserImages_5, 100)
            page5 = request.GET.get('page5')
            posts_5 = paginator5.get_page(page5)

            selectUserImages_6 = UserImages.objects.filter(card_code = '6', is_open='Y', is_active='Y').order_by('-reg_date')
            paginator6 = Paginator(selectUserImages_6, 100)
            page6 = request.GET.get('page6')
            posts_6 = paginator6.get_page(page6) #2024.01.29 카드그룹관리 위비항목 추가

            selectUserImages_7 = UserImages.objects.filter(card_code = '7', is_open='Y', is_active='Y').order_by('-reg_date')
            paginator7 = Paginator(selectUserImages_7, 100)
            page7 = request.GET.get('page7')
            posts_7 = paginator7.get_page(page7) #2024.02.05 카드그룹관리 설날항목 추가

            return render(request, 'praiseRegedit.html', {'info':info,'posts_All':posts_All,'posts_1':posts_1,'posts_2':posts_2,'posts_3':posts_3, 'posts_4':posts_4,'posts_5':posts_5,'posts_6':posts_6,'posts_7':posts_7, 'token':selectUserTokens, 'manage':selectManageTokens, 'user_info':user_info })
    # R102401172924 답장 2024.01

    ##########################
    # POST 수신시
    ##########################
    if request.method == 'POST':
                
        #-------------
        # 입력부 SET
        #-------------
        for key, value in request.POST.items():
            print('### [VIEW][INPUT]', key, value)
                
                
        # 토큰가능건수 체크
        today = datetime.now().strftime('%Y%m%d')
        selectManageTokens = ManageTokens.objects.filter(
            Q(start_date__lte=today) & Q(end_date__gte=today)
        ).first()

        toeknYear    = selectManageTokens.year
        toeknQuarter = selectManageTokens.quarter
        toeknCount   = selectManageTokens.tokens

        selectUserTokens = UserTokens.objects.filter(
            user_id=request.user.id,
            year=toeknYear,
            quarter=toeknQuarter,
            is_active='Y'
        ).first()
        
        if selectUserTokens is not None and selectUserTokens.my_current_tokens == 0:
            #-------------
            # 오류내용 SET
            #-------------
            error = "[300] 사용가능한 토큰건수가 없습니다."
            info = {'error': error,
                       'praise_id': request.POST.get('input_employee_id', ''),
                       'content': request.POST.get('input_Contents', ''),
                       'input_active': request.POST.get('input_active', '')}

            #-------------
            # 출력부 SET
            #-------------
            selectUserImages_All = UserImages.objects.filter(is_open='Y', is_active='Y').order_by('-reg_date')
            paginator0 = Paginator(selectUserImages_All, 100)
            page0 = request.GET.get('page0')
            posts_All = paginator0.get_page(page0)
            
            selectUserImages_1 = UserImages.objects.filter(card_code = '1', is_open='Y', is_active='Y').order_by('-reg_date')
            paginator1 = Paginator(selectUserImages_1, 100)
            page1 = request.GET.get('page1')
            posts_1 = paginator1.get_page(page1)
            
            selectUserImages_2 = UserImages.objects.filter(card_code = '2', is_open='Y', is_active='Y').order_by('-reg_date')
            paginator2 = Paginator(selectUserImages_2, 100)
            page2 = request.GET.get('page2')
            posts_2 = paginator2.get_page(page2)
            
            selectUserImages_3 = UserImages.objects.filter(card_code = '3', is_open='Y', is_active='Y').order_by('-reg_date')
            paginator3 = Paginator(selectUserImages_3, 100)
            page3 = request.GET.get('page3')
            posts_3 = paginator3.get_page(page3)
            
            selectUserImages_4 = UserImages.objects.filter(card_code = '4', is_open='Y', is_active='Y').order_by('-reg_date')
            paginator4 = Paginator(selectUserImages_4, 100)
            page4 = request.GET.get('page4')
            posts_4 = paginator4.get_page(page4)
            
            selectUserImages_5 = UserImages.objects.filter(card_code = '5', is_open='Y', is_active='Y').order_by('-reg_date')
            paginator5 = Paginator(selectUserImages_5, 100)
            page5 = request.GET.get('page5')
            posts_5 = paginator5.get_page(page5)

            selectUserImages_6 = UserImages.objects.filter(card_code = '6', is_open='Y', is_active='Y').order_by('-reg_date')
            paginator6 = Paginator(selectUserImages_6, 100)
            page6 = request.GET.get('page6')
            posts_6 = paginator6.get_page(page6) #2024.01.29 카드그룹관리 위비항목 추가

            selectUserImages_7 = UserImages.objects.filter(card_code = '7', is_open='Y', is_active='Y').order_by('-reg_date')
            paginator7 = Paginator(selectUserImages_7, 100)
            page7 = request.GET.get('page7')
            posts_7 = paginator7.get_page(page7) #2024.02.05 카드그룹관리 설날항목 추가
                    
            return render(request, 'praiseRegedit.html', {'info':info,'posts_All':posts_All,'posts_1':posts_1,'posts_2':posts_2,'posts_3':posts_3, 'posts_4':posts_4,'posts_5':posts_5,'posts_6':posts_6,'posts_7':posts_7, 'token':selectUserTokens, 'manage':selectManageTokens})
              
                
        if int(request.POST['input_employee_id']) == int(request.user.id):
            #-------------
            # 오류내용 SET
            #-------------
            error = "[301] 본인에게 칭찬등록 불가합니다."
            info = {'error': error,
                       'praise_id': request.POST.get('input_employee_id', ''),
                       'content': request.POST.get('input_Contents', ''),
                       'input_active': request.POST.get('input_active', '')}

            #-------------
            # 출력부 SET
            #-------------
            selectUserImages_All = UserImages.objects.filter(is_open='Y', is_active='Y').order_by('-reg_date')
            paginator0 = Paginator(selectUserImages_All, 100)
            page0 = request.GET.get('page0')
            posts_All = paginator0.get_page(page0)
            
            selectUserImages_1 = UserImages.objects.filter(card_code = '1', is_open='Y', is_active='Y').order_by('-reg_date')
            paginator1 = Paginator(selectUserImages_1, 100)
            page1 = request.GET.get('page1')
            posts_1 = paginator1.get_page(page1)
            
            selectUserImages_2 = UserImages.objects.filter(card_code = '2', is_open='Y', is_active='Y').order_by('-reg_date')
            paginator2 = Paginator(selectUserImages_2, 100)
            page2 = request.GET.get('page2')
            posts_2 = paginator2.get_page(page2)
            
            selectUserImages_3 = UserImages.objects.filter(card_code = '3', is_open='Y', is_active='Y').order_by('-reg_date')
            paginator3 = Paginator(selectUserImages_3, 100)
            page3 = request.GET.get('page3')
            posts_3 = paginator3.get_page(page3)
            
            selectUserImages_4 = UserImages.objects.filter(card_code = '4', is_open='Y', is_active='Y').order_by('-reg_date')
            paginator4 = Paginator(selectUserImages_4, 100)
            page4 = request.GET.get('page4')
            posts_4 = paginator4.get_page(page4)
            
            selectUserImages_5 = UserImages.objects.filter(card_code = '5', is_open='Y', is_active='Y').order_by('-reg_date')
            paginator5 = Paginator(selectUserImages_5, 100)
            page5 = request.GET.get('page5')
            posts_5 = paginator5.get_page(page5)

            selectUserImages_6 = UserImages.objects.filter(card_code = '6', is_open='Y', is_active='Y').order_by('-reg_date')
            paginator6 = Paginator(selectUserImages_6, 100)
            page6 = request.GET.get('page6')
            posts_6 = paginator6.get_page(page6) #2024.01.29 카드그룹관리 위비항목 추가

            selectUserImages_7 = UserImages.objects.filter(card_code = '7', is_open='Y', is_active='Y').order_by('-reg_date')
            paginator7 = Paginator(selectUserImages_7, 100)
            page7 = request.GET.get('page7')
            posts_7 = paginator7.get_page(page7) #2024.02.05 카드그룹관리 설날항목 추가
                                
            return render(request, 'praiseRegedit.html', {'info':info,'posts_All':posts_All,'posts_1':posts_1,'posts_2':posts_2,'posts_3':posts_3, 'posts_4':posts_4,'posts_5':posts_5,'posts_6':posts_6,'posts_7':posts_7, 'token':selectUserTokens, 'manage':selectManageTokens})
              
            
        # 소속장이상 여부체크    
        praise_user_id = request.POST['input_employee_id']
        selectPraiseUser = User2.objects.filter(
            id = praise_user_id
        ).first()
        #print('### praise_user_id', praise_user_id)
        
        selectPraiseManagePosi = ManagePosi.objects.filter(
            company_id=selectPraiseUser.company_id,
            posi_id=selectPraiseUser.position_id,
            is_active = 'Y'
        ).first()
        #print('### selectPraiseManagePosi', selectPraiseManagePosi.id)
        
        if selectPraiseManagePosi:
            print('### [API][LOG] selectPraiseManagePosi.reward_skip_yn',selectPraiseManagePosi.reward_skip_yn)
            
            #2023-12-14 소속장 이상허용
            if selectPraiseManagePosi.reward_skip_yn == '9999' :

                #-------------
                # 오류내용 SET
                #-------------
                error = "[302] 소속상이상은 칭찬등록 불가합니다."
                info = {'error': error,
                           'praise_id': request.POST.get('input_employee_id', ''),
                           'content': request.POST.get('input_Contents', ''),
                           'input_active': request.POST.get('input_active', '')}
                            
                #-------------
                # 출력부 SET
                #-------------
                selectUserImages_All = UserImages.objects.filter(is_open='Y', is_active='Y').order_by('-reg_date')
                paginator0 = Paginator(selectUserImages_All, 100)
                page0 = request.GET.get('page0')
                posts_All = paginator0.get_page(page0)
                
                selectUserImages_1 = UserImages.objects.filter(card_code = '1', is_open='Y', is_active='Y').order_by('-reg_date')
                paginator1 = Paginator(selectUserImages_1, 100)
                page1 = request.GET.get('page1')
                posts_1 = paginator1.get_page(page1)
                
                selectUserImages_2 = UserImages.objects.filter(card_code = '2', is_open='Y', is_active='Y').order_by('-reg_date')
                paginator2 = Paginator(selectUserImages_2, 100)
                page2 = request.GET.get('page2')
                posts_2 = paginator2.get_page(page2)
                
                selectUserImages_3 = UserImages.objects.filter(card_code = '3', is_open='Y', is_active='Y').order_by('-reg_date')
                paginator3 = Paginator(selectUserImages_3, 100)
                page3 = request.GET.get('page3')
                posts_3 = paginator3.get_page(page3)
                
                selectUserImages_4 = UserImages.objects.filter(card_code = '4', is_open='Y', is_active='Y').order_by('-reg_date')
                paginator4 = Paginator(selectUserImages_4, 100)
                page4 = request.GET.get('page4')
                posts_4 = paginator4.get_page(page4)
                
                selectUserImages_5 = UserImages.objects.filter(card_code = '5', is_open='Y', is_active='Y').order_by('-reg_date')
                paginator5 = Paginator(selectUserImages_5, 100)
                page5 = request.GET.get('page5')
                posts_5 = paginator5.get_page(page5)
                
                selectUserImages_6 = UserImages.objects.filter(card_code = '6', is_open='Y', is_active='Y').order_by('-reg_date')
                paginator6 = Paginator(selectUserImages_6, 100)
                page6 = request.GET.get('page6')
                posts_6 = paginator6.get_page(page6) #2024.01.29 카드그룹관리 위비항목 추가

                selectUserImages_7 = UserImages.objects.filter(card_code = '7', is_open='Y', is_active='Y').order_by('-reg_date')
                paginator7 = Paginator(selectUserImages_7, 100)
                page7 = request.GET.get('page7')
                posts_7 = paginator6.get_page(page7) #2024.02.05 카드그룹관리 설날항목 추가

                return render(request, 'praiseRegedit.html', {'info':info,'posts_All':posts_All,'posts_1':posts_1,'posts_2':posts_2,'posts_3':posts_3, 'posts_4':posts_4,'posts_5':posts_5,'posts_6':posts_6,'posts_7':posts_7, 'token':selectUserTokens, 'manage':selectManageTokens})
              
                
            
        try:        
            if 'input_active' in request.POST and request.POST['input_swiper_id'] in ['0']:
                print("### [VIEW][LOG] inputCardImg Start ==========")
                
                # ----------------------------------
                # 파일 업로드 ddd 
                # request.FILES.get('inputCardImg'):
                # ----------------------------------
                
                for key, file in request.FILES.items():
                    print('### [VIEW][INPUT]', key, file)
                
                insertUserImages = UserImages()
                
                formFile = request.FILES['inputCardImg']
                today = date.today().strftime("%Y%m%d")
                now = datetime.now()
                time_string = now.strftime("%H%M%S")
                path = 'user_' + str(request.user.id) + '/' + today
                filename = time_string + '_' + formFile.name
                # 이미지 저장
                filePath = save_image(formFile, path, filename)
                
                # 파일 저장 후, 저장된 경로를 출력
                print("### [VIEW][LOG] filename", filename)
                print("### [VIEW][LOG] file url", filePath)

                fileYn   = 'Y'
                insertUserImages.image_path            = filePath

                #################################################
                # DB UPDATE
                #################################################
                insertUserImages.image_name    = 'UserImage'
                insertUserImages.is_open       = 'N'
                insertUserImages.is_active     = 'N'
                insertUserImages.reg_date      = datetime.now()
                
                print("### [VIEW][LOG] insertUserImages save ========== ")
                insertUserImages.save()
                
                print("### [VIEW][LOG] insertUserImages.id : ", insertUserImages.id)
                
                
                
        except:
            #-------------
            # 오류내용 SET
            #-------------
            error = "[400] 데이터 저장시 오류가 발생 했습니다."
            info = {'error': error,
                       'praise_id': request.POST.get('input_employee_id', ''),
                       'content': request.POST.get('input_Contents', ''),
                       'input_active': request.POST.get('input_active', '')}

            #-------------
            # 출력부 SET
            #-------------
            selectUserImages = UserImages.objects.filter(is_open='Y', is_active='Y').order_by('-reg_date')

            paginator = Paginator(selectUserImages, 100)
            page = request.GET.get('page')
            posts = paginator.get_page(page)

            return render(request, 'praiseRegedit.html', {'posts':posts, 'info':info,})
                
        # 등록자 사용가능한 토큰 개수 검증
        print("### [VIEW][LOG] insertUserPraise Start ==========")
        
        #-------------
        # 업무로직
        #-------------        
        if request.POST['input_Contents']:
            try:
                # ===================
                # 2024-12-24 fix point accumulation incorrect
                # ===================
                with transaction.atomic():

                    #------------------------------------
                    # 칭찬 insert
                    #------------------------------------
                    insertUserPraise = UserPraise()
                    
                    insertUserPraise.praise_id        = request.POST['input_employee_id']
                    insertUserPraise.user_id          = request.user.id
                    insertUserPraise.compliment_type  = '1'
                    
                    
                    #chgageContents = re.sub('<\/?p[^>]*>', '', request.POST['input_Contents'])
                    insertUserPraise.content          = request.POST['input_Contents']
                    
                    if 'input_active' in request.POST and request.POST['input_swiper_id'] in ['0']:
                        insertUserPraise.images_id        = insertUserImages.id
                    else : 
                        insertUserPraise.images_id        = request.POST['input_swiper_id']
                    
                    
                    insertUserPraise.org_content      = request.POST['input_Contents_text']
                    
                    insertUserPraise.short_content    = '' # open ai 응답
                    insertUserPraise.tag              = '' # open ai 응답
                    insertUserPraise.emotion_ratio    = '' # open ai 응답
                    
                    insertUserPraise.view_count       = 0
                    insertUserPraise.comment_count    = 0
                    insertUserPraise.likes_count      = 0
                    
                    insertUserPraise.is_senduc        =  'N'
                    
                    #----------
                    # 토큰정보
                    #----------
                    today = datetime.now().strftime('%Y%m%d')
                    selectManageTokens = ManageTokens.objects.filter(
                        Q(start_date__lte=today) & Q(end_date__gte=today)
                    ).first()
                    insertUserPraise.token_id      = selectManageTokens.id
                    
                    if 'input_active' in request.POST and request.POST['input_active'] in ['on', 'Y']:
                        insertUserPraise.is_active = 'Y'
                    else:
                        insertUserPraise.is_active = 'Y'
                        
                    insertUserPraise.reg_date = datetime.now()   
                    
                    print("### [VIEW][LOG] insertUserPraise Save ==========")
                    insertUserPraise.save()
                    
                    print('### [VIEW][LOG] insertUserPraise.compliment_id   ', insertUserPraise.compliment_id)
                    
                    
                    #------------------------------------
                    # 토큰 insert & update
                    #------------------------------------
                    ##################################
                    # 등록자 토큰감소
                    ##################################

                    # 토큰정보
                    today = datetime.now().strftime('%Y%m%d')
                    selectManageTokens = ManageTokens.objects.filter(
                        Q(start_date__lte=today) & Q(end_date__gte=today)
                    ).first()
                    
                    toeknYear    = selectManageTokens.year
                    toeknQuarter = selectManageTokens.quarter
                    toeknCount   = selectManageTokens.tokens
                    hightoeknCount   = selectManageTokens.high_tokens

                    # 소속장여부 확인
                    selectuserReward = ManagePosi.objects.filter(
                        is_active  = 'Y',
                        company_id = request.user.company_id,
                        posi_id    = request.user.position_id
                    ).first()

                    if selectuserReward:
                        print('### user selectuserReward', selectuserReward.reward_skip_yn)
                        if selectuserReward.reward_skip_yn == "Y" :
                            user_reward_skip_yn = "Y"
                        else :
                            user_reward_skip_yn = "N"
                    else :
                        user_reward_skip_yn = "N"

                    # 보유토큰 조회
                    selectUserTokens = UserTokens.objects.select_for_update().filter(
                        user_id=request.user.id,
                        year=toeknYear,
                        quarter=toeknQuarter,
                        is_active='Y'
                    ).first()

                    #땡큐주간에 칭찬 발송시 토큰 추가
                    current_date = datetime.now().strftime('%Y%m%d')
                    weekym = datetime.now().strftime('%Y%m')
                    selectThankyouWeeksYn = ManageThankyouWeeks.objects.filter(is_active='Y', weeks_ym = weekym, start_date__lte=current_date, end_date__gte = current_date).first()

                    #동일 직원 칭찬 여부 확인
                    selectSameTotalCount = UserPraise.objects.select_for_update().filter(
                        is_active='Y', 
                        token_id = selectManageTokens.id,
                        user_id = request.user.id,
                        praise_id = request.POST['input_employee_id'],
                    ).count()
                    
                    # print('$$$$$$$$$$$$ selectTotalCount praise_count', selectSameTotalCount )
                    # print('$$$$$$$$$$$$ selectUserTokens null', selectUserTokens )

                    if selectUserTokens:
                        # 데이터가 존재하는 경우

                        # selectThankyouWeeksYn이 None이면 >  땡큐주간 아닌경우 (.first() > None으로 분기처리)
                        if selectThankyouWeeksYn is None:
                            selectUserTokens.my_current_tokens -= 1

                        if selectSameTotalCount == 1 :
                            selectUserTokens.my_send_tokens    += 1

                        selectUserTokens.chg_date = datetime.now()      
                        selectUserTokens.save()  # 업데이트 수행
                        print('### [VIEW][LOG] my  selectUserTokens.user_id   ', selectUserTokens.user_id)
                        
                    else:
                        # 데이터가 존재하지 않는 경우
                        insertUserTokens = UserTokens()
                        insertUserTokens.user_id           = request.user.id
                        insertUserTokens.token_id          = selectManageTokens.id
                        insertUserTokens.year              = toeknYear
                        insertUserTokens.quarter           = toeknQuarter
                        
                        #영업본부장님, 부행장들에게만 특정 수만큼 토큰 부여 2024.03.29
                        chkInsTokYn = User2.objects.filter(
                                            Q(position_name__contains='본부장') | Q(position_name__contains='부행장'),
                                            ~Q(id=5256),
                                            id=request.user.id,
                                            company_id=20    
                                        ).count()

                        if request.user.id == 15893: #회장님
                            insertUserTokens.my_tot_tokens = 100
                        else :
                            if chkInsTokYn > 0 :
                                insertUserTokens.my_tot_tokens = 100
                            else :
                                if user_reward_skip_yn == "Y" :
                                    insertUserTokens.my_tot_tokens = hightoeknCount
                                else : 
                                    insertUserTokens.my_tot_tokens = toeknCount
                        
                        # selectThankyouWeeksYn이 not None이면 땡큐주간이여서 tokens데이터 생성시 감소가 없기 때문에 초기값 세팅 그 외에는 -1을 해준다 (.first() > None으로 분기처리)
                        if selectThankyouWeeksYn is not None:
                            insertUserTokens.my_current_tokens = insertUserTokens.my_tot_tokens
                        else :
                            insertUserTokens.my_current_tokens = insertUserTokens.my_tot_tokens  - 1
                        
                        if selectSameTotalCount == 1 :
                            insertUserTokens.my_send_tokens    = 1
                        else :
                            insertUserTokens.my_send_tokens    = 0

                        insertUserTokens.received_tokens   = 0
                        insertUserTokens.is_active         = 'Y'
                        insertUserTokens.reg_date          = datetime.now()                
                        insertUserTokens.save()
                        print('### [VIEW][LOG] my  insertUserTokens.my_tot_tokens   ', insertUserTokens.my_tot_tokens)
                        print('### [VIEW][LOG] my  insertUserTokens.user_id   ', insertUserTokens.user_id)
                    
                    ###################################
                    # 칭찬대상 토큰증가
                    ###################################
                    selectUserTokens = UserTokens.objects.select_for_update().filter(
                        user_id=request.POST['input_employee_id'],
                        year=toeknYear,
                        quarter=toeknQuarter,
                        is_active='Y'
                    ).first()
                    
                    # print("$$$$$$ check selectSameTotalCount : ", selectSameTotalCount)
                    # print("$$$$$$ check selectUserTokens : ", selectUserTokens)

                    if selectUserTokens:
                        # 데이터가 존재하는 경우
                        if selectSameTotalCount == 1 :
                            selectUserTokens.received_tokens += 1
                        selectUserTokens.chg_date = datetime.now()      
                        selectUserTokens.save()  # 업데이트 수행
                        print('### [VIEW][LOG] you selectUserTokens.user_id   ', selectUserTokens.user_id)
                        
                    else:
                        # 데이터가 존재하지 않는 경우
                        # print("$$$$$$ check 존재하지 않는 경우 selectUserTokens : ", selectUserTokens)
                        insertUserTokens = UserTokens()
                        insertUserTokens.user_id           = request.POST['input_employee_id']
                        insertUserTokens.token_id          = selectManageTokens.id
                        insertUserTokens.year              = toeknYear
                        insertUserTokens.quarter           = toeknQuarter
                        
                        #영업본부장님, 부행장들에게만 특정 수만큼 토큰 부여 2024.04.09
                        chkInsTokYn = User2.objects.filter(
                                            Q(position_name__contains='본부장') | Q(position_name__contains='부행장'),
                                            ~Q(id=5256),
                                            id=insertUserTokens.user_id,
                                            company_id=20    
                                        ).count()
                        

                        # 칭찬 받는 직원 소속장여부 확인 
                        chkRecvUserInfo = User2.objects.get(id=insertUserTokens.user_id)

                        recvUserReward = ManagePosi.objects.filter(
                            is_active  = 'Y',
                            company_id = chkRecvUserInfo.company_id,
                            posi_id    = chkRecvUserInfo.position_id
                        ).first()
                        
                        # print("$$$$$$ check 존재하지 않는 경우 recvUserReward : ", recvUserReward)

                        if insertUserTokens.user_id == '15893': #회장님
                            insertUserTokens.my_tot_tokens = 100
                        else :
                            if chkInsTokYn > 0 :
                                insertUserTokens.my_tot_tokens = 100
                            else :
                                if recvUserReward is not None and recvUserReward.reward_skip_yn == "Y" :
                                    insertUserTokens.my_tot_tokens = hightoeknCount
                                else : 
                                    insertUserTokens.my_tot_tokens = toeknCount
                                
                        # insertUserTokens.my_tot_tokens     = toeknCount
                        # print("$$$$$$ check insertUserTokens.my_tot_tokens : ", insertUserTokens.my_tot_tokens)
                        
                        insertUserTokens.my_current_tokens = insertUserTokens.my_tot_tokens
                        insertUserTokens.my_send_tokens    = 0
                        
                        if selectSameTotalCount == 1 :
                            insertUserTokens.received_tokens   = 1
                        else :
                            insertUserTokens.received_tokens   = 0
                        
                        insertUserTokens.is_active         = 'Y'
                        insertUserTokens.reg_date          = datetime.now()                
                        insertUserTokens.save()
                        print('### [VIEW][LOG] you insertUserTokens.user_id   ', insertUserTokens.user_id)
                    
                    
                    #------------------------------------
                    # 알림 insert - 칭찬대상 알림 / PUSH
                    #------------------------------------
                    pushId  = request.POST['input_employee_id']
                    title   = "땡큐토큰"
                    message = request.user.employee_name+ ' '+ request.user.position_name+"님이 칭찬글을 등록 했습니다."
                    url = "/thankyoutoken/praiseDetail/" + str(insertUserPraise.compliment_id)
                    #title   = "thankyoutokentest"
                    #message = "thankyoutokentest"
                    PushYN, PushStatus  = ChwPushCall(pushId,title,message,url)
                    
                    insertUserNotices = UserNotices()
                    insertUserNotices.user_id          = request.POST['input_employee_id']
                    insertUserNotices.send_id          = request.user.id
                    insertUserNotices.notice_type      = '1'
                    insertUserNotices.compliment_id    = insertUserPraise.compliment_id
                    insertUserNotices.comment_id       = 0 
                    insertUserNotices.check_yn         = 'N' 
                    insertUserNotices.push_yn          = PushYN
                    insertUserNotices.push_status      = PushStatus
                    insertUserNotices.is_active        = 'Y'
                    insertUserNotices.reg_date         = datetime.now()                
                    insertUserNotices.save()
                    
                    print('### [VIEW][LOG] insertUserNotices.user_id   ', insertUserNotices.user_id)
                                    
                    #---------------
                    # open AI Call
                    #---------------
                    inputData = request.POST['input_Contents_text']
                    
                    
                    try:
                        # 등록직원
                        selectUser1 = User2.objects.get(id=insertUserNotices.send_id)
                        sendUser = selectUser1.employee_name
                        
                        # 칭찬직원
                        selectUser2 = User2.objects.get(id=insertUserNotices.user_id)
                        recvUser = selectUser2.employee_name
                        
                        #------------------------------------------------------------------
                        # openAI call (ChatGPT 2023-11-01)
                        #------------------------------------------------------------------
                        def call_openAi_GPT ():
                            outputJson = openAi(inputData, sendUser, recvUser)
                            short_content = outputJson['summary']
                            tag           = {'tag': outputJson['tag']}
                            emotion_ratio = ''

                            return short_content, tag
                        
                        #------------------------------------------------------------------
                        # 한국어 AI call (2023-01-01)
                        #------------------------------------------------------------------
                        def select_kWords ():
                            print("### [VIEW][LOG] select_kWords === ")

                            ############
                            # tag 추출
                            ############
                            exclude_words = [sendUser, recvUser]

                            result = ' '.join([word for word in inputData.split() if word not in exclude_words])
                            print("### [VIEW][LOG] text converse : ", result)
                            text = result

                            #단어추출
                            try:
                                #okt = Okt()
                                tag_words = [word for word in okt.nouns(text) if word not in exclude_words][:3]
                                tag       = {'tag': tag_words}
                            except:
                                tag = {'tag': ['감사','칭찬','도움']}
                                    
                            if not tag_words:
                                tag = {'tag': ['감사','칭찬','도움']}
                                print('### [VIEW][LOG] tag_words error ')
                            else :
                                print('### [VIEW][LOG] tag_words success ')
                                
                            print("### [VIEW][LOG] 주요 태그:", tag)
                            
                            ############
                            # 요약 추출
                            ############
                            if len(text) < 50:
                                short_content = text
                                
                            else:
                                
                                try: 
                                    #short_content = summarize(text)
                                    
                                    # Summarizer 객체 생성
                                    #summarizer = Summarizer()

                                    # 텍스트 요약
                                    short_content = summarizer(text)

                                    print('### [VIEW][LOG] summarize success ')
                                except:
                                    short_content = ''
                                    print('### [VIEW][LOG] summarize error ')
                                
                                print('### [VIEW][LOG] short_content', short_content)
                                
                                if short_content == '':
                                    short_content = text[:40] + "..."
                                    
                                if len(short_content) > 40:  
                                    short_content = short_content[:40] + "..."
                                
                            print("### [VIEW][LOG] 원본 길이:", len(short_content))
                            print("### [VIEW][LOG] 요약 내용:", short_content)

                            return short_content, tag

                        ##################
                        # AI호출 구분
                        ##################
                        print("### [VIEW][LOG] inputData 원본 길이:", len(inputData))

                        #if len(inputData) >= 50:  
                        #    short_content, tag = call_openAi_GPT()
                        #else : 
                        #    short_content, tag = select_kWords()

                        short_content, tag = select_kWords()
                        
                        print("### [VIEW][LOG] short_content:", short_content)
                        print("### [VIEW][LOG] tag          :", tag)
                        
                        #-------------
                        # DB Update
                        #-------------
                        updateUserPraise = UserPraise.objects.get(compliment_id=insertUserPraise.compliment_id) 

                        updateUserPraise.short_content  = short_content
                        updateUserPraise.tag            = tag
                        #updateUserPraise.emotion_ratio  = emotion_ratio

                        updateUserPraise.save()
                        
                        
                    except:                    
                        #-------------
                        # 오류내용 SET
                        #-------------
                        print("### [VIEW][LOG][ERROR openAi] 칭찬글 분석시 오류가 발생 했습니다.")
                        #print("에러 메시지:", str(e))

                        #-------------
                        # ERROR DB Update
                        #-------------
                        updateUserPraise = UserPraise.objects.get(compliment_id=insertUserPraise.compliment_id) 
                        updateUserPraise.short_content  = '시스템 확인 중 입니다.'
                        updateUserPraise.tag            = {'tag': ['확인중']}
                        updateUserPraise.emotion_ratio  = ''

                        updateUserPraise.save()

                    #----------------------------------------------------------------------------------------------------
                    # FINAL : 정상응답
                    #----------------------------------------------------------------------------------------------------
                    
                    # selectThankyouWeeksYn이 None이면 >  땡큐주간 아닌경우 (.first() > None으로 분기처리)
                    if selectThankyouWeeksYn is None:
                        return redirect('/')
                    else:
                        return redirect('/?showThkWeekModal=true')
            
            except:
                
                transaction.rollback()

                #-------------
                # 오류내용 SET
                #-------------
                error = "[403] 데이터 저장시 오류가 발생 했습니다."
                info = {'error': error,
                           'praise_id': request.POST.get('input_employee_id', ''),
                           'content': request.POST.get('input_Contents', ''),
                           'input_active': request.POST.get('input_active', '')}
                
                #-------------
                # 출력부 SET
                #-------------
                selectUserImages = UserImages.objects.filter(is_open='Y', is_active='Y').order_by('-reg_date')

                paginator = Paginator(selectUserImages, 100)
                page = request.GET.get('page')
                posts = paginator.get_page(page)
                
                return render(request, 'praiseRegedit.html', {'posts':posts, 'info':info,})
            
        else:
            #-------------
            # 오류내용 SET
            #-------------
            error = "[404] 입력된 데이터가 없습니다."
            info = {'error': error,
                       'praise_id': request.POST.get('input_employee_id', ''),
                       'content': request.POST.get('input_Contents', ''),
                       'input_active': request.POST.get('input_active', '')}
            
            #-------------
            # 출력부 SET
            #-------------
            selectUserImages = UserImages.objects.filter(is_open='Y', is_active='Y').order_by('-reg_date')

            paginator = Paginator(selectUserImages, 100)
            page = request.GET.get('page')
            posts = paginator.get_page(page)

            return render(request, 'praiseRegedit.html', {'posts':posts, 'info':info,})
                        
    #-------------
    # 업무로직
    #-------------
    
    # 토큰정보
    today = datetime.now().strftime('%Y%m%d')
    selectManageTokens = ManageTokens.objects.filter(
        Q(start_date__lte=today) & Q(end_date__gte=today)
    ).first()

    #toeknYear    = selectManageTokens.year
    #toeknQuarter = selectManageTokens.quarter
    
    #-------------
    # 토큰발행여부 검증
    #-------------
    if not selectManageTokens:
        print("### 토큰 정상필요")
        selectManageTokens = ManageTokens.objects.filter(
            Q(start_date__lte=today) & Q(end_date__gte=today)
        ).first()
    
        #error = "[안내] 관리자에게 문의 요청 드립니다. 발행된 토큰이 없습니다"
        #return render(request, 'page_error.html', {'error': error})
    
    if selectManageTokens :
        toeknCount   = selectManageTokens.tokens
        token_id     = selectManageTokens.id
    else :
        toeknCount   = 0
        token_id     = 0

    selectUserTokens = UserTokens.objects.filter(
        user_id  = request.user.id,
        token_id = token_id,
        #year=toeknYear,
        #quarter=toeknQuarter,
        is_active='Y'
    ).first()
    
    
    #my_current_tokens
    
    #-------------
    # 출력부 SET
    #-------------
    selectUserImages_All = UserImages.objects.filter(is_open='Y', is_active='Y').order_by('-reg_date')
    paginator0 = Paginator(selectUserImages_All, 100)
    page0 = request.GET.get('page0')
    posts_All = paginator0.get_page(page0)
    
    selectUserImages_1 = UserImages.objects.filter(card_code = '1', is_open='Y', is_active='Y').order_by('-reg_date')
    paginator1 = Paginator(selectUserImages_1, 100)
    page1 = request.GET.get('page1')
    posts_1 = paginator1.get_page(page1)
    
    selectUserImages_2 = UserImages.objects.filter(card_code = '2', is_open='Y', is_active='Y').order_by('-reg_date')
    paginator2 = Paginator(selectUserImages_2, 100)
    page2 = request.GET.get('page2')
    posts_2 = paginator2.get_page(page2)
    
    selectUserImages_3 = UserImages.objects.filter(card_code = '3', is_open='Y', is_active='Y').order_by('-reg_date')
    paginator3 = Paginator(selectUserImages_3, 100)
    page3 = request.GET.get('page3')
    posts_3 = paginator3.get_page(page3)
    
    selectUserImages_4 = UserImages.objects.filter(card_code = '4', is_open='Y', is_active='Y').order_by('-reg_date')
    paginator4 = Paginator(selectUserImages_4, 100)
    page4 = request.GET.get('page4')
    posts_4 = paginator4.get_page(page4)
    
    selectUserImages_5 = UserImages.objects.filter(card_code = '5', is_open='Y', is_active='Y').order_by('-reg_date')
    paginator5 = Paginator(selectUserImages_5, 100)
    page5 = request.GET.get('page5')
    posts_5 = paginator5.get_page(page5)
    
    selectUserImages_6 = UserImages.objects.filter(card_code = '6', is_open='Y', is_active='Y').order_by('-reg_date')
    paginator6 = Paginator(selectUserImages_6, 100)
    page6 = request.GET.get('page6')
    posts_6 = paginator6.get_page(page6) #2024.01.29 카드그룹관리 위비항목 추가

    selectUserImages_7 = UserImages.objects.filter(card_code = '7', is_open='Y', is_active='Y').order_by('-reg_date')
    paginator7 = Paginator(selectUserImages_7, 100)
    page7 = request.GET.get('page7')
    posts_7 = paginator7.get_page(page7) #2024.02.05 카드그룹관리 설날항목 추가
     
    return render(request, 'praiseRegedit.html', {'posts_All':posts_All,'posts_1':posts_1,'posts_2':posts_2,'posts_3':posts_3, 'posts_4':posts_4,'posts_5':posts_5,'posts_6':posts_6,'posts_7':posts_7, 'token':selectUserTokens, 'manage':selectManageTokens})

@login_required(login_url='/accounts/signin/')
def praiseModify(request, compliment_id):
    print("### [VIEW] praiseModify ####################################################")
    
    ##########################
    # POST 수신시
    ##########################
    if request.method == 'POST':
        
        for key, value in request.POST.items():
            print(key, value)

        print("### [INPUT] praiseModify compliment_id ###########", compliment_id)
        
        #-------------
        # 업무로직
        #-------------
        if compliment_id:
            print("### [VIEW] praiseModify compliment_id call #########################")
            try:
                updateUserPraise = UserPraise.objects.get(compliment_id=compliment_id) 

                # 등록직원
                selectUser1 = User2.objects.get(id=updateUserPraise.praise_id)
                sendUser = selectUser1.employee_name

                # 칭찬직원
                selectUser2 = User2.objects.get(id=updateUserPraise.user_id)
                recvUser = selectUser2.employee_name
                
                try:
                    
                    print("### [VIEW] praiseModify openAI call #########################")
                    
                    # ------------------------------------------------------------------
                    # openAI call
                    # ------------------------------------------------------------------
                    outputJson = openAi(inputData, sendUser, recvUser)
                    short_content = outputJson['summary']
                    tag           = {'tag': outputJson['tag']}
                    emotion_ratio = ''

                    # openai 값
                    updateUserPraise.short_content  = short_content
                    updateUserPraise.tag            = tag
                    updateUserPraise.emotion_ratio  = emotion_ratio  
                    
                except:
                    try:

                        print("### [VIEW] praiseModify ai call #########################")
                        # ------------------------------------------------------------------
                        # ai call
                        # ------------------------------------------------------------------
                        def checkWords ():
                            print("### [VIEW][LOG] text checking === ")

                            exclude_words = [sendUser, recvUser, '과장']

                            result = ' '.join([word for word in inputData.split() if word not in exclude_words])
                            print("### [VIEW][LOG] text converse : ", result)
                            text = result

                            okt = Okt()

                            tag_words = [word for word in okt.nouns(text) if word not in exclude_words][:3]
                            tag           = {'tag': tag_words}
                            
                            #short_content = summarize(text)
                            if short_content == '':
                                short_content = text
                            
                            emotion_ratio = 0

                            print("### [VIEW][LOG] 요약 내용:", short_content)
                            print("### [VIEW][LOG] 주요 태그:", tag)

                            return short_content, tag

                        checkWords()

                        #-------------
                        # DB Update
                        #-------------
                        updateUserPraise = UserPraise.objects.get(compliment_id=insertUserPraise.compliment_id) 

                        updateUserPraise.short_content  = short_content
                        updateUserPraise.tag            = tag
                        updateUserPraise.emotion_ratio  = emotion_ratio

                    except:
                        #-------------
                        # 오류내용 SET
                        #-------------
                        print("### [VIEW][LOG][ERROR openAi] 칭찬글 분석시 오류가 발생 했습니다.")
                        #print("에러 메시지:", str(e))

                        #-------------
                        # ERROR DB Update
                        #-------------
                        updateUserPraise = UserPraise.objects.get(compliment_id=insertUserPraise.compliment_id) 
                        updateUserPraise.short_content  = '시스템 확인 중 입니다.'
                        updateUserPraise.tag            = {'tag': ['확인중']}
                        updateUserPraise.emotion_ratio  = ''
                        
                #################################################
                # DB UPDATE
                #################################################
                updateUserPraise.compliment_type  = '1'
                updateUserPraise.content          = request.POST['input_Contents']
                updateUserPraise.images_id        = request.POST['input_swiper_id']
                
                updateUserPraise.chg_date         = datetime.now()

                if request.POST.get('input_active') in ['on', 'Y']:
                    updateUserPraise.is_active = 'Y'
                else:
                    updateUserPraise.is_active = 'N'
                                     
                updateUserPraise.save()

                return redirect('praiseDetail', compliment_id=compliment_id) 

            except:
                error = "입력이 잘못 되었습니다."
                return render(request, 'praiseModify.html', {'error': error})

        else:
            error = "입력된 데이터가 없습니다."
            return render(request, 'praiseRegedit.html', {'error': error})
        
    ##########################
    # 조회하면
    ##########################
    
    #-------------
    # 이미지 업무로직
    #-------------
    selectUserImages = UserImages.objects.filter(is_open='Y', is_active='Y').order_by('-reg_date')
    
    for row in selectUserImages.values():
        print(row)
            
    paginator = Paginator(selectUserImages, 10)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    
    #-------------
    # 원장내용 업무로직
    #-------------
    selectUserPraise = UserPraise.objects.filter(pk=compliment_id, is_active='Y').prefetch_related('praise', 'images').annotate(
        praise_employee_name=F('praise__employee_name'),
        user_employee_name=F('user__employee_name'),
        image_path=F('images__image_path')
    ).first()
        
    return render(request, 'praiseModify.html', {'info':selectUserPraise,'posts':posts})


@login_required(login_url='/accounts/signin/')
def manageImage(request):
    print("### [VIEW] manageImage ####################################################")
    
    #-------------
    # 사용자 검증
    #-------------
    if request.user.is_superuser :
        print("### 관리자 접속")
    else :
        print("### 사용자 접속")
        error = "[101] 관리자 외 접속 불가합니다."
        return render(request, 'page_error.html', {'error': error})  
    
    ##########################
    # POST 수신시
    ##########################
    if request.method == 'POST':
        
        for key, value in request.POST.items():
            print(key, value)
                
        for key, file in request.FILES.items():
            print(key, file)
                
        #-------------
        # 업무로직
        #-------------
        if 'card_regedit' in request.POST:
            
            try:
                insertUserImages = UserImages()
                #################################################
                # 이미지 파일 업로드
                #################################################
                if request.FILES.get('card_image'):
                    try: 
                        # print("### [Image] card_image ==========")
                        formFile = request.FILES['card_image']
                        today = date.today().strftime("%Y%m%d")
                        now = datetime.now()
                        time_string = now.strftime("%H%M%S")
                        path = 'user_' + str(request.user.id) + '/' + today
                        filename = time_string + '_' + formFile.name
                        # 이미지 저장
                        filePath = save_image(formFile, path, filename)
                        # 파일 저장 후, 저장된 경로를 출력
                        # print("### filename", filename)
                        # print("### file url", os.path.join(settings.MEDIA_URL, filename))

                        # filePath = os.path.join(settings.MEDIA_URL, filename)
                        fileYn   = 'Y'
                        insertUserImages.image_path            = filePath
                    except:
                        error = "[402] 파일 업로드가 잘못 되었습니다."
                        return render(request, 'manage/manageImage.html', {'error': error})    

                #################################################
                # DB UPDATE
                #################################################
                card_code = int(request.POST['card_code'])  # request.POST['card_code']를 정수로 변환

                if card_code == 1:
                    card_name = '감사'
                elif card_code == 2:
                    card_name = '응원'
                elif card_code == 3:
                    card_name = '축하'
                elif card_code == 4:
                    card_name = '재미'
                elif card_code == 5:
                    card_name = '새해'
                elif card_code == 6:
                    card_name = '위비' #2024.01.29 카드그룹관리 위비항목 추가
                elif card_code == 7:
                    card_name = '설날' #2024.02.05 카드그룹관리 설날항목 추가
                
                insertUserImages.card_code     = request.POST['card_code']
                insertUserImages.card_name     = card_name
                insertUserImages.card_message  = request.POST['card_message']
                insertUserImages.is_open       = request.POST['card_yn']
                insertUserImages.is_active     = 'Y'
                insertUserImages.reg_date      = datetime.now()
                insertUserImages.save()
                
                #-------------
                # 출력내용 SET
                #-------------
                selectUserImages = UserImages.objects.filter(is_active='Y').order_by('-reg_date')

                paginator = Paginator(selectUserImages, 10)
                page = request.GET.get('page')
                images = paginator.get_page(page)

                return render(request, 'manage/manageImage.html', {'images':images})
            
            
            except:
                error = "[403] 입력이 잘못 되었습니다."
                return render(request, 'manage/manageImage.html', {'error': error}) 
        
        elif 'card_update' in request.POST:
            
            try:
                updateImages = UserImages.objects.get(id=request.POST['card_id'])
                #################################################
                # 이미지 파일 업로드
                #################################################
                if request.FILES.get('card_image'):
                    try: 
                        print("### [Image] card_image ==========")
                        formFile = request.FILES['card_image']
                        today = date.today().strftime("%Y%m%d")
                        now = datetime.now()
                        time_string = now.strftime("%H%M%S")
                        path = 'user_' + str(request.user.id) + '/' + today
                        filename = time_string + '_' + formFile.name
                        # 이미지 저장
                        filePath = save_image(formFile, path, filename)
                        # 파일 저장 후, 저장된 경로를 출력
                        # print("### filename", filename)
                        # print("### file url", os.path.join(settings.MEDIA_URL, filename))

                        # filePath = os.path.join(settings.MEDIA_URL, filename)
                        fileYn   = 'Y'
                        updateImages.image_path            = filePath
                    except:
                        print("### 파일 저장 중 오류 발생:", str(e))
                        
                        error = "[402] 파일 업로드가 잘못 되었습니다."
                        return render(request, 'manage/manageImage.html', {'error': error})    

                #################################################
                # DB UPDATE
                #################################################
                card_code = int(request.POST['card_code'])  # request.POST['card_code']를 정수로 변환

                if card_code == 1:
                    card_name = '감사'
                elif card_code == 2:
                    card_name = '응원'
                elif card_code == 3:
                    card_name = '축하'
                elif card_code == 4:
                    card_name = '재미'
                elif card_code == 5:
                    card_name = '새해'
                elif card_code == 6:
                    card_name = '위비' #2024.01.29 카드그룹관리 위비항목 추가
                elif card_code == 7:
                    card_name = '설날' #2024.02.05 카드그룹관리 설날항목 추가
                
                updateImages.card_code     = request.POST['card_code']
                updateImages.card_name     = card_name
                updateImages.card_message  = request.POST['card_message']
                updateImages.is_open       = request.POST['card_yn']
                updateImages.chg_date      = datetime.now()

                updateImages.save()
                
                #-------------
                # 출력내용 SET
                #-------------
                selectUserImages = UserImages.objects.filter(is_active='Y').order_by('-reg_date')

                paginator = Paginator(selectUserImages, 10)
                page = request.GET.get('page')
                images = paginator.get_page(page)

                return render(request, 'manage/manageImage.html', {'images':images})
            
            
            except:
                error = "[403] 입력이 잘못 되었습니다."
                return render(request, 'manage/manageImage.html', {'error': error})            
            
        elif 'card_delete' in request.POST:
            
            try:
                updateImages = UserImages.objects.get(id=request.POST['card_id'])
                updateImages.is_active     = 'N'
                updateImages.chg_date      = datetime.now()
                updateImages.save()

                #-------------
                # 출력내용 SET
                #-------------
                selectUserImages = UserImages.objects.filter(is_active='Y').order_by('-reg_date')

                paginator = Paginator(selectUserImages, 10)
                page = request.GET.get('page')
                images = paginator.get_page(page)

                return render(request, 'manage/manageImage.html', {'images':images})
            
            except:
                error = "[403] 입력이 잘못 되었습니다."
                return render(request, 'manage/manageImage.html', {'error': error})                        
            
        else :     
            error = "[404] 입력된 데이터가 없습니다."
            return render(request, 'manage/manageImage.html', {'error': error})
        
    ##########################
    # 조회하면
    ##########################
    
    selectUserImages = UserImages.objects.filter(is_active='Y').order_by('-reg_date')
    
    paginator = Paginator(selectUserImages, 10)
    page = request.GET.get('page')
    images = paginator.get_page(page)
            
    return render(request, 'manage/manageImage.html', {'images':images})

@login_required(login_url='/accounts/signin/')
def manageTokens(request):
    print("### [VIEW] manageTokens ####################################################")
    
    #-------------
    # 사용자 검증
    #-------------
    if request.user.is_superuser :
        print("### 관리자 접속")
    else :
        print("### 사용자 접속")
        error = "[101] 관리자 외 접속 불가합니다."
        return render(request, 'page_error.html', {'error': error})  
    
    ##########################
    # POST 수신시
    ##########################
    if request.method == 'POST':
        
        for key, value in request.POST.items():
            print(key, value)
                
        for key, file in request.FILES.items():
            print(key, file)
                
        #-------------
        # 업무로직
        #-------------
        if 'token_regedit' in request.POST:
            
            try:
                insertManageTokens = ManageTokens()
                #################################################
                # DB UPDATE
                #################################################
                start_date = request.POST['manage_start_date']
                end_date = request.POST['manage_end_date']

                # '-'를 기준으로 날짜를 분할
                date_parts = start_date.split('-')
                
                # 각 부분을 추출
                year = date_parts[0]  # 년(yyyy)
                quarter = date_parts[1]  # 월(mm)
                
                start_date_val = start_date.replace('-', '')  # 'yyyymmdd' 형식으로 변환
                end_date_val = end_date.replace('-', '')  # 'yyyymmdd' 형식으로 변환

                insertManageTokens.year       = year
                insertManageTokens.quarter    = quarter
                
                insertManageTokens.tokens     = request.POST['manage_tokens']
                insertManageTokens.high_tokens = request.POST['manage_high_tokens']
                insertManageTokens.start_date = start_date_val
                insertManageTokens.end_date   = end_date_val
                
                insertManageTokens.is_active  = 'Y'
                insertManageTokens.reg_date   = datetime.now()
                insertManageTokens.save()
                
                #-------------
                # 출력내용 SET
                #-------------
                selectManageTokens = ManageTokens.objects.filter(is_active='Y').order_by('-start_date')

                paginator = Paginator(selectManageTokens, 10)
                page = request.GET.get('page')
                tokens = paginator.get_page(page)

                return render(request, 'manage/manageTokens.html', {'tokens':tokens})
            
            
            except:
                error = "[403] 입력이 잘못 되었습니다."
                return render(request, 'manage/manageTokens.html', {'error': error}) 
        
        elif 'token_update' in request.POST:
            
            try:
                updateManageTokens = ManageTokens.objects.get(id=request.POST['token_id'])
                #################################################
                # DB UPDATE
                #################################################                
                start_date = request.POST['manage_start_date']
                end_date = request.POST['manage_end_date']

                # '-'를 기준으로 날짜를 분할
                date_parts = start_date.split('-')
                
                # 각 부분을 추출
                year = date_parts[0]  # 년(yyyy)
                quarter = date_parts[1]  # 월(mm)
                
                start_date_val = start_date.replace('-', '')  # 'yyyymmdd' 형식으로 변환
                end_date_val = end_date.replace('-', '')  # 'yyyymmdd' 형식으로 변환
                
                
                updateManageTokens.year       = year
                updateManageTokens.quarter    = quarter
                updateManageTokens.tokens     = request.POST['manage_tokens']
                updateManageTokens.high_tokens = request.POST['manage_high_tokens']
                updateManageTokens.start_date = start_date_val
                updateManageTokens.end_date   = end_date_val
                
                updateManageTokens.chg_date   = datetime.now()

                updateManageTokens.save()
                
                #-------------
                # 출력내용 SET
                #-------------
                selectManageTokens = ManageTokens.objects.filter(is_active='Y').order_by('-start_date')

                paginator = Paginator(selectManageTokens, 10)
                page = request.GET.get('page')
                tokens = paginator.get_page(page)

                return render(request, 'manage/manageTokens.html', {'tokens':tokens})
            
            
            except:
                error = "[403] 입력이 잘못 되었습니다."
                return render(request, 'manage/manageTokens.html', {'error': error})            
            
        elif 'token_delete' in request.POST:
            
            try:
                updateImages = ManageTokens.objects.get(id=request.POST['token_id'])
                updateImages.is_active     = 'N'
                updateImages.chg_date      = datetime.now()
                updateImages.save()

                #-------------
                # 출력내용 SET
                #-------------
                selectManageTokens = ManageTokens.objects.filter(is_active='Y').order_by('-start_date')

                paginator = Paginator(selectManageTokens, 10)
                page = request.GET.get('page')
                tokens = paginator.get_page(page)

                return render(request, 'manage/manageTokens.html', {'tokens':tokens})
            
            except:
                error = "[403] 입력이 잘못 되었습니다."
                return render(request, 'manage/manageTokens.html', {'error': error})                        
            
        else :     
            error = "[404] 입력된 데이터가 없습니다."
            return render(request, 'manage/manageTokens.html', {'error': error})
        
    ##########################
    # 조회하면
    ##########################
    selectManageTokens = ManageTokens.objects.filter(is_active='Y').order_by('-start_date')
    
    paginator = Paginator(selectManageTokens, 10)
    page = request.GET.get('page')
    tokens = paginator.get_page(page)
            
    return render(request, 'manage/manageTokens.html', {'tokens':tokens})

@login_required(login_url='/accounts/signin/')
def manageTokensGroup(request):
    print("### [VIEW] manageTokensGroup ####################################################")
    
    #-------------
    # 사용자 검증
    #-------------
    if request.user.is_superuser :
        print("### 관리자 접속")
    else :
        print("### 사용자 접속")
        error = "[101] 관리자 외 접속 불가합니다."
        return render(request, 'page_error.html', {'error': error})  
    
    ##########################
    # POST 수신시
    ##########################
    if request.method == 'POST':
        
        for key, value in request.POST.items():
            print(key, value)
                
        for key, file in request.FILES.items():
            print(key, file)
                
        #-------------
        # 업무로직
        #-------------
        if 'token_regedit' in request.POST:
            
            try:
                print('0000')

                insertManageTokensGroup = ManageTokensGroup()
                #################################################
                # DB UPDATE
                #################################################
                start_date = request.POST['manage_start_date']
                end_date = request.POST['manage_end_date']
                
                start_date_val = start_date.replace('-', '')  # 'yyyymmdd' 형식으로 변환
                end_date_val = end_date.replace('-', '')  # 'yyyymmdd' 형식으로 변환
                
                insertManageTokensGroup.start_date = start_date_val
                insertManageTokensGroup.end_date   = end_date_val
                
                insertManageTokensGroup.is_active  = 'Y'
                insertManageTokensGroup.reg_date   = datetime.now()
                insertManageTokensGroup.save()
                
                #-------------
                # 출력내용 SET
                #-------------
                selectManageTokensGroup = ManageTokensGroup.objects.filter(is_active='Y').order_by('-start_date')

                paginator = Paginator(selectManageTokensGroup, 10)
                page = request.GET.get('page')
                tokens = paginator.get_page(page)

                return render(request, 'manage/manageTokensGroup.html', {'tokens':tokens})
            
            
            except:
                error = "[403] 입력이 잘못 되었습니다."
                return render(request, 'manage/manageTokensGroup.html', {'error': error}) 
        
        elif 'token_update' in request.POST:
            
            try:
                updateManageTokensGroup = ManageTokensGroup.objects.get(id=request.POST['token_id'])
                #################################################
                # DB UPDATE
                #################################################                
                start_date = request.POST['manage_start_date']
                end_date = request.POST['manage_end_date']
                start_date_val = start_date.replace('-', '')  # 'yyyymmdd' 형식으로 변환
                end_date_val = end_date.replace('-', '')  # 'yyyymmdd' 형식으로 변환
                
                updateManageTokensGroup.start_date = start_date_val
                updateManageTokensGroup.end_date   = end_date_val
                updateManageTokensGroup.chg_date   = datetime.now()

                updateManageTokensGroup.save()
                
                #-------------
                # 출력내용 SET
                #-------------
                selectManageTokensGroup = ManageTokensGroup.objects.filter(is_active='Y').order_by('-start_date')

                paginator = Paginator(selectManageTokensGroup, 10)
                page = request.GET.get('page')
                tokens = paginator.get_page(page)

                return render(request, 'manage/manageTokensGroup.html', {'tokens':tokens})
            
            
            except:
                error = "[403] 입력이 잘못 되었습니다."
                return render(request, 'manage/manageTokensGroup.html', {'error': error})            
            
        elif 'token_delete' in request.POST:
            
            try:
                deleteManageTokensGroup = ManageTokensGroup.objects.get(id=request.POST['token_id'])
                deleteManageTokensGroup.is_active     = 'N'
                deleteManageTokensGroup.chg_date      = datetime.now()
                deleteManageTokensGroup.save()

                #-------------
                # 출력내용 SET
                #-------------
                selectManageTokensGroup = ManageTokensGroup.objects.filter(is_active='Y').order_by('-start_date')

                paginator = Paginator(selectManageTokensGroup, 10)
                page = request.GET.get('page')
                tokens = paginator.get_page(page)

                return render(request, 'manage/manageTokensGroup.html', {'tokens':tokens})
            
            except:
                error = "[403] 입력이 잘못 되었습니다."
                return render(request, 'manage/manageTokensGroup.html', {'error': error})                        
            
        else :     
            error = "[404] 입력된 데이터가 없습니다."
            return render(request, 'manage/manageTokensGroup.html', {'error': error})
        
    ##########################
    # 조회하면
    ##########################
    selectManageTokensGroup = ManageTokensGroup.objects.filter(is_active='Y').order_by('-start_date')
    
    paginator = Paginator(selectManageTokensGroup, 10)
    page = request.GET.get('page')
    tokens = paginator.get_page(page)
            
    return render(request, 'manage/manageTokensGroup.html', {'tokens':tokens})

@login_required(login_url='/accounts/signin/')
@measure_execution_time
def rankList_new(request):
    # ==========================
    # 2024-12-25 refactor and add new functions of home, search, tk_list, rankList
    # ==========================

    """Main view function for ranking list"""
    today = datetime.now().strftime('%Y%m%d')
    
    # Get manage tokens
    manage_token_id = request.GET.get('manage_token_id', 0)
    basic_tokens = get_active_tokens(ManageTokens, today)
    
    if int(basic_tokens.id) == int(manage_token_id):
        manage_token_id = 0
    
    select_tokens = (
        get_active_tokens(ManageTokens, today) if manage_token_id == 0
        else ManageTokens.objects.filter(id=manage_token_id, is_active='Y').first()
    )
    
    # Get navigation tokens
    token_prev = ManageTokens.objects.filter(
        id__lt=select_tokens.id, is_active='Y'
    ).order_by('-id').values_list('id', flat=True).first() or 0
    
    token_next = ManageTokens.objects.filter(
        id__gt=select_tokens.id, is_active='Y'
    ).order_by('id').values_list('id', flat=True).first() or 0
    
    # # Get active staff users
    # manage_user_ids = User2.objects.filter(
    #     is_staff=True, is_active=True
    # ).values_list('id', flat=True)
    
    # Handle company specific logic
    company_id = request.user.company_id
    dept_ids = []
    dept_names = []
    peer_no = ''
    
    if company_id == "20":  # 우리은행
        user_peer = ManageDept.objects.get(
            is_active='Y', 
            dept_id=request.user.department_id
        )
        peer_no = user_peer.peer_no
        
        dept_data = ManageDept.objects.filter(
            is_active='Y',
            company_id=company_id,
            peer_no=peer_no
        )
        dept_ids = [d.dept_id for d in dept_data]
        dept_names = [d.dept_name for d in dept_data]
        
        # company_filters = {
        #     'user__company_id': company_id,
        #     'user__department_id__in': dept_ids
        # }

        tag_filters = {
            'praise__company_id': company_id,
            'praise__department_id__in': dept_ids
        }
    else:
        # company_filters = {'user__company_id': company_id}
        tag_filters = {'praise__company_id': company_id}
    
    # # Get user praise data
    # base_query = get_user_tokens_base_query(
    #     select_tokens.id,
    #     company_filters,
    #     manage_user_ids
    # )
    # posts = get_user_praise_query(base_query)
    
    # Process tags
    top3_tags = process_praise_tags(select_tokens.id, tag_filters)
    
    # Handle group data
    group_tokens = get_active_tokens(ManageTokensGroup, today)
    # token_ids = ManageTokens.objects.filter(
    #     Q(start_date__gte=group_tokens.start_date) &
    #     Q(end_date__lte=group_tokens.end_date),
    #     is_active='Y'
    # ).values_list('id', flat=True)
    
    # # Determine user's group
    # groups = get_group_mapping()
    # user_group = next(
    #     (group_id for group_id, companies in groups.items() 
    #      if company_id in companies),
    #     None
    # )
    
    # # Get group data
    # if user_group:
    #     group_filters = {'user__company_id__in': groups[user_group]}
    #     group_base_query = get_user_tokens_base_query(
    #         token_ids,
    #         group_filters,
    #         manage_user_ids
    #     )
    #     posts_group = get_user_praise_query(group_base_query)
    # else:
    #     posts_group = []
    
    # # Handle superuser specific group data
    # group_data = {}
    # if request.user.is_superuser:
    #     for group_name, group_companies in groups.items():
    #         group_filters = {'user__company_id__in': group_companies}
    #         base_query = get_user_tokens_base_query(
    #             token_ids,
    #             group_filters,
    #             manage_user_ids
    #         )
    #         group_data[f'postsGroup{group_name}'] = get_user_praise_query(base_query)
    
    return render(request, 'rankList.html', {
        # 'posts': posts,
        # 'postsGroup': posts_group,
        'manageToken': select_tokens,
        'top3_result': top3_tags,
        'token_prev': token_prev,
        'token_next': token_next,
        'peer_no': peer_no,
        'dept_names': dept_names,
        'group_start_dt': group_tokens.start_date,
        'group_end_dt': group_tokens.end_date,
        # **group_data
    })

@login_required(login_url='/accounts/signin/')
@measure_execution_time
def rankList(request):
    print("### [VIEW] rankList ####################################################")

    #-------------
    # 업무로직
    #-------------
    
    ##########################
    # POST 수신시
    ##########################
    if request.method == 'POST':
        print('### [VIEW][LOG] POST ')
        
    ##########################
    # GET 수신시
    ##########################
    if 'manage_token_id' in request.GET:
        manage_token_id = request.GET['manage_token_id']
        #print('[VIEW][LOG] manage_token_id ', manage_token_id)
    else : 
        manage_token_id = 0
        
    print('[VIEW][LOG] manage_token_id ', manage_token_id)            
    #--------------
    # 토큰기준
    #--------------
    today = datetime.now().strftime('%Y%m%d')
    baiscManageTokens = ManageTokens.objects.filter(
        Q(start_date__lte=today) & Q(end_date__gte=today)
    ).first()
    
    #-------------
    # 토큰발행여부 검증
    #-------------
    if not baiscManageTokens:
        print("### 토큰 정상필요 baiscManageTokens")
        baiscManageTokens = ManageTokens.objects.filter(
            is_active='Y'
        ).order_by('-end_date').first()
        
        #error = "[안내] 관리자에게 문의 요청 드립니다. 발행된 토큰이 없습니다"
        #return render(request, 'page_error.html', {'error': error})
    
    #print('### baiscManageTokens.id', baiscManageTokens.id)
    
    if int(baiscManageTokens.id) == int(manage_token_id):
        manage_token_id = 0
        print('### chg manage_token_id', manage_token_id)
    
    if manage_token_id == 0:
        selectManageTokens = ManageTokens.objects.filter(
            Q(start_date__lte=today) & Q(end_date__gte=today),
            is_active = 'Y'
        ).first()
        
        if not selectManageTokens:
            print("### 토큰 정상필요 selectManageTokens")
            selectManageTokens = ManageTokens.objects.filter(
                is_active='Y'
            ).order_by('-end_date').first()
        
    else:
        selectManageTokens = ManageTokens.objects.filter(
            id=manage_token_id, is_active = 'Y'
        ).first()
        

    subquery_prev = ManageTokens.objects.filter(
        id__lt=selectManageTokens.id,
        is_active = 'Y'
    ).order_by('-id').first()

    subquery_next = ManageTokens.objects.filter(
        id__gt=selectManageTokens.id,
        is_active = 'Y'
    ).order_by('id').first()

    if subquery_prev:
        token_prev = subquery_prev.id
    else:
        token_prev = 0

    if subquery_next:
        token_next = subquery_next.id
    else:
        token_next = 0

    #print('### selectManageTokens id ', selectManageTokens.id)
    #print('### selectManageTokens token_prev ', token_prev)
    #print('### selectManageTokens token_next ', token_next)
    
    #-------------
    # 운영자 대상추출
    #-------------
    selectManageUser = User2.objects.filter(
        is_staff=True,
        is_active=True
    )
                
    ManageUser_ids = [ManageUser.id for ManageUser in selectManageUser]
    print('### [LOG] ManageUser_ids', ManageUser_ids)

    #-------------
    # 칭찬정보
    #-------------
    print('### user.company_id', request.user.company_id)
    peer_no = ''
    dept_names = ''
    
    # 우리은행 경우,Peer 기준으로 조회
    if request.user.company_id == "20" :
        selectUserPeerNo = ManageDept.objects.get(is_active='Y', dept_id=request.user.department_id)
        
        peer_no = selectUserPeerNo.peer_no
        print('### peer_no', peer_no)
        
        selectManageDept = ManageDept.objects.filter(is_active='Y', company_id=request.user.company_id, peer_no=peer_no)
        
        #for dept in selectManageDept:
        #    print('selectManageDept :', dept.dept_id, dept.dept_name, dept.peer_no)    
    
        dept_ids = [dept.dept_id for dept in selectManageDept]
        dept_names = [dept.dept_name for dept in selectManageDept]
        #print('dept_ids', dept_ids)
        
        subquery = UserTokens.objects.filter(
            token_id=selectManageTokens.id,
            is_active='Y',
            user__company_id=request.user.company_id,
            user__department_id__in=dept_ids
        ).annotate(
            #user_id=F('user__id'),
            #chg_date=F('chg_date'),
            employee_id=F('user__employee_id'),
            employee_name=F('user__employee_name'),
            company_id=F('user__company_id'),
            company_name=F('user__company_name'),
            department_name=F('user__department_name'),
            position_id=F('user__position_id'),
            position_name=F('user__position_name'),
            user_image_yn=F('user__image_yn'),
            user_image=F('user__image'),
            recev_point=ExpressionWrapper(F('received_tokens') * 1, output_field=fields.IntegerField()),
            send_point=ExpressionWrapper(F('my_send_tokens') * 1, output_field=fields.IntegerField()) # 2024.3.4부터 보낸 포인트 *2 > *1 
        ).exclude(
            user_id__in=ManageUser_ids
        ).values(
            'user_id', 'chg_date', 'employee_id', 'employee_name', 'company_id', 'company_name', 'department_name','position_id','position_name', 'user_image_yn', 'user_image','recev_point', 'send_point'
        )
        
        selectUserPraise = subquery.annotate(
            reward_skip_yn=Coalesce(
                Subquery(
                    ManagePosi.objects.filter(
                        is_active="Y",
                        company_id=OuterRef('company_id'),
                        posi_id=OuterRef('position_id'),
                        reward_skip_yn__isnull=False
                    ).values('reward_skip_yn')[:1]
                ), Value('N')  # 기본값으로 'N' 사용
            ),
            tot_point=ExpressionWrapper(F('recev_point') + F('send_point'), output_field=fields.IntegerField())
        ).exclude(reward_skip_yn='Y'
        ).filter(tot_point__gt=0  # 1포인트 이상 조건
        ).order_by('-tot_point', 'chg_date').values(
            'user_id', 'chg_date', 'employee_id', 'employee_name', 'company_id', 'company_name', 'department_name','position_id','position_name', 'user_image_yn', 'user_image', 'recev_point', 'send_point','tot_point', 'reward_skip_yn'
        )
                
    
    else : 
        subquery = UserTokens.objects.filter(
            token_id=selectManageTokens.id,
            is_active='Y',
            user__company_id=request.user.company_id
        ).annotate(
            #user_id=F('user__id'),
            #chg_date=F('chg_date'),
            employee_id=F('user__employee_id'),
            employee_name=F('user__employee_name'),
            company_id=F('user__company_id'),
            company_name=F('user__company_name'),
            department_name=F('user__department_name'),
            position_id=F('user__position_id'),
            position_name=F('user__position_name'),
            user_image_yn=F('user__image_yn'),
            user_image=F('user__image'),
            recev_point=ExpressionWrapper(F('received_tokens') * 1, output_field=fields.IntegerField()),
            send_point=ExpressionWrapper(F('my_send_tokens') * 1, output_field=fields.IntegerField()) # 2024.3.4부터 보낸 포인트 *2 > *1 
        ).exclude(
            user_id__in=ManageUser_ids
        ).values(
            'user_id', 'chg_date', 'employee_id', 'employee_name', 'company_id', 'company_name', 'department_name','position_id','position_name', 'user_image_yn', 'user_image','recev_point', 'send_point'
        )

        selectUserPraise = subquery.annotate(
            reward_skip_yn=Coalesce(
                Subquery(
                    ManagePosi.objects.filter(
                        is_active="Y",
                        company_id=OuterRef('company_id'),
                        posi_id=OuterRef('position_id'),
                        reward_skip_yn__isnull=False
                    ).values('reward_skip_yn')[:1]
                ), Value('N')  # 기본값으로 'N' 사용
            ),
            tot_point=ExpressionWrapper(F('recev_point') + F('send_point'), output_field=fields.IntegerField())
        ).exclude(reward_skip_yn='Y'
        ).filter(tot_point__gt=0  # 1포인트 이상 조건
        ).order_by('-tot_point', 'chg_date').values(
            'user_id', 'chg_date', 'employee_id', 'employee_name', 'company_id', 'company_name', 'department_name','position_id','position_name', 'user_image_yn', 'user_image', 'recev_point', 'send_point','tot_point', 'reward_skip_yn'
        )
        
    # 출력부 SET
    paginator = Paginator(selectUserPraise, 10)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
        
        
    #for item in selectUserPraise:
    #    print(item)
        
    #-----------------------------     
    # TAG 추출
    #-----------------------------

    # 우리은행 경우,Peer 기준으로 조회
    if request.user.company_id == "20" :

        praise_tags = (
            UserPraise.objects
            .filter(is_active='Y', token_id = selectManageTokens.id, praise__company_id=request.user.company_id, praise__department_id__in=dept_ids)
            .values('praise_id', 'tag')
        )
        
    else :
        
        praise_tags = (
            UserPraise.objects
            .filter(is_active='Y', token_id = selectManageTokens.id, praise__company_id=request.user.company_id)
            .values('praise_id', 'tag')
        )
        
    # praise_id별로 tag 값을 모아서 저장하기 위한 딕셔너리
    praise_tags_dict = {}

    # 결과 반복문으로 순회하며 데이터 저장
    for praise in praise_tags:
        praise_id = praise['praise_id']
        tag = praise['tag']
        
        if tag.startswith("{") and tag.endswith("}"):
            tag = json.loads(tag.replace("'", "\""))
        else:
            tag = {'tag': []}
                    
        if praise_id in praise_tags_dict:
            praise_tags_dict[praise_id].append(tag)
        else:
            praise_tags_dict[praise_id] = [tag]
            

    # 결과 출력
    tag_result = {}
    temp = []
    for praise_id, tags in praise_tags_dict.items():
        #print("### tag 0 === ",praise_id, tags)   
        
        temp = []
        for tag in tags:
            #print("### tags 2 ", tag['tag'])
            temp.extend( tag['tag'])
            #print("### temp ", temp)
            
        #tag_result.append({'praise_id': praise_id, 'tag': temp})
        tag_result[praise_id] = temp
        #print("### tag_result ", tag_result)
            

    top3_result = {}
    for key, value in tag_result.items():
        counter = Counter(value)
        #print(f"Key {key}: {counter.most_common(3)}")
        #print(f"Key {key}: {[i[0] for i in counter.most_common(3)]}")
        top3_result[key] = [i[0] for i in counter.most_common(3)]
        
        
    #print("top3_result", top3_result)    
        
    
    #-----------------------------     
    # 그룹사 추출
    #-----------------------------
    
    GroupManageTokensGroup = ManageTokensGroup.objects.filter(
        Q(start_date__lte=today) & Q(end_date__gte=today)
    ).first()
    
    if not GroupManageTokensGroup:
        print("### 토큰(그룹) 입력필요")
        GroupManageTokensGroup = ManageTokensGroup.objects.filter(
            is_active='Y'
        ).order_by('-end_date').first()
        #error = "[안내] 관리자에게 문의 요청 드립니다. 토큰그룹 정보가 없습니다"
        #return render(request, 'page_error.html', {'error': error})
    
    # print('### GroupManageTokensGroup', GroupManageTokensGroup.id, GroupManageTokensGroup.start_date, GroupManageTokensGroup.end_date )
    
    group_start_dt = GroupManageTokensGroup.start_date
    group_end_dt = GroupManageTokensGroup.end_date
    
    GroupManageTokens = ManageTokens.objects.filter(
        Q(start_date__gte=group_start_dt) &
        Q(end_date__lte=group_end_dt),
        is_active='Y'    )
                
    token_ids = [token.id for token in GroupManageTokens]
    print('token_ids', token_ids)
            
    # A_Group_ids = ["20", "95", "B1", "E5", "D2", "E3"]
    # B_Group_ids = ["B3", "C1", "C7", "C9", "D1", "E1", "E4", "E6", "E7", "E8", "W5"]
    
    A_Group_ids = ["20"] #20:우리은행
    B_Group_ids = ["95", "E5", "B3", "B1"] #95:우리은행, E5:우리금융캐피탈, B3:우리금융지주, B1:우리에프아이에스
    C_Group_ids = ["D2", "E3", "E1", "C9", "E6"] #D2:우리종합금융, E3:우리자산신탁, E1:우리자산운용, C9:우리신용정보, E6:우리금융저축은행
    D_Group_ids = ["C7", "E8", "D1", "C1", "E7"] #C7:우리펀드서비스, E8:우리벤처파트너스, D1:우리금융경영연구소, C1:우리프라이빗에퀴티자산운용, E7:우리금융에프앤아이


    # 우리은행 경우,Peer 기준으로 조회
    if request.user.company_id in A_Group_ids:
        Group_ids    = A_Group_ids
    
    if request.user.company_id in B_Group_ids:
        Group_ids    = B_Group_ids
    
    if request.user.company_id in C_Group_ids:
        Group_ids    = C_Group_ids
    
    if request.user.company_id in D_Group_ids:
        Group_ids    = D_Group_ids

    subqueryGroup = UserTokens.objects.filter(
        token_id__in = token_ids,
        is_active='Y',
        user__company_id__in=Group_ids
    ).annotate(
        #user_id=F('user__id'),
        #chg_date=F('chg_date'),
        employee_id=F('user__employee_id'),
        employee_name=F('user__employee_name'),
        company_id=F('user__company_id'),
        company_name=F('user__company_name'),
        department_name=F('user__department_name'),
        position_id=F('user__position_id'),
        position_name=F('user__position_name'),
        user_image_yn=F('user__image_yn'),
        user_image=F('user__image'),
        recev_point=ExpressionWrapper(F('received_tokens') * 1, output_field=fields.IntegerField()),
        send_point=ExpressionWrapper(F('my_send_tokens') * 1, output_field=fields.IntegerField()) # 2024.3.4부터 보낸 포인트 *2 > *1 
    ).exclude(
            user_id__in=ManageUser_ids
    ).values(
        'user_id', 'chg_date', 'employee_id', 'employee_name', 'company_id', 'company_name', 'department_name','position_id','position_name', 'user_image_yn', 'user_image','recev_point', 'send_point'
    )
        
    selectUserPraiseGroup = subqueryGroup.values('user_id', 'employee_id', 'employee_name', 'company_id', 'company_name', 'department_name', 'position_id', 'position_name', 'user_image_yn', 'user_image').annotate(
        reward_skip_yn=Coalesce(
            Subquery(
                ManagePosi.objects.filter(
                    is_active="Y",
                    company_id=OuterRef('company_id'),
                    posi_id=OuterRef('position_id'),
                    reward_skip_yn__isnull=False
                ).values('reward_skip_yn')[:1]
            ), Value('N')  # 기본값으로 'N' 사용
        ),
        tot_point=Sum(ExpressionWrapper(F('recev_point') + F('send_point'), output_field=fields.IntegerField()))
    ).exclude(reward_skip_yn='Y'
    ).filter(tot_point__gt=0  # 1포인트 이상 조건
    ).order_by('-tot_point'
    ).values(
        'user_id', 'employee_id', 'employee_name', 'company_id', 'company_name', 'department_name', 'position_id', 'position_name', 'user_image_yn', 'user_image', 'tot_point', 'reward_skip_yn'
    )
            
    # 출력부 SET
    paginator = Paginator(selectUserPraiseGroup, 10)
    page = request.GET.get('page')
    postsGroup = paginator.get_page(page)

    #-------------
    # 2023-12-14 관리자 그룹순위 제공
    #-------------
    if request.user.is_superuser :
        
        # A_Group_ids = ["20", "95", "B1", "E5", "D2", "E3"]
        # B_Group_ids = ["B3", "C1", "C7", "C9", "D1", "E1", "E4", "E6", "E7", "E8"]
        A_Group_ids = ["20"] #20:우리은행
        B_Group_ids = ["95", "E5", "B3", "B1"] #95:우리은행, E5:우리금융캐피탈, B3:우리금융지주, B1:우리에프아이에스
        C_Group_ids = ["D2", "E3", "E1", "C9", "E6"] #D2:우리종합금융, E3:우리자산신탁, E1:우리자산운용, C9:우리신용정보, E6:우리금융저축은행
        D_Group_ids = ["C7", "E8", "D1", "C1", "E7"] #C7:우리펀드서비스, E8:우리벤처파트너스, D1:우리금융경영연구소, C1:우리프라이빗에퀴티자산운용, E7:우리금융에프앤아이
            
        #-----------
        # Group A
        #-----------
        subqueryGroupA = UserTokens.objects.filter(
            token_id__in = token_ids,
            is_active='Y',
            user__company_id__in=A_Group_ids
        ).annotate(
            #user_id=F('user__id'),
            #chg_date=F('chg_date'),
            employee_id=F('user__employee_id'),
            employee_name=F('user__employee_name'),
            company_id=F('user__company_id'),
            company_name=F('user__company_name'),
            department_name=F('user__department_name'),
            position_id=F('user__position_id'),
            position_name=F('user__position_name'),
            user_image_yn=F('user__image_yn'),
            user_image=F('user__image'),
            recev_point=ExpressionWrapper(F('received_tokens') * 1, output_field=fields.IntegerField()),
            send_point=ExpressionWrapper(F('my_send_tokens') * 1, output_field=fields.IntegerField()) # 2024.3.4부터 보낸 포인트 *2 > *1 
        ).exclude(
            user_id__in=ManageUser_ids
        ).values(
            'user_id', 'chg_date', 'employee_id', 'employee_name', 'company_id', 'company_name', 'department_name','position_id','position_name', 'user_image_yn', 'user_image','recev_point', 'send_point'
        )
        print("subqueryGroupA::::::::::::::subqueryGroupA******* : ", subqueryGroupA)
            
        selectUserPraiseGroupA = subqueryGroupA.values('user_id', 'employee_id', 'employee_name', 'company_id', 'company_name', 'department_name', 'position_id', 'position_name', 'user_image_yn', 'user_image').annotate(
            reward_skip_yn=Coalesce(
                Subquery(
                    ManagePosi.objects.filter(
                        is_active="Y",
                        company_id=OuterRef('company_id'),
                        posi_id=OuterRef('position_id'),
                        reward_skip_yn__isnull=False
                    ).values('reward_skip_yn')[:1]
                ), Value('N')  
            ),
            tot_point=Sum(ExpressionWrapper(F('recev_point') + F('send_point'), output_field=fields.IntegerField()))
        ).exclude(reward_skip_yn='Y'
        ).filter(tot_point__gt=0  
        ).order_by('-tot_point'
        ).values(
            'user_id', 'employee_id', 'employee_name', 'company_id', 'company_name', 'department_name', 'position_id', 'position_name', 'user_image_yn', 'user_image', 'tot_point', 'reward_skip_yn'
        )
        
        # print("selectUserPraiseGroupA::::::::::::::selectUserPraiseGroupA******* : ", selectUserPraiseGroupA)

        # 
        paginatorA = Paginator(selectUserPraiseGroupA, 10)
        pageGroupA = request.GET.get('pageGroupA')
        postsGroupA = paginatorA.get_page(pageGroupA)
        
        #-----------
        # Group B
        #-----------
        subqueryGroupB = UserTokens.objects.filter(
            token_id__in = token_ids,
            is_active='Y',
            user__company_id__in=B_Group_ids
        ).annotate(
            #user_id=F('user__id'),
            #chg_date=F('chg_date'),
            employee_id=F('user__employee_id'),
            employee_name=F('user__employee_name'),
            company_id=F('user__company_id'),
            company_name=F('user__company_name'),
            department_name=F('user__department_name'),
            position_id=F('user__position_id'),
            position_name=F('user__position_name'),
            user_image_yn=F('user__image_yn'),
            user_image=F('user__image'),
            recev_point=ExpressionWrapper(F('received_tokens') * 1, output_field=fields.IntegerField()),
            send_point=ExpressionWrapper(F('my_send_tokens') * 1, output_field=fields.IntegerField()) # 2024.3.4부터 보낸 포인트 *2 > *1 
        ).exclude(
            user_id__in=ManageUser_ids
        ).values(
            'user_id', 'chg_date', 'employee_id', 'employee_name', 'company_id', 'company_name', 'department_name','position_id','position_name', 'user_image_yn', 'user_image','recev_point', 'send_point'
        )
            
        selectUserPraiseGroupB = subqueryGroupB.values('user_id', 'employee_id', 'employee_name', 'company_id', 'company_name', 'department_name', 'position_id', 'position_name', 'user_image_yn', 'user_image').annotate(
            reward_skip_yn=Coalesce(
                Subquery(
                    ManagePosi.objects.filter(
                        is_active="Y",
                        company_id=OuterRef('company_id'),
                        posi_id=OuterRef('position_id'),
                        reward_skip_yn__isnull=False
                    ).values('reward_skip_yn')[:1]
                ), Value('N')  
            ),
            tot_point=Sum(ExpressionWrapper(F('recev_point') + F('send_point'), output_field=fields.IntegerField()))
        ).exclude(reward_skip_yn='Y'
        ).filter(tot_point__gt=0  # 1??ъ씤??? ??댁긽 議곌굔
        ).order_by('-tot_point'
        ).values(
            'user_id', 'employee_id', 'employee_name', 'company_id', 'company_name', 'department_name', 'position_id', 'position_name', 'user_image_yn', 'user_image', 'tot_point', 'reward_skip_yn'
        )
                
        paginatorB = Paginator(selectUserPraiseGroupB, 10)
        pageGroupB = request.GET.get('pageGroupB')
        postsGroupB = paginatorB.get_page(pageGroupB)
        
        #-----------
        # Group C
        #-----------
        subqueryGroupC = UserTokens.objects.filter(
            token_id__in = token_ids,
            is_active='Y',
            user__company_id__in=C_Group_ids
        ).annotate(
            #user_id=F('user__id'),
            #chg_date=F('chg_date'),
            employee_id=F('user__employee_id'),
            employee_name=F('user__employee_name'),
            company_id=F('user__company_id'),
            company_name=F('user__company_name'),
            department_name=F('user__department_name'),
            position_id=F('user__position_id'),
            position_name=F('user__position_name'),
            user_image_yn=F('user__image_yn'),
            user_image=F('user__image'),
            recev_point=ExpressionWrapper(F('received_tokens') * 1, output_field=fields.IntegerField()),
            send_point=ExpressionWrapper(F('my_send_tokens') * 1, output_field=fields.IntegerField()) # 2024.3.4부터 보낸 포인트 *2 > *1 
        ).exclude(
            user_id__in=ManageUser_ids
        ).values(
            'user_id', 'chg_date', 'employee_id', 'employee_name', 'company_id', 'company_name', 'department_name','position_id','position_name', 'user_image_yn', 'user_image','recev_point', 'send_point'
        )
            
        selectUserPraiseGroupC = subqueryGroupC.values('user_id', 'employee_id', 'employee_name', 'company_id', 'company_name', 'department_name', 'position_id', 'position_name', 'user_image_yn', 'user_image').annotate(
            reward_skip_yn=Coalesce(
                Subquery(
                    ManagePosi.objects.filter(
                        is_active="Y",
                        company_id=OuterRef('company_id'),
                        posi_id=OuterRef('position_id'),
                        reward_skip_yn__isnull=False
                    ).values('reward_skip_yn')[:1]
                ), Value('N')  
            ),
            tot_point=Sum(ExpressionWrapper(F('recev_point') + F('send_point'), output_field=fields.IntegerField()))
        ).exclude(reward_skip_yn='Y'
        ).filter(tot_point__gt=0  # 1??ъ씤??? ??댁긽 議곌굔
        ).order_by('-tot_point'
        ).values(
            'user_id', 'employee_id', 'employee_name', 'company_id', 'company_name', 'department_name', 'position_id', 'position_name', 'user_image_yn', 'user_image', 'tot_point', 'reward_skip_yn'
        )
                
        paginatorC = Paginator(selectUserPraiseGroupC, 10)
        pageGroupC = request.GET.get('pageGroupC')
        postsGroupC = paginatorC.get_page(pageGroupC)

        #-----------
        # Group D
        #-----------
        # D_Group_ids = ["C7", "E8", "D1", "C1", "E7"] #C7:우리펀드서비스, E8:우리벤처파트너스, D1:우리금융경영연구소, C1:우리프라이빗에퀴티자산운용, E7:우리금융에프앤아이
        subqueryGroupD = UserTokens.objects.filter(
            token_id__in = token_ids,
            is_active='Y',
            user__company_id__in=D_Group_ids
        ).annotate(
            #user_id=F('user__id'),
            #chg_date=F('chg_date'),
            employee_id=F('user__employee_id'),
            employee_name=F('user__employee_name'),
            company_id=F('user__company_id'),
            company_name=F('user__company_name'),
            department_name=F('user__department_name'),
            position_id=F('user__position_id'),
            position_name=F('user__position_name'),
            user_image_yn=F('user__image_yn'),
            user_image=F('user__image'),
            recev_point=ExpressionWrapper(F('received_tokens') * 1, output_field=fields.IntegerField()),
            send_point=ExpressionWrapper(F('my_send_tokens') * 1, output_field=fields.IntegerField()) # 2024.3.4부터 보낸 포인트 *2 > *1 
        ).exclude(
            user_id__in=ManageUser_ids
        ).values(
            'user_id', 'chg_date', 'employee_id', 'employee_name', 'company_id', 'company_name', 'department_name','position_id','position_name', 'user_image_yn', 'user_image','recev_point', 'send_point'
        )
            
        selectUserPraiseGroupD = subqueryGroupD.values('user_id', 'employee_id', 'employee_name', 'company_id', 'company_name', 'department_name', 'position_id', 'position_name', 'user_image_yn', 'user_image').annotate(
            reward_skip_yn=Coalesce(
                Subquery(
                    ManagePosi.objects.filter(
                        is_active="Y",
                        company_id=OuterRef('company_id'),
                        posi_id=OuterRef('position_id'),
                        reward_skip_yn__isnull=False
                    ).values('reward_skip_yn')[:1]
                ), Value('N')  
            ),
            tot_point=Sum(ExpressionWrapper(F('recev_point') + F('send_point'), output_field=fields.IntegerField()))
        ).exclude(reward_skip_yn='Y'
        ).filter(tot_point__gt=0  # 1??ъ씤??? ??댁긽 議곌굔
        ).order_by('-tot_point'
        ).values(
            'user_id', 'employee_id', 'employee_name', 'company_id', 'company_name', 'department_name', 'position_id', 'position_name', 'user_image_yn', 'user_image', 'tot_point', 'reward_skip_yn'
        )
                
        paginatorD = Paginator(selectUserPraiseGroupD, 10)
        pageGroupD = request.GET.get('pageGroupC')
        postsGroupD = paginatorD.get_page(pageGroupD)


        # print("postsGroupA : ", postsGroupA)
        # print("postsGroupB : ", postsGroupB)
        # print("postsGroupC : ", postsGroupC)
        # print("postsGroupD : ", postsGroupD)

    else :
        postsGroupA = ''
        postsGroupB = ''
        postsGroupC = ''
        postsGroupD = ''
    
    return render(request, 'rankList.html', {'posts':posts, 'postsGroup':postsGroup, 'postsGroupA':postsGroupA, 'postsGroupB':postsGroupB, 'postsGroupC':postsGroupC, 'postsGroupD':postsGroupD, 'manageToken':selectManageTokens, 'top3_result':top3_result,'token_prev':token_prev,'token_next':token_next,'peer_no':peer_no, 'dept_names':dept_names, 'group_start_dt':group_start_dt, 'group_end_dt':group_end_dt})

@login_required(login_url='/accounts/signin/')
def manageMember(request):
    print("### [VIEW] manageMember ####################################################")
        
    ##########################
    # POST 수신시
    ##########################
    if request.method == 'POST':
        for key, value in request.POST.items():
            print(key, value)            

    ##########################
    # GET 수신시
    ##########################
    if 'searchCode' in request.GET:
        searchCode = request.GET['searchCode']
    else:
        searchCode = 'A'  
    
    if 'searchDeptName' in request.GET:
        searchDeptName = request.GET['searchDeptName']
        print('[VIEW][INPUT] searchDeptName ', searchDeptName)
    else:
        searchDeptName = ''  

    if 'searchUserName' in request.GET:
        searchUserName = request.GET['searchUserName']
        print('[VIEW][INPUT] searchUserName ', searchUserName)
    else:
        searchUserName = ''  
        
    if 'manage_token_id' in request.GET:
        manage_token_id = request.GET['manage_token_id']
        print('[VIEW][INPUT] manage_token_id ', manage_token_id)
    else : 
        manage_token_id = 0
        
    if 'company_id' in request.GET:
        company_id = request.GET['company_id']
    else:
        company_id = '20'  
    print('[VIEW][INPUT] company_id ', company_id)

    #--------------
    # 토큰기준
    #--------------
    today = datetime.now().strftime('%Y%m%d')
    baiscManageTokens = ManageTokens.objects.filter(
        Q(start_date__lte=today) & Q(end_date__gte=today)
    ).first()

    #-------------
    # 토큰발행여부 검증
    #-------------
    if not baiscManageTokens:
        print("### 토큰 정상필요")
        
        baiscManageTokens = ManageTokens.objects.filter(
            is_active='Y'
        ).order_by('-end_date').first()
        
        #error = "[안내] 관리자에게 문의 요청 드립니다. 발행된 토큰이 없습니다"
        #return render(request, 'page_error.html', {'error': error})
    
    print('### baiscManageTokens.id', baiscManageTokens.id)
    
    if int(baiscManageTokens.id) == int(manage_token_id):
        manage_token_id = 0
        print('### chg manage_token_id', manage_token_id)
    
    if manage_token_id == 0:
        selectManageTokens = ManageTokens.objects.filter(
            Q(start_date__lte=today) & Q(end_date__gte=today),
            is_active = 'Y'
        ).first()
        
        if not selectManageTokens:
            print("### 토큰 정상필요 selectManageTokens")
            
            selectManageTokens = ManageTokens.objects.filter(
                is_active='Y'
            ).order_by('-end_date').first()
    else:
        selectManageTokens = ManageTokens.objects.filter(
            id=manage_token_id, is_active = 'Y'
        ).first()
        

    subquery_prev = ManageTokens.objects.filter(
        id__lt=selectManageTokens.id,
        is_active = 'Y'
    ).order_by('-id').first()

    subquery_next = ManageTokens.objects.filter(
        id__gt=selectManageTokens.id,
        is_active = 'Y'
    ).order_by('id').first()

    if subquery_prev:
        token_prev = subquery_prev.id
    else:
        token_prev = 0

    if subquery_next:
        token_next = subquery_next.id
    else:
        token_next = 0

    # print('### [VIEW][LOG] selectManageTokens id ', selectManageTokens.id)
    # print('### [VIEW][LOG] selectManageTokens token_prev ', token_prev)
    # print('### [VIEW][LOG] selectManageTokens token_next ', token_next)
    # print('### [VIEW][LOG] searchUserName ', searchUserName)
    # print('### [VIEW][LOG] searchDeptName ', searchDeptName)
    # print('### [VIEW][LOG] searchCode     ', searchCode)
    
    if searchCode == "B":
        token_Count = 1
    else:
        token_Count = -1
    
    #----------
    # 토큰정보
    #----------
    
    selectUserTokens = UserTokens.objects.filter(
            is_active='Y',
            token_id=selectManageTokens.id,
            received_tokens__gt=token_Count,  # 이상으로 조건 변경
            user__is_active=True,
            user__department_name__icontains=searchDeptName,
            user__employee_name__icontains=searchUserName,
            user__company_id = company_id
        ).select_related('user').order_by('-received_tokens')
    
    # 특수문자 개선
    for post in selectUserTokens:
        
        #print('### post.my_story_book', post.my_story_book)       
        if post.my_story_book is not None:
            post.my_story_book = post.my_story_book.replace(r'\r\n', '<br>')
            post.my_story_book = post.my_story_book.replace('\r\n', '<br>')
            post.my_story_book = post.my_story_book.replace('\r\n', '<br>')
            post.my_story_book = post.my_story_book.replace('\r', '<br>')
            post.my_story_book = post.my_story_book.replace('\n', '<br>')
            
            post.my_story_book = post.my_story_book.replace("'", "")
            post.my_story_book = post.my_story_book.replace(",", "")
            post.my_story_book = post.my_story_book.replace('"', "")         
            #print('### post.my_story_book after' , post.my_story_book)
        
    # 출력부 SET
    paginator = Paginator(selectUserTokens, 100)     
    page = request.GET.get('page')
    posts = paginator.get_page(page)
        
    #-------------
    # 2. 부서정보 업무로직
    #-------------   
    
    subquery = UserTokens.objects.filter(
        token_id=selectManageTokens.id,
        is_active='Y',
        user__company_id=company_id
    ).annotate(
        #user_id=F('user__id'),
        #chg_date=F('chg_date'),
        employee_id=F('user__employee_id'),
        employee_name=F('user__employee_name'),
        company_id=F('user__company_id'),
        company_name=F('user__company_name'),
        department_name=F('user__department_name'),
        position_name=F('user__position_name'),
        user_image_yn=F('user__image_yn'),
        user_image=F('user__image'),
        recev_point=ExpressionWrapper(F('received_tokens') * 1, output_field=fields.IntegerField()),
        send_point=ExpressionWrapper(F('my_send_tokens') * 1, output_field=fields.IntegerField()) # 2024.3.4부터 보낸 포인트 *2 > *1 
    ).values(
        'user_id', 'chg_date', 'employee_id', 'employee_name', 'company_id', 'company_name', 'department_name','position_name', 'user_image_yn', 'user_image','recev_point', 'send_point'
    )

    selectDeptPraise = subquery.annotate(
        tot_point=ExpressionWrapper(F('recev_point') + F('send_point'), output_field=fields.IntegerField())
    ).order_by('-tot_point', 'chg_date').values(
        'user_id', 'chg_date', 'employee_id', 'employee_name', 'company_id', 'company_name', 'department_name','position_name', 'user_image_yn', 'user_image', 'recev_point', 'send_point','tot_point'
    )
		
		# 출력부 SET
    paginatorDept = Paginator(selectDeptPraise, 10)
    pageDept = request.GET.get('pageDept')
    postDept = paginatorDept.get_page(pageDept)
            
    return render(request, 'manage/manageMember.html', {'posts':posts, 'manageToken':selectManageTokens, 'searchDeptName':searchDeptName, 'searchUserName':searchUserName, 'searchCode':searchCode, 'postDept':postDept, 'company_id':company_id, 'token_prev':token_prev,'token_next':token_next })
      
      
@login_required(login_url='/accounts/signin/')
def manageRank(request):
    print("### [VIEW] manageRank ####################################################")
        
    ##########################
    # POST 수신시
    ##########################
    if request.method == 'POST':
        for key, value in request.POST.items():
            print(key, value)            

    ##########################
    # GET 수신시
    ##########################
    if 'searchPeerNo' in request.GET:
        searchPeerNo = request.GET['searchPeerNo']
    else:
        searchPeerNo = ''  
        
    if 'manage_token_id' in request.GET:
        manage_token_id = request.GET['manage_token_id']
        print('[VIEW][INPUT] manage_token_id ', manage_token_id)
    else : 
        manage_token_id = 0
        
    if 'company_id' in request.GET:
        company_id = request.GET['company_id']
    else:
        company_id = '20'  
    print('[VIEW][INPUT] company_id ', company_id)

    #--------------
    # 토큰기준
    #--------------
    today = datetime.now().strftime('%Y%m%d')
    baiscManageTokens = ManageTokens.objects.filter(
        Q(start_date__lte=today) & Q(end_date__gte=today)
    ).first()

    #-------------
    # 토큰발행여부 검증
    #-------------
    if not baiscManageTokens:
        print("### 토큰 정상필요")
        
        baiscManageTokens = ManageTokens.objects.filter(
            is_active='Y'
        ).order_by('-end_date').first()
        
        #error = "[안내] 관리자에게 문의 요청 드립니다. 발행된 토큰이 없습니다"
        #return render(request, 'page_error.html', {'error': error})
    
    print('### baiscManageTokens.id', baiscManageTokens.id)
    
    if int(baiscManageTokens.id) == int(manage_token_id):
        manage_token_id = 0
        print('### chg manage_token_id', manage_token_id)
    
    if manage_token_id == 0:
        selectManageTokens = ManageTokens.objects.filter(
            Q(start_date__lte=today) & Q(end_date__gte=today),
            is_active = 'Y'
        ).first()
        
        if not selectManageTokens:
            print("### 토큰 정상필요 selectManageTokens")
            
            selectManageTokens = ManageTokens.objects.filter(
                is_active='Y'
            ).order_by('-end_date').first()
    else:
        selectManageTokens = ManageTokens.objects.filter(
            id=manage_token_id, is_active = 'Y'
        ).first()
        

    subquery_prev = ManageTokens.objects.filter(
        id__lt=selectManageTokens.id,
        is_active = 'Y'
    ).order_by('-id').first()

    subquery_next = ManageTokens.objects.filter(
        id__gt=selectManageTokens.id,
        is_active = 'Y'
    ).order_by('id').first()

    if subquery_prev:
        token_prev = subquery_prev.id
    else:
        token_prev = 0

    if subquery_next:
        token_next = subquery_next.id
    else:
        token_next = 0

    print('### [VIEW][LOG] selectManageTokens id ', selectManageTokens.id)
    print('### [VIEW][LOG] selectManageTokens token_prev ', token_prev)
    print('### [VIEW][LOG] selectManageTokens token_next ', token_next)
    print('### [VIEW][LOG] searchPeerNo ', searchPeerNo)
    
    #-------------
    # 부서정보 업무로직
    #-------------   
    
    peer_no = ''
    dept_names = ''
    
    # 우리은행 경우,Peer 기준으로 조회
    if company_id == "20" :    

        if searchPeerNo == '99' :
          
            print("### [VIEW][LOG] 우리은행 searchPeerNo",searchPeerNo)

            # 초기화
            combined_result = None
            for searchPeerNo in range(1, 39):
                #print('### [VIEW] searchPeerNo',searchPeerNo)
                selectManageDept = ManageDept.objects.filter(is_active='Y', company_id=company_id, peer_no=str(searchPeerNo))
                dept_ids = [dept.dept_id for dept in selectManageDept]

                subquery = UserTokens.objects.filter(
                    token_id=selectManageTokens.id,
                    is_active='Y',
                    user__company_id=company_id,
                    user__department_id__in=dept_ids
                ).annotate(
                    searchPeerNo=Value(str(searchPeerNo), output_field=CharField()),  # searchPeerNo 값을 추가
                    employee_id=F('user__employee_id'),
                    employee_name=F('user__employee_name'),
                    company_id=F('user__company_id'),
                    company_name=F('user__company_name'),
                    department_name=F('user__department_name'),
                    position_name=F('user__position_name'),
                    user_image_yn=F('user__image_yn'),
                    user_image=F('user__image'),
                    recev_point=ExpressionWrapper(F('received_tokens') * 1, output_field=fields.IntegerField()),
                    send_point=ExpressionWrapper(F('my_send_tokens') * 1, output_field=fields.IntegerField())  # 2024.3.4부터 보낸 포인트 *2 > *1 
                ).values(
                    'searchPeerNo', 'user_id', 'chg_date', 'employee_id', 'employee_name', 'company_id',
                    'company_name', 'department_name','position_name', 'user_image_yn', 'user_image',
                    'recev_point', 'send_point'
                )

                selectDeptPraise = subquery.annotate(
                    tot_point=ExpressionWrapper(F('recev_point') + F('send_point'), output_field=fields.IntegerField())
                ).order_by('-tot_point', 'chg_date').annotate(
                    rownum=Window(expression=RowNumber(), order_by=[F('tot_point').desc(), 'chg_date'])
                ).values(
                    'searchPeerNo', 'rownum', 'user_id', 'chg_date', 'employee_id', 'employee_name', 'company_id',
                    'company_name', 'department_name','position_name', 'user_image_yn', 'user_image',
                    'recev_point', 'send_point','tot_point'
                )

                if combined_result is None:
                    combined_result = selectDeptPraise
                else:
                    combined_result = combined_result.union(selectDeptPraise)

            # 최종 결과
            final_result = combined_result.order_by('searchPeerNo', 'rownum').values(
                'searchPeerNo', 'rownum', 'user_id', 'chg_date', 'employee_id', 'employee_name', 'company_id',
                'company_name', 'department_name', 'position_name', 'user_image_yn', 'user_image',
                'recev_point', 'send_point', 'tot_point'
            )
            
            selectDeptPraise = final_result
            searchPeerNo     = ''
          
        else :
            print("### [VIEW][LOG] 우리은행 searchPeerNo",searchPeerNo)
    
            selectManageDept = ManageDept.objects.filter(is_active='Y', company_id=company_id, peer_no=searchPeerNo)
            
            #for dept in selectManageDept:
            #    print('selectManageDept :', dept.dept_id, dept.dept_name, dept.peer_no)    
        
            dept_ids = [dept.dept_id for dept in selectManageDept]
            dept_names = [dept.dept_name for dept in selectManageDept]
            
            #print('dept_ids', dept_ids)
            
            subquery = UserTokens.objects.filter(
                token_id=selectManageTokens.id,
                is_active='Y',
                user__company_id=company_id,
                user__department_id__in=dept_ids
            ).annotate(
                searchPeerNo=Value(str(searchPeerNo), output_field=CharField()),  # searchPeerNo 값을 추가
                #user_id=F('user__id'),
                #chg_date=F('chg_date'),
                employee_id=F('user__employee_id'),
                employee_name=F('user__employee_name'),
                company_id=F('user__company_id'),
                company_name=F('user__company_name'),
                department_name=F('user__department_name'),
                position_name=F('user__position_name'),
                user_image_yn=F('user__image_yn'),
                user_image=F('user__image'),
                recev_point=ExpressionWrapper(F('received_tokens') * 1, output_field=fields.IntegerField()),
                send_point=ExpressionWrapper(F('my_send_tokens') * 1, output_field=fields.IntegerField()) # 2024.3.4부터 보낸 포인트 *2 > *1 
            ).values(
                'searchPeerNo', 'user_id', 'chg_date', 'employee_id', 'employee_name', 'company_id', 'company_name', 'department_name','position_name', 'user_image_yn', 'user_image','recev_point', 'send_point'
            )

            selectDeptPraise = subquery.annotate(
                tot_point=ExpressionWrapper(F('recev_point') + F('send_point'), output_field=fields.IntegerField())
            ).order_by('-tot_point', 'chg_date').annotate(
                rownum=Window(expression=RowNumber(), order_by=[F('tot_point').desc(), 'chg_date'])
            ).values(
                'searchPeerNo', 'rownum' ,'user_id', 'chg_date', 'employee_id', 'employee_name', 'company_id', 'company_name', 'department_name','position_name', 'user_image_yn', 'user_image', 'recev_point', 'send_point','tot_point'
            )
        
    
    else :     
    
        subquery = UserTokens.objects.filter(
            token_id=selectManageTokens.id,
            is_active='Y',
            user__company_id=company_id
        ).annotate(
            searchPeerNo=Value(str(''), output_field=CharField()),  # searchPeerNo 값을 추가
            #user_id=F('user__id'),
            #chg_date=F('chg_date'),
            employee_id=F('user__employee_id'),
            employee_name=F('user__employee_name'),
            company_id=F('user__company_id'),
            company_name=F('user__company_name'),
            department_name=F('user__department_name'),
            position_name=F('user__position_name'),
            user_image_yn=F('user__image_yn'),
            user_image=F('user__image'),
            recev_point=ExpressionWrapper(F('received_tokens') * 1, output_field=fields.IntegerField()),
            send_point=ExpressionWrapper(F('my_send_tokens') * 1, output_field=fields.IntegerField()) # 2024.3.4부터 보낸 포인트 *2 > *1 
        ).values(
            'searchPeerNo', 'user_id', 'chg_date', 'employee_id', 'employee_name', 'company_id', 'company_name', 'department_name','position_name', 'user_image_yn', 'user_image','recev_point', 'send_point'
        )

        selectDeptPraise = subquery.annotate(
            tot_point=ExpressionWrapper(F('recev_point') + F('send_point'), output_field=fields.IntegerField())
        ).order_by('-tot_point', 'chg_date').annotate(
            rownum=Window(expression=RowNumber(), order_by=[F('tot_point').desc(), 'chg_date'])
        ).values(
            'searchPeerNo', 'rownum','user_id', 'chg_date', 'employee_id', 'employee_name', 'company_id', 'company_name', 'department_name','position_name', 'user_image_yn', 'user_image', 'recev_point', 'send_point','tot_point'
        )
		
		# 출력부 SET
    paginatorDept = Paginator(selectDeptPraise, 10)
    pageDept = request.GET.get('pageDept')
    postDept = paginatorDept.get_page(pageDept)
            
    return render(request, 'manage/manageRank.html', {'dept_names':dept_names, 'manageToken':selectManageTokens, 'searchPeerNo':searchPeerNo, 'postDept':postDept, 'company_id':company_id, 'token_prev':token_prev,'token_next':token_next })

@login_required(login_url='/accounts/signin/')
def manageSingup(request):
    print("### [VIEW] manageSingup ####################################################")
    
    #-------------
    # 사용자 검증
    #-------------
    if request.user.is_superuser :
        print("### 관리자 접속")
    else :
        print("### 사용자 접속")
        error = "[101] 관리자 외 접속 불가합니다."
        return render(request, 'page_error.html', {'error': error})  
    
    ##########################
    # POST 수신시
    ##########################
    if request.method == 'POST':
        print('### [VIEW][LOG] POST ')
        
    ##########################
    # GET 수신시
    ##########################
    if 'searchDeptName' in request.GET:
        searchDeptName = request.GET['searchDeptName']
    else:
        searchDeptName = ''  

    if 'searchUserName' in request.GET:
        searchUserName = request.GET['searchUserName']
    else:
        searchUserName = ''  
        
    if 'searchCode' in request.GET:
        searchCode = request.GET['searchCode']
    else:
        searchCode = '1'  
    print('[VIEW][INPUT] searchCode ', searchCode)


    if 'company_id' in request.GET:
        company_id = request.GET['company_id']
    else:
        company_id = '20'  
    print('[VIEW][INPUT] company_id ', company_id)
    
        
    print('### [VIEW][LOG] GET ', searchDeptName)
    
    #-------------
    # 1. 회원정보 업무로직
    #-------------        
    selectUser = User2.objects.filter(
                    is_active=True,
                    department_name__icontains=searchDeptName,
                    employee_name__icontains=searchUserName,
                    company_id  = company_id,
                    ty          = searchCode
                ).order_by('-date_joined')
        
    # 출력부 SET
    paginator = Paginator(selectUser, 100)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
    
    #-------------
    # 2. 부서정보 업무로직
    #-------------   
    selectCompany = User2.objects.filter(
                    is_active=True,
                    ty=True,
                    company_name__isnull=False,
                    company_id__isnull=False,
                ).values('company_id', 'company_name').annotate(count=Count('id'))


    # 출력부 SET
    paginator = Paginator(selectCompany, 20)
    page = request.GET.get('page')
    companyInfo = paginator.get_page(page)
    
    
    return render(request, 'manage/manageSingup.html', {'posts':posts,'companyInfo':companyInfo,'searchDeptName':searchDeptName, 'searchUserName':searchUserName,'company_id':company_id,'searchCode':searchCode })

@login_required(login_url='/accounts/signin/')
def manageDepartment(request):
    print("### [VIEW] manageDepartment ####################################################")
    
    #-------------
    # 사용자 검증
    #-------------
    if request.user.is_superuser :
        print("### 관리자 접속")
    else :
        print("### 사용자 접속")
        error = "[101] 관리자 외 접속 불가합니다."
        return render(request, 'page_error.html', {'error': error})  
    
    ##########################
    # POST 수신시
    ##########################
    if request.method == 'POST':
        print('### [VIEW][LOG] POST ')
        
    ##########################
    # GET 수신시
    ##########################
    if 'searchDeptName' in request.GET:
        searchDeptName = request.GET['searchDeptName']
    else:
        searchDeptName = ''  

    if 'searchPeerNumber' in request.GET:
        searchPeerNumber = request.GET['searchPeerNumber']
    else:
        searchPeerNumber = ''  
    print('[VIEW][INPUT] searchPeerNumber ', searchPeerNumber)

    if 'company_id' in request.GET:
        company_id = request.GET['company_id']
    else:
        company_id = '20'  
    print('[VIEW][INPUT] company_id ', company_id)
    
        
    print('### [VIEW][LOG] GET ', searchDeptName)
    
    #-------------
    # 1. 회원정보 업무로직
    #-------------        
    selectManageDept = ManageDept.objects.filter(
        is_active='Y',
        dept_name__icontains=searchDeptName,
        company_id=company_id
    )

    if searchPeerNumber:
        selectManageDept = selectManageDept.filter(peer_no__icontains=searchPeerNumber)

        
    # 출력부 SET
    paginator = Paginator(selectManageDept, 10)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
        
    
    return render(request, 'manage/manageDepartment.html', {'posts':posts,'searchDeptName':searchDeptName,'company_id':company_id,'searchPeerNumber':searchPeerNumber })

@login_required(login_url='/accounts/signin/')
def managePosition(request):
    print("### [VIEW] managePosition ####################################################")
    
    #-------------
    # 사용자 검증
    #-------------
    if request.user.is_superuser :
        print("### 관리자 접속")
    else :
        print("### 사용자 접속")
        error = "[101] 관리자 외 접속 불가합니다."
        return render(request, 'page_error.html', {'error': error})  
    
    ##########################
    # POST 수신시
    ##########################
    if request.method == 'POST':
        print('### [VIEW][LOG] POST ')
        
    ##########################
    # GET 수신시
    ##########################
    if 'searchPosiName' in request.GET:
        searchPosiName = request.GET['searchPosiName']
    else:
        searchPosiName = ''  
    print('[VIEW][INPUT] searchPosiName ', searchPosiName)

    if 'company_id' in request.GET:
        company_id = request.GET['company_id']
    else:
        company_id = '20'  
    print('[VIEW][INPUT] company_id ', company_id)
    
       
    if 'searchRewardYn' in request.GET: 
        searchRewardYn = request.GET['searchRewardYn']
    else:
        searchRewardYn = ''  
    print('[VIEW][INPUT] searchRewardYn ', searchRewardYn)
            
    #-------------
    # 1. 회원정보 업무로직
    #-------------        
    selectManagePosi = ManagePosi.objects.filter(
                    is_active='Y',
                    posi_name__icontains=searchPosiName,
                    reward_skip_yn__icontains=searchRewardYn,
                    company_id  = company_id,
                ).order_by('posi_name')
        
    # 출력부 SET
    paginator = Paginator(selectManagePosi, 10)
    page = request.GET.get('page')
    posts = paginator.get_page(page)
        
    
    return render(request, 'manage/managePosition.html', {'posts':posts,'searchPosiName':searchPosiName,'company_id':company_id, 'searchRewardYn':searchRewardYn })

@login_required(login_url='/accounts/signin/')
@measure_execution_time
def thankyouList_new(request):
    # ==========================
    # 2024-12-25 refactor and add new functions of home, search, tk_list, rankList
    # ==========================

    """
    View function for handling the thank you list page.
    Displays praise interactions between users.
    """

    if request.user.id != 15893:
        one_month_ago = timezone.now() - timedelta(days=31)
        uc_messages = get_unprocessed_messages(request.user.username, one_month_ago)
        
        if uc_messages.exists():
            for message in uc_messages:
                try:
                    process_single_message(message, request)
                except Exception as e:
                    print(f"Error processing message {message.id}: {str(e)}")
                    return render(request, 'tk_list.html', {
                        'info': {'error': "[403] UC메신저 데이터 저장시 오류가 발생 했습니다."}
                    })
    
    # # Get compliment IDs for the current user
    # compliment_ids = select_my_list(request.user.id)

    # # Get user praise data
    # processed_queryset = get_user_praise_queryset(compliment_ids, request.user.id)

    # # Get user images
    # user_images = get_user_images()
    
    # Render the template with the processed data
    return render(request, 'tk_list.html', {
        # 'posts': processed_queryset,
        # 'images': user_images,
        'addPage': 'Y'
    })

#2024.02 My땡큐 마이땡큐
@login_required(login_url='/accounts/signin/')
@measure_execution_time
def thankyouList(request):
    print("### [VIEW] tk_list thankyouList ####################################################")
    # print("### [user.id] tk_list request.user.id : ", request.user.id)

    ###################################
    # 2024-02-26 떙큐리스트 개발
    ###################################
    if request.user.id != 15893:

        one_month_ago = timezone.now() - timedelta(days=31)

        your_ucmessages = BefInsUcmsg.objects.filter(
                            (Q(send_username= request.user.username) | Q(recv_username=request.user.username))
                            , insert_yn='N' # insert_yn 필드 값이 'Y'가 아닌 경우
                            , send_time__gte=one_month_ago
                        )

        if your_ucmessages.exists():

            for ucmessage in your_ucmessages:

                        receiver = User2.objects.filter(username=ucmessage.recv_username)
                        sender = User2.objects.filter(username=ucmessage.send_username)
                        
                        if receiver.exists() and sender.exists():
                            print("*************************** send_username과 recv_username 둘 다 있음")
                            send_user = sender.first()
                            recv_user = receiver.first()

                            try:
                                #------------------------------------
                                # 칭찬 insert
                                #------------------------------------
                                insertUserPraise = UserPraise()
                                
                                insertUserPraise.praise_id        = recv_user.id # 칭찬 받는 직원
                                insertUserPraise.user_id          = send_user.id # 칭찬한 직원
                                insertUserPraise.compliment_type  = '1'
                                
                                
                                #MY땡큐 UC칭찬
                                if ucmessage.images_id != '' and ucmessage.images_id != 'null'  :
                                        insertUserPraise.images_id        = ucmessage.images_id
                                else : 
                                        insertUserPraise.images_id        = '428'
                                
                                if ucmessage.send_content != '' and ucmessage.send_content != 'null' and ucmessage.send_content != None  :
                                    #chgageContents = re.sub('<\/?p[^>]*>', '', request.POST['input_Contents'])
                                    insertUserPraise.content          = ucmessage.send_content
                                    insertUserPraise.org_content      = ucmessage.send_content
                                    insertUserPraise.short_content    = ucmessage.send_content[:100]
                                else:
                                    insertUserPraise.content          = '감사합니다.'
                                    insertUserPraise.org_content      = '감사합니다.'
                                    insertUserPraise.short_content    = '감사합니다.'

                                insertUserPraise.tag              = {'tag': ['감사','칭찬','UC']}
                                insertUserPraise.emotion_ratio    = '' # open ai 응답
                                
                                insertUserPraise.view_count       = 0
                                insertUserPraise.comment_count    = 0
                                insertUserPraise.likes_count      = 0

                                insertUserPraise.is_senduc        = 'Y'
                                
                                
                                #----------
                                # 토큰정보
                                #----------
                                msgtoday = ucmessage.send_time.strftime('%Y%m%d')
                                selectManageTokens = ManageTokens.objects.filter(
                                    Q(start_date__lte=msgtoday) & Q(end_date__gte=msgtoday)
                                ).first()
                                insertUserPraise.token_id      = selectManageTokens.id
                                
                                insertUserPraise.is_active = 'Y'
                                    
                                insertUserPraise.reg_date = ucmessage.send_time #datetime.now()   
                                
                                # print("### [VIEW][LOG] ucmessage insertUserPraise Save ==========")
                                insertUserPraise.save()
                                
                                # print('### [VIEW][LOG] ucmessage insertUserPraise.compliment_id   ', insertUserPraise.compliment_id)
                                
                                #------------------------------------
                                # 알림 insert - 칭찬대상 알림 / PUSH
                                #------------------------------------
                                pushId  = recv_user.id
                                title   = "땡큐토큰"
                                message = send_user.employee_name+ ' '+ send_user.position_name+"님이 칭찬글을 등록 했습니다."
                                url = "/thankyoutoken/praiseDetail/" + str(insertUserPraise.compliment_id)
                                #title   = "thankyoutokentest"
                                #message = "thankyoutokentest"

                                insertUserNotices = UserNotices()
                                insertUserNotices.user_id          = recv_user.id
                                insertUserNotices.send_id          = send_user.id
                                insertUserNotices.notice_type      = '1'
                                insertUserNotices.compliment_id    = insertUserPraise.compliment_id
                                insertUserNotices.comment_id       = 0 
                                insertUserNotices.check_yn         = 'N' 
                                insertUserNotices.push_yn          = 'N'
                                insertUserNotices.push_status      = ''
                                insertUserNotices.is_active        = 'Y'
                                insertUserNotices.reg_date         = datetime.now()                
                                insertUserNotices.save()
                                
                                # print('### [VIEW][LOG] ucmessage insertUserNotices.user_id   ', insertUserNotices.user_id)
                                                
                                #------------------------------------
                                # 토큰 insert & update
                                #------------------------------------
                                ##################################
                                # 등록자 토큰감소
                                ##################################

                                # 토큰정보
                                # msgtoday = ucmessage.send_time.strftime('%Y%m%d')
                                # selectManageTokens = ManageTokens.objects.filter(
                                #     Q(start_date__lte=msgtoday) & Q(end_date__gte=msgtoday)
                                # ).first()
                                
                                toeknYear    = selectManageTokens.year
                                toeknQuarter = selectManageTokens.quarter
                                toeknCount   = selectManageTokens.tokens
                                hightoeknCount   = selectManageTokens.high_tokens

                                # 소속장여부 확인
                                # print('### send_user.company_id ', send_user.company_id)
                                # print('### send_user.position_id ', send_user.position_id)
                                selectuserReward = ManagePosi.objects.filter(
                                    is_active  = 'Y',
                                    company_id = send_user.company_id,
                                    posi_id    = send_user.position_id
                                ).first()

                                # print('### ******* user ucmessage selectuserReward', selectuserReward)

                                if selectuserReward:
                                    # print('### user ucmessage selectuserReward', selectuserReward.reward_skip_yn)
                                    if selectuserReward.reward_skip_yn == "Y" :
                                        user_reward_skip_yn = "Y"
                                    else :
                                        user_reward_skip_yn = "N"
                                else :
                                    user_reward_skip_yn = "N"
                                    # print('### else user ucmessage user_reward_skip_yn', user_reward_skip_yn)

                                # 보유토큰 조회
                                selectSendUserTokens = UserTokens.objects.filter(
                                    user_id=send_user.id,
                                    token_id = selectManageTokens.id,
                                    is_active='Y'
                                ).first()

                                selectSendUserTokensCount = UserTokens.objects.filter(
                                    user_id=send_user.id,
                                    token_id = selectManageTokens.id,
                                    is_active='Y'
                                ).count()

                                # UC메신저로도 칭찬 메시지가 있어서 순위에는 제외되도록
                                selectSameTotalCount = UserPraise.objects.filter(
                                        is_active='Y', 
                                        token_id = selectManageTokens.id,
                                        user_id = send_user.id,
                                        praise_id = recv_user.id,
                                    ).count()
                                
                                # print("$$$$$$ chk selectSameTotalCount : " , selectSameTotalCount)
                                # print("$$$$$$ chk send_user.id : " , send_user.id)
                                # print("$$$$$$ chk recv_user.id : " , recv_user.id)
                                # print("$$$$$$$$$$$$$$$$$$ @@@@@@@@@US insert chk selectUserTokens uc ucmessage.send_content : " , ucmessage.send_content)
                                # print("$$$$$$$$$$$$$$$$$$ US insert chk selectUserTokens 업로드여부 : " , selectSendUserTokens)

                                if selectSendUserTokensCount > 0:
                                    # 데이터가 존재하는 경우

                                    # selectThankyouWeeksYn이 None이면 >  땡큐주간 아닌경우 (.first() > None으로 분기처리)
                                    # if selectThankyouWeeksYn is None:
                                    # UC메신저를 통한 땡큐토큰 발송은 my_current_tokens에 연관도 없음
                                    #     selectUserTokens.my_current_tokens -= 1
                                    if selectSameTotalCount == 1 :
                                        selectSendUserTokens.my_send_tokens    += 1

                                    selectSendUserTokens.chg_date = datetime.now()      
                                    selectSendUserTokens.save()  # 업데이트 수행
                                    print('### [VIEW][LOG] my ucmessage selectUserTokens.user_id   ', selectSendUserTokens.user_id)
                                    
                                else:
                                    # 데이터가 존재하지 않는 경우
                                    print(" why why 왜!!!!!!!!!!!!!!! 보내는 아이디 chk send_user.id : " , send_user.id)
                                    print(" selectSendUserTokens : " ,selectSendUserTokens)
                                    
                                    insertSendUserTokens = UserTokens()
                                    insertSendUserTokens.user_id           = send_user.id
                                    insertSendUserTokens.token_id          = selectManageTokens.id
                                    insertSendUserTokens.year              = toeknYear
                                    insertSendUserTokens.quarter           = toeknQuarter
                                    
                                    #영업본부장님, 부행장들에게만 특정 수만큼 토큰 부여 2024.03.29
                                    chkInsTokYn = User2.objects.filter(
                                                        Q(position_name__contains='본부장') | Q(position_name__contains='부행장'),
                                                        ~Q(id=5256),
                                                        id=request.user.id,
                                                        company_id=20    
                                                    ).count()

                                    if request.user.id == 15893: #회장님
                                        insertSendUserTokens.my_tot_tokens = 100
                                    else :
                                        if chkInsTokYn > 0 :
                                            insertSendUserTokens.my_tot_tokens = 100
                                        else :
                                            if user_reward_skip_yn == "Y" :
                                                insertSendUserTokens.my_tot_tokens = hightoeknCount
                                            else : 
                                                insertSendUserTokens.my_tot_tokens = toeknCount
                                    
                                    insertSendUserTokens.my_current_tokens = insertSendUserTokens.my_tot_tokens
                                    # UC메신저로도 칭찬 메시지가 있어서 순위에는 제외되도록
                                    #UC 메신저로 보낸거 포인트에 넣어야 하나?
                                    if selectSameTotalCount == 1 :
                                        insertSendUserTokens.my_send_tokens    = 1
                                    else :
                                        insertSendUserTokens.my_send_tokens    = 0

                                    insertSendUserTokens.received_tokens   = 0
                                    insertSendUserTokens.is_active         = 'Y'
                                    insertSendUserTokens.reg_date          = datetime.now()                
                                    insertSendUserTokens.save()
                                    # print('### [VIEW][LOG] ucmessage my insertUserTokens.my_tot_tokens   ', insertUserTokens.my_tot_tokens)
                                    # print('### [VIEW][LOG] ucmessage my insertUserTokens.user_id   ', insertUserTokens.user_id)
                                
                                
                                ###################################
                                # 칭찬대상 토큰증가
                                ###################################
                                selectRecvUserTokens = UserTokens.objects.filter(
                                    user_id=recv_user.id,
                                    token_id = selectManageTokens.id,
                                    is_active='Y'
                                ).first()

                                # print("$$$$$$ 보내는 아이디 chk send_user.id : " , send_user.id)
                                # print("$$$$$$ 받는 아이디 chk recv_user.id : " , recv_user.id)
                                # print("$$$$$$$$$$$$$$$$$$ @@@@@@@@@US 칭찬대상 토큰증가uc ucmessage.send_content : " , ucmessage.send_content)
                                # print("$$$$$$$$$$$$$$$$$$ 받는 사람 토큰테이블에 기존 값이 있는지 ?  : " , selectRecvUserTokens)
                                
                                if selectRecvUserTokens:
                                    # 데이터가 존재하는 경우
                                    if selectSameTotalCount == 1 :
                                        selectRecvUserTokens.received_tokens += 1
                                    
                                    selectRecvUserTokens.chg_date = datetime.now()      
                                    selectRecvUserTokens.save()  # 업데이트 수행
                                    print('### [VIEW][LOG] ucmessage you selectRecvUserTokens.user_id   ', selectRecvUserTokens.user_id)
                                    
                                else:
                                    # 데이터가 존재하지 않는 경우
                                    insertRecvUserTokens = UserTokens()
                                    insertRecvUserTokens.user_id           = recv_user.id
                                    insertRecvUserTokens.token_id          = selectManageTokens.id
                                    insertRecvUserTokens.year              = toeknYear
                                    insertRecvUserTokens.quarter           = toeknQuarter
                                    
                                    #영업본부장님, 부행장들에게만 특정 수만큼 토큰 부여 2024.04.09
                                    chkInsTokYn = User2.objects.filter(
                                                        Q(position_name__contains='본부장') | Q(position_name__contains='부행장'),
                                                        ~Q(id=5256),
                                                        id=insertRecvUserTokens.user_id,
                                                        company_id=20    
                                                    ).count()
                                    

                                    # 칭찬 받는 직원 소속장여부 확인 
                                    chkRecvUserInfo = User2.objects.get(id=insertRecvUserTokens.user_id)

                                    recvUserReward = ManagePosi.objects.filter(
                                        is_active  = 'Y',
                                        company_id = chkRecvUserInfo.company_id,
                                        posi_id    = chkRecvUserInfo.position_id
                                    ).first()
                                    
                                    
                                    if insertRecvUserTokens.user_id == '15893': #회장님
                                        insertRecvUserTokens.my_tot_tokens = 100
                                    else :
                                        if chkInsTokYn > 0 :
                                            insertRecvUserTokens.my_tot_tokens = 100
                                        else :
                                            if recvUserReward is not None and recvUserReward.reward_skip_yn == "Y" :
                                                insertRecvUserTokens.my_tot_tokens = hightoeknCount
                                            else : 
                                                insertRecvUserTokens.my_tot_tokens = toeknCount
                                            
                                    # insertRecvUserTokens.my_tot_tokens     = toeknCount
                                    
                                    insertRecvUserTokens.my_current_tokens = insertRecvUserTokens.my_tot_tokens

                                    insertRecvUserTokens.my_send_tokens    = 0

                                    if selectSameTotalCount == 1 :
                                        insertRecvUserTokens.received_tokens   = 1
                                    else :
                                        insertRecvUserTokens.received_tokens   = 0
                                    
                                    insertRecvUserTokens.is_active         = 'Y'
                                    insertRecvUserTokens.reg_date          = datetime.now()                
                                    insertRecvUserTokens.save()
                                    print('### [VIEW][LOG] ucmessage you insertRecvUserTokens.user_id   ', insertRecvUserTokens.user_id)
                                
                                
                                #---------------
                                # open AI Call
                                #---------------
                                

                                #----------------------------------------------------------------------------------------------------
                                # FINAL : 정상응답
                                #----------------------------------------------------------------------------------------------------
                                                        
                                # account_user_befinsucmsg 테이블에 Insert
                                print("MY땡큐 FINAL : 정상응답 ucmessage.id : ", ucmessage.id)
                                updateBefInsUcmsg = BefInsUcmsg.objects.get(id=ucmessage.id) 
                                updateBefInsUcmsg.insert_yn  = 'Y'
                                updateBefInsUcmsg.insert_time = datetime.now()
                                updateBefInsUcmsg.insertfail_reason = ''

                                updateBefInsUcmsg.save()

                                

                            
                            except:
                                
                                #-------------
                                # 오류내용 SET
                                #-------------
                                error = "[403] UC메신저 데이터 저장시 오류가 발생 했습니다."
                                info = {'error': error}
                                                    
                                return render(request, 'tk_list.html', {'info':info,})            
           
    
    # Subquery to get the notice count
    notice_count_subquery = UserNotices.objects.filter(
        user_id=request.user.id,
        send_id=OuterRef('user_id'),
        check_yn='N'
    ).values('user_id').annotate(notice_count=Count('notice_id')).values('notice_count')[:1]

    def selectMyList(user_id):

        if request.user.id == 15893:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT t1.list_id, MAX(t1.compliment_id) AS compliment_id
                    FROM (
                        SELECT compliment_id, user_id AS list_id, reg_date
                        FROM wbntt.account_user_praise
                        WHERE praise_id = %s AND is_active = 'Y' AND reg_date >= DATE_SUB(NOW(), INTERVAL 2 MONTH) 
                        UNION ALL
                        SELECT compliment_id, praise_id AS list_id, reg_date
                        FROM wbntt.account_user_praise
                        WHERE user_id = %s AND is_active = 'Y' AND reg_date >= DATE_SUB(NOW(), INTERVAL 2 MONTH)
                    ) AS t1
                    GROUP BY t1.list_id 
                """, [user_id, user_id])
                rows = cursor.fetchall()
                #for row in rows:
                #    print(row)
                
                # rows의 'compliment_id' 값을 list 변수에 넣는다고 가정합니다.
                compliment_ids = [row[1] for row in rows]
                #print('compliment_ids', compliment_ids)
                
                return compliment_ids
        
        else :
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT list_id, compliment_id
                        FROM (
                            SELECT list_id,
                                compliment_id,
                                ROW_NUMBER() OVER(PARTITION BY list_id ORDER BY reg_date DESC) AS rn
                            FROM (
                                SELECT user_id AS list_id, 
                                    compliment_id, 
                                    reg_date
                                FROM wbntt.account_user_praise
                                WHERE praise_id = %s AND is_active = 'Y' 
                                UNION ALL
                                SELECT praise_id AS list_id, 
                                    compliment_id, 
                                    reg_date
                                FROM wbntt.account_user_praise
                                WHERE user_id = %s AND is_active = 'Y' 
                            ) AS t1
                        ) AS t2
                        WHERE rn = 1
                """, [user_id, user_id])
                rows = cursor.fetchall()
                #for row in rows:
                #    print(row)
                
                # rows의 'compliment_id' 값을 list 변수에 넣는다고 가정합니다.
                compliment_ids = [row[1] for row in rows]
                #print('compliment_ids', compliment_ids)
                
                return compliment_ids

    
    #마이떙큐 리스트 대상조회    
    compliment_ids = selectMyList(request.user.id)
    # print('compliment_ids ', compliment_ids)
    

    # UserPraise 모델에 compliment_id 조건을 넣어서 쿼리셋을 가져옵니다.
    selectUserPraise = UserPraise.objects.filter(compliment_id__in=compliment_ids 
    ).select_related('praise', 'user').prefetch_related('images').annotate(
        praise_employee_name=F('praise__employee_name'),
        praise_employee_id=F('praise__employee_id'),
        praise_department_name=F('praise__department_name'),
        praise_position_name=F('praise__position_name'),
        praise_company_name=F('praise__company_name'),
        praise_image_yn=F('praise__image_yn'),
        praise_image=F('praise__image'),
        user_employee_name=F('user__employee_name'),
        user_employee_id=F('user__employee_id'),
        user_department_name=F('user__department_name'),
        user_position_name=F('user__position_name'),
        user_company_name=F('user__company_name'),
        user_image_yn=F('user__image_yn'),
        user_image=F('user__image'),
        image_path=F('images__image_path'),
        notice_count=Subquery(notice_count_subquery)
    ).order_by('-reg_date')
    
    # 등록자 정보 재할당
    for item in selectUserPraise:
        if item.user_id == request.user.id:
            # Swap variables
            item.praise_id, item.user_id = item.user_id, item.praise_id
            item.praise_employee_name, item.user_employee_name = item.user_employee_name, item.praise_employee_name
            item.praise_employee_id, item.user_employee_id = item.user_employee_id, item.praise_employee_id
            item.praise_department_name, item.user_department_name = item.user_department_name, item.praise_department_name
            item.praise_position_name, item.user_position_name = item.user_position_name, item.praise_position_name
            item.praise_company_name, item.user_company_name = item.user_company_name, item.praise_company_name
            item.praise_image_yn, item.user_image_yn = item.user_image_yn, item.praise_image_yn
            item.praise_image, item.user_image = item.user_image, item.praise_image

    
    # Paginate the queryset
    paginator = Paginator(selectUserPraise, 100)
    page = request.GET.get('page')
    posts = paginator.get_page(page)


    #-------------
    # 이미지 출력SET
    #-------------
    selectUserImages = UserImages.objects.filter(is_open='Y', is_active='Y').order_by('-reg_date')
    
    paginator = Paginator(selectUserImages, 100)
    page = request.GET.get('page')
    images = paginator.get_page(page)

    return render(request, 'tk_list.html',  {'posts':posts, 'images':images, 'addPage':'Y'})
    
 
@login_required(login_url='/accounts/signin/')
@measure_execution_time
def thankyouTalk(request):
    print("### [VIEW] tk_talk thankyouTalk ####################################################")
    user_info = None

    #-------------
    # 출력부 SET
    #-------------
    selectUserImages_All = UserImages.objects.filter(is_open='Y', is_active='Y').order_by('-reg_date')
    paginator0 = Paginator(selectUserImages_All, 100)
    page0 = request.GET.get('page0')
    posts_All = paginator0.get_page(page0)
    
    selectUserImages_1 = UserImages.objects.filter(card_code = '1', is_open='Y', is_active='Y').order_by('-reg_date')
    paginator1 = Paginator(selectUserImages_1, 100)
    page1 = request.GET.get('page1')
    posts_1 = paginator1.get_page(page1)
    
    selectUserImages_2 = UserImages.objects.filter(card_code = '2', is_open='Y', is_active='Y').order_by('-reg_date')
    paginator2 = Paginator(selectUserImages_2, 100)
    page2 = request.GET.get('page2')
    posts_2 = paginator2.get_page(page2)
    
    selectUserImages_3 = UserImages.objects.filter(card_code = '3', is_open='Y', is_active='Y').order_by('-reg_date')
    paginator3 = Paginator(selectUserImages_3, 100)
    page3 = request.GET.get('page3')
    posts_3 = paginator3.get_page(page3)
    
    selectUserImages_4 = UserImages.objects.filter(card_code = '4', is_open='Y', is_active='Y').order_by('-reg_date')
    paginator4 = Paginator(selectUserImages_4, 100)
    page4 = request.GET.get('page4')
    posts_4 = paginator4.get_page(page4)
    
    selectUserImages_5 = UserImages.objects.filter(card_code = '5', is_open='Y', is_active='Y').order_by('-reg_date')
    paginator5 = Paginator(selectUserImages_5, 100)
    page5 = request.GET.get('page5')
    posts_5 = paginator5.get_page(page5)

    selectUserImages_6 = UserImages.objects.filter(card_code = '6', is_open='Y', is_active='Y').order_by('-reg_date')
    paginator6 = Paginator(selectUserImages_6, 100)
    page6 = request.GET.get('page6')
    posts_6 = paginator6.get_page(page6) #2024.01.29 카드그룹관리 위비항목 추가

    selectUserImages_7 = UserImages.objects.filter(card_code = '7', is_open='Y', is_active='Y').order_by('-reg_date')
    paginator7 = Paginator(selectUserImages_7, 100)
    page7 = request.GET.get('page7')
    posts_7 = paginator7.get_page(page7) #2024.02.05 카드그룹관리 설날항목 추가
    
    if 'sendId' in request.GET:
        sendId = request.GET.get('sendId', None)
        print('user_id request.GET>> : ', sendId)
    
        from django.db.models import F, Q

        selectUserPraise = UserPraise.objects.filter(
            Q(Q(praise_id=request.user.id) & Q(user_id=sendId)) | Q(Q(praise_id=sendId) & Q(user_id=request.user.id)),
            is_active='Y',
        ).select_related('praise', 'user').prefetch_related('images').annotate(
            praise_employee_name=F('praise__employee_name'),
            praise_employee_id=F('praise__employee_id'),
            praise_department_name=F('praise__department_name'),
            praise_position_name=F('praise__position_name'),
            praise_company_name=F('praise__company_name'),
            praise_image_yn=F('praise__image_yn'),
            praise_image=F('praise__image'),
            user_employee_name=F('user__employee_name'),
            user_employee_id=F('user__employee_id'),
            user_department_name=F('user__department_name'),
            user_position_name=F('user__position_name'),
            user_company_name=F('user__company_name'),
            user_image_yn=F('user__image_yn'),
            user_image=F('user__image'),
            image_path=F('images__image_path'),
        ).order_by('reg_date')


        # Print the results
        # for row in selectUserPraise.values():
        #     print(row)


        # Paginate the queryset
        paginator = Paginator(selectUserPraise, 100)
        page = request.GET.get('page')
        posts = paginator.get_page(page)

        if len(posts) > 0:
            last_post = posts[-1]

            if last_post.praise_id == request.user.id:
                user_id = request.user.id
                user_record = User2.objects.filter(id=user_id).values('id', 'employee_name', 'company_name','department_name').first()

                if user_record:
                    user_id = user_record['id']
                    user_info = {'user_id': user_record['id'],
                            'employee_name': user_record['employee_name'],
                            'company_name': user_record['company_name'],
                            'department_name': user_record['department_name'],}

                    # 이제 user_id와 employee_name을 사용할 수 있음
                else:
                    # 해당 user_id에 대한 레코드가 없을 경우 처리
                    pass

                # 토큰가능건수 체크
                today = datetime.now().strftime('%Y%m%d')
                selectManageTokens = ManageTokens.objects.filter(
                    Q(start_date__lte=today) & Q(end_date__gte=today)
                ).first()

                toeknYear    = selectManageTokens.year
                toeknQuarter = selectManageTokens.quarter
                toeknCount   = selectManageTokens.tokens

                selectUserTokens = UserTokens.objects.filter(
                    user_id=request.user.id,
                    year=toeknYear,
                    quarter=toeknQuarter,
                    is_active='Y'
                ).first()
                
                if selectUserTokens is not None and selectUserTokens.my_current_tokens == 0:
                    #-------------
                    # 오류내용 SET
                    #-------------
                    error = "[300] 사용가능한 토큰건수가 없습니다."
                    info = {'error': error,
                            'praise_id': request.POST.get('input_employee_id', ''),
                            'content': request.POST.get('input_Contents', ''),
                            'input_active': request.POST.get('input_active', '')}

                else:
                    alarmChk = "get으로 접속 for 답장"
                    info = {'alarmChk': alarmChk }

        #-------------
        # 이미지 출력SET
        #-------------
        selectUserImages = UserImages.objects.filter(is_open='Y', is_active='Y').order_by('-reg_date')
        
        paginator = Paginator(selectUserImages, 100)
        page = request.GET.get('page')
        images = paginator.get_page(page)

    ##########################
    # POST 수신시
    # 2024-12-03 handle praise
    ##########################
    if request.method == 'POST':
        print(request.POST['input_employee_id'], request.user.id)
                
        #-------------
        # 입력부 SET
        #-------------
        for key, value in request.POST.items():
            print('### [VIEW][INPUT]', key, value)
                
        from django.db.models import F, Q

        # 토큰가능건수 체크
        today = datetime.now().strftime('%Y%m%d')
        selectManageTokens = ManageTokens.objects.filter(
            Q(start_date__lte=today) & Q(end_date__gte=today)
        ).first()

        toeknYear    = selectManageTokens.year
        toeknQuarter = selectManageTokens.quarter
        toeknCount   = selectManageTokens.tokens

        selectUserTokens = UserTokens.objects.filter(
            user_id=request.user.id,
            year=toeknYear,
            quarter=toeknQuarter,
            is_active='Y'
        ).first()
        
        if selectUserTokens is not None and selectUserTokens.my_current_tokens == 0:
            #-------------
            # 오류내용 SET
            #-------------
            error = "[300] 사용가능한 토큰건수가 없습니다."
            info = {'error': error,
                       'praise_id': request.POST.get('input_employee_id', ''),
                       'content': request.POST.get('input_Contents', ''),
                       'input_active': request.POST.get('input_active', '')}

            return render(request, 'tk_talk.html', {'info':info,'posts_All':posts_All,'posts_1':posts_1,'posts_2':posts_2,'posts_3':posts_3, 'posts_4':posts_4,'posts_5':posts_5,'posts_6':posts_6,'posts_7':posts_7, 'token':selectUserTokens, 'manage':selectManageTokens})
              
                
        if int(request.POST['input_employee_id']) == int(request.user.id):
            #-------------
            # 오류내용 SET
            #-------------
            error = "[301] 본인에게 칭찬등록 불가합니다."
            info = {'error': error,
                       'praise_id': request.POST.get('input_employee_id', ''),
                       'content': request.POST.get('input_Contents', ''),
                       'input_active': request.POST.get('input_active', '')}

            return render(request, 'tk_talk.html', {'info':info,'posts_All':posts_All,'posts_1':posts_1,'posts_2':posts_2,'posts_3':posts_3, 'posts_4':posts_4,'posts_5':posts_5,'posts_6':posts_6,'posts_7':posts_7, 'token':selectUserTokens, 'manage':selectManageTokens})
              
            
        # 소속장이상 여부체크    
        praise_user_id = request.POST['input_employee_id']
        selectPraiseUser = User2.objects.filter(
            id = praise_user_id
        ).first()
        #print('### praise_user_id', praise_user_id)
        
        selectPraiseManagePosi = ManagePosi.objects.filter(
            company_id=selectPraiseUser.company_id,
            posi_id=selectPraiseUser.position_id,
            is_active = 'Y'
        ).first()
        #print('### selectPraiseManagePosi', selectPraiseManagePosi.id)
        
        if selectPraiseManagePosi:
            print('### [API][LOG] selectPraiseManagePosi.reward_skip_yn',selectPraiseManagePosi.reward_skip_yn)
            
            #2023-12-14 소속장 이상허용
            if selectPraiseManagePosi.reward_skip_yn == '9999' :

                #-------------
                # 오류내용 SET
                #-------------
                error = "[302] 소속상이상은 칭찬등록 불가합니다."
                info = {'error': error,
                           'praise_id': request.POST.get('input_employee_id', ''),
                           'content': request.POST.get('input_Contents', ''),
                           'input_active': request.POST.get('input_active', '')}
                            
                return render(request, 'tk_talk.html', {'info':info,'posts_All':posts_All,'posts_1':posts_1,'posts_2':posts_2,'posts_3':posts_3, 'posts_4':posts_4,'posts_5':posts_5,'posts_6':posts_6,'posts_7':posts_7, 'token':selectUserTokens, 'manage':selectManageTokens})
              
                
            
        try:        
            if 'input_active' in request.POST and request.POST['input_swiper_id'] in ['0']:
                print("### [VIEW][LOG] inputCardImg Start ==========")
                
                # ----------------------------------
                # 파일 업로드 ddd 
                # request.FILES.get('inputCardImg'):
                # ----------------------------------
                
                for key, file in request.FILES.items():
                    print('### [VIEW][INPUT]', key, file)
                
                insertUserImages = UserImages()
                
                formFile = request.FILES['inputCardImg']
                today = date.today().strftime("%Y%m%d")
                now = datetime.now()
                time_string = now.strftime("%H%M%S")
                path = 'user_' + str(request.user.id) + '/' + today
                filename = time_string + '_' + formFile.name
                # 이미지 저장
                filePath = save_image(formFile, path, filename)
                
                # 파일 저장 후, 저장된 경로를 출력
                print("### [VIEW][LOG] filename", filename)
                print("### [VIEW][LOG] file url", filePath)

                # filePath = os.path.join(settings.MEDIA_URL, filename)
                fileYn   = 'Y'
                insertUserImages.image_path            = filePath

                #################################################
                # DB UPDATE
                #################################################
                insertUserImages.image_name    = 'UserImage'
                insertUserImages.is_open       = 'N'
                insertUserImages.is_active     = 'N'
                insertUserImages.reg_date      = datetime.now()
                
                print("### [VIEW][LOG] insertUserImages save ========== ")
                insertUserImages.save()
                
                print("### [VIEW][LOG] insertUserImages.id : ", insertUserImages.id)
                
                
                
        except:
            #-------------
            # 오류내용 SET
            #-------------
            error = "[400] 데이터 저장시 오류가 발생 했습니다."
            info = {'error': error,
                       'praise_id': request.POST.get('input_employee_id', ''),
                       'content': request.POST.get('input_Contents', ''),
                       'input_active': request.POST.get('input_active', '')}

            #-------------
            # 출력부 SET
            #-------------
            selectUserImages = UserImages.objects.filter(is_open='Y', is_active='Y').order_by('-reg_date')

            paginator = Paginator(selectUserImages, 100)
            page = request.GET.get('page')
            posts = paginator.get_page(page)

            return render(request, 'tk_talk.html', {'posts':posts, 'info':info,})
                
        # 등록자 사용가능한 토큰 개수 검증
        print("### [VIEW][LOG] insertUserPraise Start ==========")
        
        #-------------
        # 업무로직
        #-------------        
        if request.POST['input_Contents']:
            try:
                # ===================
                # 2024-12-24 fix point accumulation incorrect
                # ===================
                with transaction.atomic():

                    #------------------------------------
                    # 칭찬 insert
                    #------------------------------------
                    insertUserPraise = UserPraise()
                    
                    insertUserPraise.praise_id        = request.POST['input_employee_id']
                    insertUserPraise.user_id          = request.user.id
                    insertUserPraise.compliment_type  = '1'
                    
                    
                    #chgageContents = re.sub('<\/?p[^>]*>', '', request.POST['input_Contents'])
                    insertUserPraise.content          = request.POST['input_Contents']
                    
                    if 'input_active' in request.POST and request.POST['input_swiper_id'] in ['0']:
                        insertUserPraise.images_id        = insertUserImages.id
                    else : 
                        insertUserPraise.images_id        = request.POST['input_swiper_id']
                    
                    
                    insertUserPraise.org_content      = request.POST['input_Contents_text']
                    
                    insertUserPraise.short_content    = '' # open ai 응답
                    insertUserPraise.tag              = '' # open ai 응답
                    insertUserPraise.emotion_ratio    = '' # open ai 응답
                    
                    insertUserPraise.view_count       = 0
                    insertUserPraise.comment_count    = 0
                    insertUserPraise.likes_count      = 0
                    
                    insertUserPraise.is_senduc        =  'N'
                    
                    #----------
                    # 토큰정보
                    #----------
                    today = datetime.now().strftime('%Y%m%d')
                    selectManageTokens = ManageTokens.objects.filter(
                        Q(start_date__lte=today) & Q(end_date__gte=today)
                    ).first()
                    insertUserPraise.token_id      = selectManageTokens.id
                    
                    if 'input_active' in request.POST and request.POST['input_active'] in ['on', 'Y']:
                        insertUserPraise.is_active = 'Y'
                    else:
                        insertUserPraise.is_active = 'Y'
                        
                    insertUserPraise.reg_date = datetime.now()   
                    
                    print("### [VIEW][LOG] insertUserPraise Save ==========")
                    insertUserPraise.save()
                    
                    print('### [VIEW][LOG] insertUserPraise.compliment_id   ', insertUserPraise.compliment_id)
                    
                    
                    #------------------------------------
                    # 토큰 insert & update
                    #------------------------------------
                    ##################################
                    # 등록자 토큰감소
                    ##################################

                    # 토큰정보
                    today = datetime.now().strftime('%Y%m%d')
                    selectManageTokens = ManageTokens.objects.filter(
                        Q(start_date__lte=today) & Q(end_date__gte=today)
                    ).first()
                    
                    toeknYear    = selectManageTokens.year
                    toeknQuarter = selectManageTokens.quarter
                    toeknCount   = selectManageTokens.tokens
                    hightoeknCount   = selectManageTokens.high_tokens

                    # 소속장여부 확인
                    selectuserReward = ManagePosi.objects.filter(
                        is_active  = 'Y',
                        company_id = request.user.company_id,
                        posi_id    = request.user.position_id
                    ).first()

                    if selectuserReward:
                        print('### user selectuserReward', selectuserReward.reward_skip_yn)
                        if selectuserReward.reward_skip_yn == "Y" :
                            user_reward_skip_yn = "Y"
                        else :
                            user_reward_skip_yn = "N"
                    else :
                        user_reward_skip_yn = "N"

                    # 보유토큰 조회
                    selectUserTokens = UserTokens.objects.select_for_update().filter(
                        user_id=request.user.id,
                        year=toeknYear,
                        quarter=toeknQuarter,
                        is_active='Y'
                    ).first()

                    #땡큐주간에 칭찬 발송시 토큰 추가
                    current_date = datetime.now().strftime('%Y%m%d')
                    weekym = datetime.now().strftime('%Y%m')
                    selectThankyouWeeksYn = ManageThankyouWeeks.objects.filter(is_active='Y', weeks_ym = weekym, start_date__lte=current_date, end_date__gte = current_date).first()

                    #동일 직원 칭찬 여부 확인
                    selectSameTotalCount = UserPraise.objects.select_for_update().filter(
                        is_active='Y', 
                        token_id = selectManageTokens.id,
                        user_id = request.user.id,
                        praise_id = request.POST['input_employee_id'],
                    ).count()
                    
                    # print('$$$$$$$$$$$$ selectTotalCount praise_count', selectSameTotalCount )
                    # print('$$$$$$$$$$$$ selectUserTokens null', selectUserTokens )

                    if selectUserTokens:
                        # 데이터가 존재하는 경우

                        # selectThankyouWeeksYn이 None이면 >  땡큐주간 아닌경우 (.first() > None으로 분기처리)
                        if selectThankyouWeeksYn is None:
                            selectUserTokens.my_current_tokens -= 1

                        if selectSameTotalCount == 1 :
                            selectUserTokens.my_send_tokens    += 1

                        selectUserTokens.chg_date = datetime.now()      
                        selectUserTokens.save()  # 업데이트 수행
                        print('### [VIEW][LOG] my  selectUserTokens.user_id   ', selectUserTokens.user_id)
                        
                    else:
                        # 데이터가 존재하지 않는 경우
                        insertUserTokens = UserTokens()
                        insertUserTokens.user_id           = request.user.id
                        insertUserTokens.token_id          = selectManageTokens.id
                        insertUserTokens.year              = toeknYear
                        insertUserTokens.quarter           = toeknQuarter
                        
                        #영업본부장님, 부행장들에게만 특정 수만큼 토큰 부여 2024.03.29
                        chkInsTokYn = User2.objects.filter(
                                            Q(position_name__contains='본부장') | Q(position_name__contains='부행장'),
                                            ~Q(id=5256),
                                            id=request.user.id,
                                            company_id=20    
                                        ).count()

                        if request.user.id == 15893: #회장님
                            insertUserTokens.my_tot_tokens = 100
                        else :
                            if chkInsTokYn > 0 :
                                insertUserTokens.my_tot_tokens = 100
                            else :
                                if user_reward_skip_yn == "Y" :
                                    insertUserTokens.my_tot_tokens = hightoeknCount
                                else : 
                                    insertUserTokens.my_tot_tokens = toeknCount
                        
                        # selectThankyouWeeksYn이 not None이면 땡큐주간이여서 tokens데이터 생성시 감소가 없기 때문에 초기값 세팅 그 외에는 -1을 해준다 (.first() > None으로 분기처리)
                        if selectThankyouWeeksYn is not None:
                            insertUserTokens.my_current_tokens = insertUserTokens.my_tot_tokens
                        else :
                            insertUserTokens.my_current_tokens = insertUserTokens.my_tot_tokens  - 1
                        
                        if selectSameTotalCount == 1 :
                            insertUserTokens.my_send_tokens    = 1
                        else :
                            insertUserTokens.my_send_tokens    = 0

                        insertUserTokens.received_tokens   = 0
                        insertUserTokens.is_active         = 'Y'
                        insertUserTokens.reg_date          = datetime.now()                
                        insertUserTokens.save()
                        print('### [VIEW][LOG] my  insertUserTokens.my_tot_tokens   ', insertUserTokens.my_tot_tokens)
                        print('### [VIEW][LOG] my  insertUserTokens.user_id   ', insertUserTokens.user_id)
                    
                    ###################################
                    # 칭찬대상 토큰증가
                    ###################################
                    selectUserTokens = UserTokens.objects.select_for_update().filter(
                        user_id=request.POST['input_employee_id'],
                        year=toeknYear,
                        quarter=toeknQuarter,
                        is_active='Y'
                    ).first()
                    
                    # print("$$$$$$ check selectSameTotalCount : ", selectSameTotalCount)
                    # print("$$$$$$ check selectUserTokens : ", selectUserTokens)

                    if selectUserTokens:
                        # 데이터가 존재하는 경우
                        if selectSameTotalCount == 1 :
                            selectUserTokens.received_tokens += 1
                        selectUserTokens.chg_date = datetime.now()      
                        selectUserTokens.save()  # 업데이트 수행
                        print('### [VIEW][LOG] you selectUserTokens.user_id   ', selectUserTokens.user_id)
                        
                    else:
                        # 데이터가 존재하지 않는 경우
                        # print("$$$$$$ check 존재하지 않는 경우 selectUserTokens : ", selectUserTokens)
                        insertUserTokens = UserTokens()
                        insertUserTokens.user_id           = request.POST['input_employee_id']
                        insertUserTokens.token_id          = selectManageTokens.id
                        insertUserTokens.year              = toeknYear
                        insertUserTokens.quarter           = toeknQuarter
                        
                        #영업본부장님, 부행장들에게만 특정 수만큼 토큰 부여 2024.04.09
                        chkInsTokYn = User2.objects.filter(
                                            Q(position_name__contains='본부장') | Q(position_name__contains='부행장'),
                                            ~Q(id=5256),
                                            id=insertUserTokens.user_id,
                                            company_id=20    
                                        ).count()
                        

                        # 칭찬 받는 직원 소속장여부 확인 
                        chkRecvUserInfo = User2.objects.get(id=insertUserTokens.user_id)

                        recvUserReward = ManagePosi.objects.filter(
                            is_active  = 'Y',
                            company_id = chkRecvUserInfo.company_id,
                            posi_id    = chkRecvUserInfo.position_id
                        ).first()
                        
                        # print("$$$$$$ check 존재하지 않는 경우 recvUserReward : ", recvUserReward)

                        if insertUserTokens.user_id == '15893': #회장님
                            insertUserTokens.my_tot_tokens = 100
                        else :
                            if chkInsTokYn > 0 :
                                insertUserTokens.my_tot_tokens = 100
                            else :
                                if recvUserReward is not None and recvUserReward.reward_skip_yn == "Y" :
                                    insertUserTokens.my_tot_tokens = hightoeknCount
                                else : 
                                    insertUserTokens.my_tot_tokens = toeknCount
                                
                        # insertUserTokens.my_tot_tokens     = toeknCount
                        # print("$$$$$$ check insertUserTokens.my_tot_tokens : ", insertUserTokens.my_tot_tokens)
                        
                        insertUserTokens.my_current_tokens = insertUserTokens.my_tot_tokens
                        insertUserTokens.my_send_tokens    = 0
                        
                        if selectSameTotalCount == 1 :
                            insertUserTokens.received_tokens   = 1
                        else :
                            insertUserTokens.received_tokens   = 0
                        
                        insertUserTokens.is_active         = 'Y'
                        insertUserTokens.reg_date          = datetime.now()                
                        insertUserTokens.save()
                        print('### [VIEW][LOG] you insertUserTokens.user_id   ', insertUserTokens.user_id)
                    
                    
                    #------------------------------------
                    # 알림 insert - 칭찬대상 알림 / PUSH
                    #------------------------------------
                    pushId  = request.POST['input_employee_id']
                    title   = "땡큐토큰"
                    message = request.user.employee_name+ ' '+ request.user.position_name+"님이 칭찬글을 등록 했습니다."
                    url = "/thankyoutoken/praiseDetail/" + str(insertUserPraise.compliment_id)
                    #title   = "thankyoutokentest"
                    #message = "thankyoutokentest"
                    PushYN, PushStatus  = ChwPushCall(pushId,title,message,url)
                    
                    insertUserNotices = UserNotices()
                    insertUserNotices.user_id          = request.POST['input_employee_id']
                    insertUserNotices.send_id          = request.user.id
                    insertUserNotices.notice_type      = '1'
                    insertUserNotices.compliment_id    = insertUserPraise.compliment_id
                    insertUserNotices.comment_id       = 0 
                    insertUserNotices.check_yn         = 'N' 
                    insertUserNotices.push_yn          = PushYN
                    insertUserNotices.push_status      = PushStatus
                    insertUserNotices.is_active        = 'Y'
                    insertUserNotices.reg_date         = datetime.now()                
                    insertUserNotices.save()
                    
                    print('### [VIEW][LOG] insertUserNotices.user_id   ', insertUserNotices.user_id)
                                    
                    #---------------
                    # open AI Call
                    #---------------
                    inputData = request.POST['input_Contents_text']
                    
                    
                    try:
                        # 등록직원
                        selectUser1 = User2.objects.get(id=insertUserNotices.send_id)
                        sendUser = selectUser1.employee_name
                        
                        # 칭찬직원
                        selectUser2 = User2.objects.get(id=insertUserNotices.user_id)
                        recvUser = selectUser2.employee_name
                        
                        #------------------------------------------------------------------
                        # openAI call (ChatGPT 2023-11-01)
                        #------------------------------------------------------------------
                        def call_openAi_GPT ():
                            outputJson = openAi(inputData, sendUser, recvUser)
                            short_content = outputJson['summary']
                            tag           = {'tag': outputJson['tag']}
                            emotion_ratio = ''

                            return short_content, tag
                        
                        #------------------------------------------------------------------
                        # 한국어 AI call (2023-01-01)
                        #------------------------------------------------------------------
                        def select_kWords ():
                            print("### [VIEW][LOG] select_kWords === ")

                            ############
                            # tag 추출
                            ############
                            exclude_words = [sendUser, recvUser]

                            result = ' '.join([word for word in inputData.split() if word not in exclude_words])
                            print("### [VIEW][LOG] text converse : ", result)
                            text = result

                            #단어추출
                            try:
                                #okt = Okt()
                                tag_words = [word for word in okt.nouns(text) if word not in exclude_words][:3]
                                tag       = {'tag': tag_words}
                            except:
                                tag = {'tag': ['감사','칭찬','도움']}
                                    
                            if not tag_words:
                                tag = {'tag': ['감사','칭찬','도움']}
                                print('### [VIEW][LOG] tag_words error ')
                            else :
                                print('### [VIEW][LOG] tag_words success ')
                                
                            print("### [VIEW][LOG] 주요 태그:", tag)
                            
                            ############
                            # 요약 추출
                            ############
                            if len(text) < 50:
                                short_content = text
                                
                            else:
                                
                                try: 
                                    #short_content = summarize(text)
                                    
                                    # Summarizer 객체 생성
                                    #summarizer = Summarizer()

                                    # 텍스트 요약
                                    short_content = summarizer(text)

                                    print('### [VIEW][LOG] summarize success ')
                                except:
                                    short_content = ''
                                    print('### [VIEW][LOG] summarize error ')
                                
                                print('### [VIEW][LOG] short_content', short_content)
                                
                                if short_content == '':
                                    short_content = text[:40] + "..."
                                    
                                if len(short_content) > 40:  
                                    short_content = short_content[:40] + "..."
                                
                            print("### [VIEW][LOG] 원본 길이:", len(short_content))
                            print("### [VIEW][LOG] 요약 내용:", short_content)

                            return short_content, tag

                        ##################
                        # AI호출 구분
                        ##################
                        print("### [VIEW][LOG] inputData 원본 길이:", len(inputData))

                        #if len(inputData) >= 50:  
                        #    short_content, tag = call_openAi_GPT()
                        #else : 
                        #    short_content, tag = select_kWords()

                        short_content, tag = select_kWords()
                        
                        print("### [VIEW][LOG] short_content:", short_content)
                        print("### [VIEW][LOG] tag          :", tag)
                        
                        #-------------
                        # DB Update
                        #-------------
                        updateUserPraise = UserPraise.objects.get(compliment_id=insertUserPraise.compliment_id) 

                        updateUserPraise.short_content  = short_content
                        updateUserPraise.tag            = tag
                        #updateUserPraise.emotion_ratio  = emotion_ratio

                        updateUserPraise.save()
                        
                        
                    except:                    
                        #-------------
                        # 오류내용 SET
                        #-------------
                        print("### [VIEW][LOG][ERROR openAi] 칭찬글 분석시 오류가 발생 했습니다.")
                        #print("에러 메시지:", str(e))

                        #-------------
                        # ERROR DB Update
                        #-------------
                        updateUserPraise = UserPraise.objects.get(compliment_id=insertUserPraise.compliment_id) 
                        updateUserPraise.short_content  = '시스템 확인 중 입니다.'
                        updateUserPraise.tag            = {'tag': ['확인중']}
                        updateUserPraise.emotion_ratio  = ''

                        updateUserPraise.save()

                    #----------------------------------------------------------------------------------------------------
                    # FINAL : 정상응답
                    #----------------------------------------------------------------------------------------------------
                    
                    # selectThankyouWeeksYn이 None이면 >  땡큐주간 아닌경우 (.first() > None으로 분기처리)
                    if selectThankyouWeeksYn is None:
                        return redirect('/')
                    else:
                        return redirect('/?showThkWeekModal=true')
            
            except:
                
                transaction.rollback()

                #-------------
                # 오류내용 SET
                #-------------
                error = "[403] 데이터 저장시 오류가 발생 했습니다."
                info = {'error': error,
                           'praise_id': request.POST.get('input_employee_id', ''),
                           'content': request.POST.get('input_Contents', ''),
                           'input_active': request.POST.get('input_active', '')}
                
                #-------------
                # 출력부 SET
                #-------------
                selectUserImages = UserImages.objects.filter(is_open='Y', is_active='Y').order_by('-reg_date')

                paginator = Paginator(selectUserImages, 100)
                page = request.GET.get('page')
                posts = paginator.get_page(page)
                
                return render(request, 'tk_talk.html', {'posts':posts, 'info':info,})
            
        else:
            #-------------
            # 오류내용 SET
            #-------------
            error = "[404] 입력된 데이터가 없습니다."
            info = {'error': error,
                       'praise_id': request.POST.get('input_employee_id', ''),
                       'content': request.POST.get('input_Contents', ''),
                       'input_active': request.POST.get('input_active', '')}
            
            #-------------
            # 출력부 SET
            #-------------
            selectUserImages = UserImages.objects.filter(is_open='Y', is_active='Y').order_by('-reg_date')

            paginator = Paginator(selectUserImages, 100)
            page = request.GET.get('page')
            posts = paginator.get_page(page)

            return render(request, 'tk_talk.html', {'posts':posts, 'info':info,})

    #-------------
    # 업무로직
    #-------------
    
    # 토큰정보
    today = datetime.now().strftime('%Y%m%d')
    selectManageTokens = ManageTokens.objects.filter(
        Q(start_date__lte=today) & Q(end_date__gte=today)
    ).first()

    #toeknYear    = selectManageTokens.year
    #toeknQuarter = selectManageTokens.quarter
    
    #-------------
    # 토큰발행여부 검증
    #-------------
    if not selectManageTokens:
        print("### 토큰 정상필요")
        selectManageTokens = ManageTokens.objects.filter(
            Q(start_date__lte=today) & Q(end_date__gte=today)
        ).first()
    
        #error = "[안내] 관리자에게 문의 요청 드립니다. 발행된 토큰이 없습니다"
        #return render(request, 'page_error.html', {'error': error})
    
    if selectManageTokens :
        toeknCount   = selectManageTokens.tokens
        token_id     = selectManageTokens.id
    else :
        toeknCount   = 0
        token_id     = 0

    selectUserTokens = UserTokens.objects.filter(
        user_id  = request.user.id,
        token_id = token_id,
        #year=toeknYear,
        #quarter=toeknQuarter,
        is_active='Y'
    ).first()

    return render(request, 'tk_talk.html',  {'posts':posts, 'images':images, 'addPage':'Y', 'user_info': user_info, 'posts_All':posts_All,'posts_1':posts_1,'posts_2':posts_2,'posts_3':posts_3, 'posts_4':posts_4,'posts_5':posts_5,'posts_6':posts_6,'posts_7':posts_7, 'token':selectUserTokens, 'manage':selectManageTokens})


@login_required(login_url='/accounts/signin/')
def manageThankyouWeeks(request):
    print("### [VIEW] manageThankyouWeeks ####################################################")
    
    #-------------
    # 사용자 검증
    #-------------
    if request.user.is_superuser :
        print("### 관리자 접속")
    else :
        print("### 사용자 접속")
        error = "[101] 관리자 외 접속 불가합니다."
        return render(request, 'page_error.html', {'error': error})  
    
    ##########################
    # POST 수신시
    ##########################
    if request.method == 'POST':
        
        for key, value in request.POST.items():
            print(key, value)
                
        for key, file in request.FILES.items():
            print(key, file)
                
        #-------------
        # 업무로직
        #-------------
        if 'token_regedit' in request.POST:
            
            try:
                print('manageThankyouWeeks 전')

                insertManageThankyouWeeks = ManageThankyouWeeks()
                
                print('insertManageThankyouWeeks')

                #################################################
                # DB INSERT
                #################################################
                start_date = request.POST['manage_start_date']
                end_date = request.POST['manage_end_date']
                
                start_date_val = start_date.replace('-', '')  # 'yyyymmdd' 형식으로 변환
                end_date_val = end_date.replace('-', '')  # 'yyyymmdd' 형식으로 변환
                
                #weeks_year, weeks_month 화면 저장시에 입력할 수 있게 설정하기
                insertManageThankyouWeeks.weeks_ym = start_date_val[0:6]

                insertManageThankyouWeeks.start_date = start_date_val
                insertManageThankyouWeeks.end_date   = end_date_val
                
                insertManageThankyouWeeks.is_active  = 'Y'
                insertManageThankyouWeeks.reg_date   = datetime.now()
                insertManageThankyouWeeks.save()
                
                #-------------
                # 출력내용 SET
                #-------------
                selectManageThankyouWeeks = ManageThankyouWeeks.objects.filter(is_active='Y').order_by('-start_date')

                paginator = Paginator(selectManageThankyouWeeks, 10)
                page = request.GET.get('page')
                tokens = paginator.get_page(page)

                return render(request, 'manage/manageThankyouWeeks.html', {'tokens':tokens})
            
            
            except:
                error = "[403] 입력이 잘못 되었습니다."
                return render(request, 'manage/manageThankyouWeeks.html', {'error': error}) 
        
        elif 'token_update' in request.POST:
            
            try:
                updateManageThankyouWeeks = ManageThankyouWeeks.objects.get(id=request.POST['token_id'])
                #################################################
                # DB UPDATE
                #################################################                
                start_date = request.POST['manage_start_date']
                end_date = request.POST['manage_end_date']
                start_date_val = start_date.replace('-', '')  # 'yyyymmdd' 형식으로 변환
                end_date_val = end_date.replace('-', '')  # 'yyyymmdd' 형식으로 변환
                
                
                updateManageThankyouWeeks.weeks_ym = start_date_val[0:6]

                updateManageThankyouWeeks.start_date = start_date_val
                updateManageThankyouWeeks.end_date   = end_date_val
                updateManageThankyouWeeks.chg_date   = datetime.now()

                updateManageThankyouWeeks.save()
                
                #-------------
                # 출력내용 SET
                #-------------
                selectManageThankyouWeeks = ManageThankyouWeeks.objects.filter(is_active='Y').order_by('-start_date')

                paginator = Paginator(selectManageThankyouWeeks, 10)
                page = request.GET.get('page')
                tokens = paginator.get_page(page)

                return render(request, 'manage/manageThankyouWeeks.html', {'tokens':tokens})
            
            
            except:
                error = "[403] 입력이 잘못 되었습니다."
                return render(request, 'manage/manageThankyouWeeks.html', {'error': error})            
            
        elif 'token_delete' in request.POST:
            
            try:
                deleteManageThankyouWeeks = ManageThankyouWeeks.objects.get(id=request.POST['token_id'])
                deleteManageThankyouWeeks.is_active     = 'N'
                deleteManageThankyouWeeks.chg_date      = datetime.now()
                deleteManageThankyouWeeks.save()

                #-------------
                # 출력내용 SET
                #-------------
                selectManageThankyouWeeks = ManageThankyouWeeks.objects.filter(is_active='Y').order_by('-start_date')

                paginator = Paginator(selectManageThankyouWeeks, 10)
                page = request.GET.get('page')
                tokens = paginator.get_page(page)

                return render(request, 'manage/manageThankyouWeeks.html', {'tokens':tokens})
            
            except:
                error = "[403] 입력이 잘못 되었습니다."
                return render(request, 'manage/manageThankyouWeeks.html', {'error': error})                        
            
        else :     
            error = "[404] 입력된 데이터가 없습니다."
            return render(request, 'manage/manageThankyouWeeks.html', {'error': error})
        
    ##########################
    # 조회하면
    ##########################
    selectManageThankyouWeeks = ManageThankyouWeeks.objects.filter(is_active='Y').order_by('-start_date')
    
    paginator = Paginator(selectManageThankyouWeeks, 10)
    page = request.GET.get('page')
    tokens = paginator.get_page(page)
            
    return render(request, 'manage/manageThankyouWeeks.html', {'tokens':tokens})



@login_required(login_url='/accounts/signin/')
def manageUcExcelupload(request):
    print("### [VIEW] manageUcExcelupload ####################################################")
    
    #-------------
    # 사용자 검증
    #-------------
    if request.user.is_superuser :
        print("### 관리자 접속")
    else :
        print("### 사용자 접속")
        error = "[101] 관리자 외 접속 불가합니다."
        return render(request, 'page_error.html', {'error': error})
        

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            if file.name.endswith('.xlsx'):
                if process_excel_data(file) :
                    print("yes")
                    #채널W어플 가입여부
                    # for문 돌면서 send, recv username 둘다 값이 있으면               
                        # praise insert 
                        # tokens update send, recv
                        # BefInsUcmsg update
                        # get으로 하면 값 없을 때를 위해 try except문 사용해야 한다.
                    
        # all_ucmessages = BefInsUcmsg.objects.all()
        today = datetime.now().strftime('%Y-%m-%d')
        all_ucmessages = BefInsUcmsg.objects.filter(reg_date__icontains=today, insert_yn = 'R')

        for ucmessage in all_ucmessages:

            receiver = User2.objects.filter(username=ucmessage.recv_username)
            sender = User2.objects.filter(username=ucmessage.send_username)
            
            if receiver.exists() and sender.exists():
                print("*************************** send_username과 recv_username 둘 다 있음")
                send_user = sender.first()
                recv_user = receiver.first()

                try:
                    #------------------------------------
                    # 칭찬 insert
                    #------------------------------------
                    insertUserPraise = UserPraise()
                    
                    insertUserPraise.praise_id        = recv_user.id # 칭찬 받는 직원
                    insertUserPraise.user_id          = send_user.id # 칭찬한 직원
                    insertUserPraise.compliment_type  = '1'
                    
                    
                    #일괄 UC메시지
                    if ucmessage.images_id != '' and ucmessage.images_id != 'null'  :
                            insertUserPraise.images_id        = ucmessage.images_id
                    else : 
                        insertUserPraise.images_id        = '428'
                    
                    
                    if ucmessage.send_content != '' and ucmessage.send_content != 'null' and ucmessage.send_content != None  :
                        #chgageContents = re.sub('<\/?p[^>]*>', '', request.POST['input_Contents'])
                        insertUserPraise.content          = ucmessage.send_content
                        insertUserPraise.org_content      = ucmessage.send_content
                        insertUserPraise.short_content    = ucmessage.send_content[:100]
                    else:
                        insertUserPraise.content          = '감사합니다.'
                        insertUserPraise.org_content      = '감사합니다.'
                        insertUserPraise.short_content    = '감사합니다.'

                        
                    insertUserPraise.tag              = {'tag': ['감사','칭찬','UC']}
                    insertUserPraise.emotion_ratio    = '' # open ai 응답
                    
                    insertUserPraise.view_count       = 0
                    insertUserPraise.comment_count    = 0
                    insertUserPraise.likes_count      = 0

                    insertUserPraise.is_senduc        = 'Y'
                    
                    
                    #----------
                    # 토큰정보
                    #----------
                    # today = datetime.now().strftime('%Y%m%d')
                    msgtoday = ucmessage.send_time.strftime('%Y%m%d')
                    selectManageTokens = ManageTokens.objects.filter(
                        Q(start_date__lte=msgtoday) & Q(end_date__gte=msgtoday)
                    ).first()
                    insertUserPraise.token_id      = selectManageTokens.id
                    
                    insertUserPraise.is_active = 'Y'
                        
                    insertUserPraise.reg_date = ucmessage.send_time #datetime.now()   
                    
                    # print("### [VIEW][LOG] ucmessage insertUserPraise Save ==========")
                    insertUserPraise.save()
                    
                    # print('### [VIEW][LOG] ucmessage insertUserPraise.compliment_id   ', insertUserPraise.compliment_id)
                    
                    #------------------------------------
                    # 알림 insert - 칭찬대상 알림 / PUSH
                    #------------------------------------
                    pushId  = recv_user.id
                    title   = "땡큐토큰"
                    message = send_user.employee_name+ ' '+ send_user.position_name+"님이 칭찬글을 등록 했습니다."
                    url = "/thankyoutoken/praiseDetail/" + str(insertUserPraise.compliment_id)
                    PushYN, PushStatus  = ChwPushCall(pushId,title,message,url) #20240814 우리투자증권 대표이사 발송을 위해서 실행함
                    #title   = "thankyoutokentest"
                    #message = "thankyoutokentest"
                    # print("$$$$$$$$$$$$$$$ ucmessage.send_time.date() ", ucmessage.send_time.date())
                    # print("$$$$$$$$$$$$$$$ date.today() ", date.today())

                    # if ucmessage.send_time.date() == date.today() :
                    #     PushYN, PushStatus  = ChwPushCall(pushId,title,message,url)
                    # else :
                    #     PushYN = 'N'
                    #     PushStatus = ''

                    insertUserNotices = UserNotices()
                    insertUserNotices.user_id          = recv_user.id
                    insertUserNotices.send_id          = send_user.id
                    insertUserNotices.notice_type      = '1'
                    insertUserNotices.compliment_id    = insertUserPraise.compliment_id
                    insertUserNotices.comment_id       = 0 
                    insertUserNotices.check_yn         = 'N' 
                    insertUserNotices.push_yn          = 'N'
                    insertUserNotices.push_status      = ''
                    insertUserNotices.is_active        = 'Y'
                    insertUserNotices.reg_date         = datetime.now()                
                    insertUserNotices.save()
                    
                    # print('### [VIEW][LOG] ucmessage insertUserNotices.user_id   ', insertUserNotices.user_id)
                                    
                    # #------------------------------------
                    # # 토큰 insert & update
                    # #------------------------------------
                    # ##################################
                    # # 등록자 토큰감소
                    # ##################################

                    # # 토큰정보
                    # # today = datetime.now().strftime('%Y%m%d') 
                    # msgtoday = ucmessage.send_time.strftime('%Y%m%d')
                    # selectManageTokens = ManageTokens.objects.filter(
                    #     Q(start_date__lte=msgtoday) & Q(end_date__gte=msgtoday)
                    # ).first()
                    
                    # toeknYear    = selectManageTokens.year
                    # toeknQuarter = selectManageTokens.quarter
                    # toeknCount   = selectManageTokens.tokens
                    # hightoeknCount   = selectManageTokens.high_tokens

                    # # 소속장여부 확인
                    # # print('### send_user.company_id ', send_user.company_id)
                    # # print('### send_user.position_id ', send_user.position_id)
                    # selectuserReward = ManagePosi.objects.filter(
                    #     is_active  = 'Y',
                    #     company_id = send_user.company_id,
                    #     posi_id    = send_user.position_id
                    # ).first()

                    # # print('### ******* user ucmessage selectuserReward', selectuserReward)

                    # if selectuserReward:
                    #     # print('### user ucmessage selectuserReward', selectuserReward.reward_skip_yn)
                    #     if selectuserReward.reward_skip_yn == "Y" :
                    #         user_reward_skip_yn = "Y"
                    #     else :
                    #         user_reward_skip_yn = "N"
                    # else :
                    #     user_reward_skip_yn = "N"
                    #     # print('### else user ucmessage user_reward_skip_yn', user_reward_skip_yn)

                    # # 보유토큰 조회
                    # selectSendUserTokens = UserTokens.objects.filter(
                    #     user_id=send_user.id,
                    #     token_id = selectManageTokens.id,
                    #     is_active='Y'
                    # ).first()

                    # selectSendUserTokensCount = UserTokens.objects.filter(
                    #     user_id=send_user.id,
                    #     token_id = selectManageTokens.id,
                    #     is_active='Y'
                    # ).count()

                    # # UC메신저로도 칭찬 메시지가 있어서 순위에는 제외되도록
                    # selectSameTotalCount = UserPraise.objects.filter(
                    #         is_active='Y', 
                    #         token_id = selectManageTokens.id,
                    #         user_id = send_user.id,
                    #         praise_id = recv_user.id,
                    #     ).count()
                    

                    # if selectSendUserTokensCount > 0:
                    #     # 데이터가 존재하는 경우

                    #     # selectThankyouWeeksYn이 None이면 >  땡큐주간 아닌경우 (.first() > None으로 분기처리)
                    #     # if selectThankyouWeeksYn is None:
                    #     # UC메신저를 통한 땡큐토큰 발송은 my_current_tokens에 연관도 없음
                    #     #     selectUserTokens.my_current_tokens -= 1
                    #     if selectSameTotalCount == 1 :
                    #         selectSendUserTokens.my_send_tokens    += 1

                    #     selectSendUserTokens.chg_date = datetime.now()      
                    #     selectSendUserTokens.save()  # 업데이트 수행
                    #     print('### [VIEW][LOG] my ucmessage selectUserTokens.user_id   ', selectSendUserTokens.user_id)
                        
                    # else:
                    #     # 데이터가 존재하지 않는 경우
                    #     # print(" why why 왜!!!!!!!!!!!!!!! 보내는 아이디 chk send_user.id : " , send_user.id)
                    #     # print(" selectSendUserTokens : " ,selectSendUserTokens)
                        
                    #     insertSendUserTokens = UserTokens()
                    #     insertSendUserTokens.user_id           = send_user.id
                    #     insertSendUserTokens.token_id          = selectManageTokens.id
                    #     insertSendUserTokens.year              = toeknYear
                    #     insertSendUserTokens.quarter           = toeknQuarter
                        
                    #     #영업본부장님, 부행장들에게만 특정 수만큼 토큰 부여 2024.03.29
                    #     chkInsTokYn = User2.objects.filter(
                    #                         Q(position_name__contains='본부장') | Q(position_name__contains='부행장'),
                    #                         ~Q(id=5256),
                    #                         id=request.user.id,
                    #                         company_id=20    
                    #                     ).count()

                    #     if request.user.id == 15893: #회장님
                    #         insertSendUserTokens.my_tot_tokens = 100
                    #     else :
                    #         if chkInsTokYn > 0 :
                    #             insertSendUserTokens.my_tot_tokens = 100
                    #         else :
                    #             if user_reward_skip_yn == "Y" :
                    #                 insertSendUserTokens.my_tot_tokens = hightoeknCount
                    #             else : 
                    #                 insertSendUserTokens.my_tot_tokens = toeknCount
                        
                    #     insertSendUserTokens.my_current_tokens = insertSendUserTokens.my_tot_tokens
                    #     # UC메신저로도 칭찬 메시지가 있어서 순위에는 제외되도록
                    #     #UC 메신저로 보낸거 포인트에 넣어야 하나?
                    #     if selectSameTotalCount == 1 :
                    #         insertSendUserTokens.my_send_tokens    = 1
                    #     else :
                    #         insertSendUserTokens.my_send_tokens    = 0

                    #     insertSendUserTokens.received_tokens   = 0
                    #     insertSendUserTokens.is_active         = 'Y'
                    #     insertSendUserTokens.reg_date          = datetime.now()                
                    #     insertSendUserTokens.save()
                    #     # print('### [VIEW][LOG] ucmessage my insertUserTokens.my_tot_tokens   ', insertUserTokens.my_tot_tokens)
                    #     # print('### [VIEW][LOG] ucmessage my insertUserTokens.user_id   ', insertUserTokens.user_id)
                    
                    
                    # ###################################
                    # # 칭찬대상 토큰증가
                    # ###################################
                    # selectRecvUserTokens = UserTokens.objects.filter(
                    #     user_id=recv_user.id,
                    #     token_id = selectManageTokens.id,
                    #     is_active='Y'
                    # ).first()

                    
                    # if selectRecvUserTokens:
                    #     # 데이터가 존재하는 경우
                    #     if selectSameTotalCount == 1 :
                    #         selectRecvUserTokens.received_tokens += 1
                        
                    #     selectRecvUserTokens.chg_date = datetime.now()      
                    #     selectRecvUserTokens.save()  # 업데이트 수행
                    #     print('### [VIEW][LOG] ucmessage you selectRecvUserTokens.user_id   ', selectRecvUserTokens.user_id)
                        
                    # else:
                    #     # 데이터가 존재하지 않는 경우
                    #     insertRecvUserTokens = UserTokens()
                    #     insertRecvUserTokens.user_id           = recv_user.id
                    #     insertRecvUserTokens.token_id          = selectManageTokens.id
                    #     insertRecvUserTokens.year              = toeknYear
                    #     insertRecvUserTokens.quarter           = toeknQuarter
                        
                    #     #영업본부장님, 부행장들에게만 특정 수만큼 토큰 부여 2024.04.09
                    #     chkInsTokYn = User2.objects.filter(
                    #                         Q(position_name__contains='본부장') | Q(position_name__contains='부행장'),
                    #                         ~Q(id=5256),
                    #                         id=insertRecvUserTokens.user_id,
                    #                         company_id=20    
                    #                     ).count()
                        

                    #     # 칭찬 받는 직원 소속장여부 확인 
                    #     chkRecvUserInfo = User2.objects.get(id=insertRecvUserTokens.user_id)

                    #     recvUserReward = ManagePosi.objects.filter(
                    #         is_active  = 'Y',
                    #         company_id = chkRecvUserInfo.company_id,
                    #         posi_id    = chkRecvUserInfo.position_id
                    #     ).first()
                        
                        
                    #     if insertRecvUserTokens.user_id == '15893': #회장님
                    #         insertRecvUserTokens.my_tot_tokens = 100
                    #     else :
                    #         if chkInsTokYn > 0 :
                    #             insertRecvUserTokens.my_tot_tokens = 100
                    #         else :
                    #             if recvUserReward is not None and recvUserReward.reward_skip_yn == "Y" :
                    #                 insertRecvUserTokens.my_tot_tokens = hightoeknCount
                    #             else : 
                    #                 insertRecvUserTokens.my_tot_tokens = toeknCount
                                
                    #     # insertRecvUserTokens.my_tot_tokens     = toeknCount
                        
                    #     insertRecvUserTokens.my_current_tokens = insertRecvUserTokens.my_tot_tokens

                    #     insertRecvUserTokens.my_send_tokens    = 0

                    #     if selectSameTotalCount == 1 :
                    #         insertRecvUserTokens.received_tokens   = 1
                    #     else :
                    #         insertRecvUserTokens.received_tokens   = 0
                        
                    #     insertRecvUserTokens.is_active         = 'Y'
                    #     insertRecvUserTokens.reg_date          = datetime.now()                
                    #     insertRecvUserTokens.save()
                    #     print('### [VIEW][LOG] ucmessage you insertRecvUserTokens.user_id   ', insertRecvUserTokens.user_id)
                    
                    
                    #---------------
                    # open AI Call
                    #---------------
                    inputData = ucmessage.send_content
                    
                    
                    try:
                        # 등록직원
                        selectUser1 = User2.objects.get(id=insertUserNotices.send_id)
                        sendUser = selectUser1.employee_name
                        
                        # 칭찬직원
                        selectUser2 = User2.objects.get(id=insertUserNotices.user_id)
                        recvUser = selectUser2.employee_name
                        
                        #------------------------------------------------------------------
                        # openAI call (ChatGPT 2023-11-01)
                        #------------------------------------------------------------------
                        def call_openAi_GPT ():
                            outputJson = openAi(inputData, sendUser, recvUser)
                            short_content = outputJson['summary']
                            tag           = {'tag': outputJson['tag']}
                            emotion_ratio = ''

                            return short_content, tag
                        
                        #------------------------------------------------------------------
                        # 한국어 AI call (2023-01-01)
                        #------------------------------------------------------------------
                        def select_kWords ():
                            print("### [VIEW][LOG] ucmessage select_kWords === ")

                            ############
                            # tag 추출
                            ############
                            exclude_words = [sendUser, recvUser]

                            result = ' '.join([word for word in inputData.split() if word not in exclude_words])
                            print("### [VIEW][LOG] ucmessage text converse : ", result)
                            text = result

                            #단어추출
                            try:
                                #okt = Okt()
                                tag_words = [word for word in okt.nouns(text) if word not in exclude_words][:3]
                                tag       = {'tag': tag_words}
                            except:
                                tag = {'tag': ['감사','칭찬','도움']}
                                    
                            if not tag_words:
                                tag = {'tag': ['감사','칭찬','도움']}
                                print('### [VIEW][LOG] ucmessage tag_words error ')
                            else :
                                print('### [VIEW][LOG] ucmessage tag_words success ')
                                
                            print("### [VIEW][LOG] ucmessage 주요 태그:", tag)
                            
                            ############
                            # 요약 추출
                            ############
                            if len(text) < 50:
                                short_content = text
                                
                            else:
                                
                                try: 
                                    #short_content = summarize(text)
                                    
                                    # Summarizer 객체 생성
                                    #summarizer = Summarizer()

                                    # 텍스트 요약
                                    short_content = summarizer(text)

                                    print('### [VIEW][LOG] ucmessage summarize success ')
                                except:
                                    short_content = ''
                                    print('### [VIEW][LOG] ucmessage summarize error ')
                                
                                print('### [VIEW][LOG] ucmessage short_content', short_content)
                                
                                if short_content == '':
                                    short_content = text[:40] + "..."
                                    
                                if len(short_content) > 40:  
                                    short_content = short_content[:40] + "..."
                                
                            print("### [VIEW][LOG] ucmessage 원본 길이:", len(short_content))
                            print("### [VIEW][LOG] ucmessage 요약 내용:", short_content)

                            return short_content, tag

                        ##################
                        # AI호출 구분
                        ##################
                        print("### [VIEW][LOG] ucmessage inputData 원본 길이:", len(inputData))

                        #if len(inputData) >= 50:  
                        #    short_content, tag = call_openAi_GPT()
                        #else : 
                        #    short_content, tag = select_kWords()

                        short_content, tag = select_kWords()
                        
                        print("### [VIEW][LOG] ucmessage short_content:", short_content)
                        print("### [VIEW][LOG] ucmessage tag          :", tag)
                        
                        #-------------
                        # DB Update
                        #-------------
                        updateUserPraise = UserPraise.objects.get(compliment_id=insertUserPraise.compliment_id) 

                        updateUserPraise.short_content  = short_content
                        updateUserPraise.tag            = tag
                        #updateUserPraise.emotion_ratio  = emotion_ratio

                        updateUserPraise.save()
                        
                        
                    except:                    
                        #-------------
                        # 오류내용 SET
                        #-------------
                        print("### [VIEW][LOG][ERROR openAi] ucmessage 칭찬글 분석시 오류가 발생 했습니다.")
                        #print("에러 메시지:", str(e))

                        #-------------
                        # ERROR DB Update
                        #-------------
                        updateUserPraise = UserPraise.objects.get(compliment_id=insertUserPraise.compliment_id)
                        updateUserPraise.short_content  = '시스템 확인 중 입니다.'
                        updateUserPraise.tag            = {'tag': ['확인중']}
                        updateUserPraise.emotion_ratio  = ''

                        updateUserPraise.save()

                    #----------------------------------------------------------------------------------------------------
                    # FINAL : 정상응답
                    #----------------------------------------------------------------------------------------------------
                                            
                    # account_user_befinsucmsg 테이블에 Insert
                    print("관리자 일괄등록 FINAL : 정상응답 ucmessage.id : ", ucmessage.id)
                    updateBefInsUcmsg = BefInsUcmsg.objects.get(id=ucmessage.id) 
                    updateBefInsUcmsg.insert_yn  = 'Y'
                    updateBefInsUcmsg.insert_time = datetime.now()
                    updateBefInsUcmsg.insertfail_reason = ''

                    updateBefInsUcmsg.save()

                
                except:
                    
                    #-------------
                    # 오류내용 SET
                    #-------------
                    error = "[403] UC메신저 데이터 저장시 오류가 발생 했습니다."
                    info = {'error': error}
                    
                    return render(request, 'manage/manageUcExcelupload.html', {'info':info,})
            
            elif sender.exists() and not receiver.exists():
                print("send_username만 있음 insertfail_reason")
                updateBefInsUcmsg = BefInsUcmsg.objects.get(id=ucmessage.id) 
                updateBefInsUcmsg.insert_yn  = 'N'
                updateBefInsUcmsg.insertfail_reason = f"수신자 채널W 미가입 사번 : {ucmessage.recv_username}"
                
                updateBefInsUcmsg.save()
            
            elif not sender.exists() and receiver.exists():
                print("recv_username만 있음 insertfail_reason")
                updateBefInsUcmsg = BefInsUcmsg.objects.get(id=ucmessage.id) 
                updateBefInsUcmsg.insert_yn  = 'N'
                updateBefInsUcmsg.insertfail_reason = f"발송자 채널W 미가입 사번 : {ucmessage.send_username}"
                
                updateBefInsUcmsg.save()
            
            elif not sender.exists() and not receiver.exists():
                print("둘 다 없음 insertfail_reason")
                updateBefInsUcmsg = BefInsUcmsg.objects.get(id=ucmessage.id) 
                updateBefInsUcmsg.insert_yn  = 'N'
                updateBefInsUcmsg.insertfail_reason = f"발송/수신 둘다 채널W 미가입"
                
                updateBefInsUcmsg.save()

            else :
                print("err")
        
    
        registered_successfully = True  # 예를 들어, 실제로 등록이 완료되었을 때 True로 설정해야 합니다.
        today = datetime.now().strftime('%Y-%m-%d')
        all_ucmessages = BefInsUcmsg.objects.filter(reg_date__icontains=today).order_by('insert_yn')

        #등록한 파일명
        registered_filename = file.name
        

        #등록한 건수
        insertYesCnt = BefInsUcmsg.objects.filter(insert_yn = 'Y', reg_date__icontains=today).count()
        #등록 실패한 건수
        insertNoCnt = BefInsUcmsg.objects.filter(insert_yn = 'N', reg_date__icontains=today).count()

        return render(request, 'manage/manageUcExcelupload.html'
                    , {'registered_successfully': registered_successfully, 'uc_messages': all_ucmessages, 'today': today, 'registered_filename':registered_filename
                        , 'insertYesCnt': insertYesCnt, 'insertNoCnt':insertNoCnt})
        # registered_successfully = True
        # return render(request, 'manage/manageUcExcelupload.html', {'registered_successfully': registered_successfully})
        # 채널W어플 미가입자 대상 조회화면 개발
        # 미대상들만 신규로 넣을 수 있게 세팅 날짜가 같아도 다르게 넣을 수 있게 세팅
        # return render(request, 'upload.html', {'data_ready': True})  # 데이터 준비 완료 메시지 표시
    else:
        # form = UploadFileForm()
        print("Post 아닌경우")
        # return render(request, 'manage/manageUcExcelupload.html')
    
    today = datetime.now().strftime('%Y-%m-%d')
    all_ucmessages = BefInsUcmsg.objects.filter(reg_date__icontains=today).order_by('insert_yn')

    #등록한 건수
    insertYesCnt = BefInsUcmsg.objects.filter(insert_yn = 'Y', reg_date__icontains=today).count()
    #등록 실패한 건수
    insertNoCnt = BefInsUcmsg.objects.filter(insert_yn = 'N', reg_date__icontains=today).count()

    return render(request, 'manage/manageUcExcelupload.html', {'uc_messages': all_ucmessages, 'today': today, 'insertYesCnt': insertYesCnt, 'insertNoCnt':insertNoCnt})

