####################################################################
# 업무제목 : 땡큐토큰 API 업무
# 프로그램 : apis.py
# ------------------------------------------------------------------
# 2023-12-11 김대영 최초개발
# 2023-12-22 김대영 엑셀일괄 다운로드 추가
# 2023-12-28 김대영 유저데이터 이행작업 수행
# 2024-01-23 김대영 전직자 정보검증 추가
# 2024-03-04 윤준영 리뉴얼 개발 (토큰 추가, 왕관표시, 칭찬5개 체크, MY땡큐 등등..)
# 2024-04-01 윤준영 투데이땡큐 등록 및 해제
# 2024-06-05 윤준영 UC메신저 땡큐토큰은 제한로직에서 예외처리
# 2024-12-17 VTI   Add a filter condition for user search to the `praise_page` API.
# 2024-12-25 VTI   Add APIs in home, search, tk_list, rankList screen.
# 2025-04-23 VTI   add limit, offset in api get data tk_list
####################################################################
from django.shortcuts import render, HttpResponse
from myprofile.models import User as User2
from myprofile.models import UserTokens, UserPraise, UserNotices, UserComment, UserImages, UserLike, ManageTokens, ManageDept, ManagePosi, MigrationUser, ManageTokensGroup

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

from datetime import datetime
from django.utils.html import escape

from django.db.models.expressions import Case
from django.db.models.query import When
from django.utils import timezone


from konlpy.tag import Okt
# from gensim.summarization.summarizer import summarize
from summarizer import Summarizer    # pip install bert-extractive-summarizer

import requests
import time
import random

import hashlib
import hmac
import base64

from django.views.decorators.csrf import csrf_exempt
from django.db.models import Max    
from django.db.models import F

from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.humanize.templatetags import humanize

#import matplotlib.pyplot as plt
from wordcloud import WordCloud
import os
from datetime import date
from django.conf import settings
from django.core.files.storage import FileSystemStorage
import numpy as np
from PIL import Image

from django.db.models.functions import Coalesce
from django.db.models import OuterRef, Subquery
from django.db.models import Value, CharField
from django.db.models import ExpressionWrapper, fields, Sum

from .decorators import measure_execution_time
from .services.rankList import get_user_tokens_base_query, get_active_tokens, get_user_praise_query, get_group_mapping
from .services.tk_list import select_my_list, get_user_praise_queryset

# Okt 객체를 전역으로 선언하여 재사용
okt = Okt()

# Summarizer 객체 생성
# summarizer = Summarizer()

@csrf_exempt
def praise_like(request):
    print('### [API] praise_like ####################################################')
    
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':
        for key, value in request.POST.items():
            print('### [INPUT] ', key, value)
            
        #-------------
        # 업무로직
        #-------------
        if request.POST['compliment_id']:
            try:        
                
                compliment_id = request.POST.get('compliment_id')
                
                # 로그인 user_id 가져오기
                user_id = request.user.id
                print('### [user_id] ',user_id)
                
                # 취소여부 설정
                CancelYn = 'N'
                
                # 좋아요 테이블 select 문 실행
                result = UserLike.objects.filter(compliment_id=compliment_id, user_id = user_id, is_active = 'Y')
               


                if result.exists():
                    # 업무원장 갱신
                    updateUserPraise = UserPraise.objects.get(compliment_id=compliment_id)
                    updateUserPraise.likes_count -= 1
                    updateUserPraise.save()
                    
                    # 좋아요 원장 갱신
                    updateUserLike = UserLike.objects.filter(compliment_id=compliment_id, user_id=user_id).update(is_active='N')
                    
                    # 취소여부
                    CancelYn = 'Y'
                    
                else:
                    # result가 존재하지 않는 경우 처리할 내용
                    # 좋아요 테이블 insert 문 실행
                
                    result_Like = UserLike.objects.filter(compliment_id=compliment_id, user_id = user_id)
                    if result_Like.exists():
                        updateUserLike = UserLike.objects.filter(compliment_id=compliment_id, user_id=user_id).update(is_active='Y')
                    else:
                        #------------------------------------------------
                        # DB INSERT
                        #------------------------------------------------
                        insertUserLike = UserLike()

                        insertUserLike.compliment_id    = compliment_id           
                        insertUserLike.user_id          = user_id         
                        insertUserLike.is_active        = 'Y'

                        print('insertUserLike.compliment_id   ', insertUserLike.compliment_id)
                        print('insertUserLike.user_id         ', insertUserLike.user_id)

                        insertUserLike.chg_date = datetime.now()   
                        insertUserLike.reg_date = datetime.now()  
                        insertUserLike.save()
                    
                    # 칭찬테이블 update 문 실행
                    updateUserPraise = UserPraise.objects.get(compliment_id=compliment_id)
                    updateUserPraise.likes_count += 1
                    updateUserPraise.save() 


                #-------------
                # 출력내용 SET
                #-------------
                ResultData = {
                    'status' : '200',
                    'likes_count' : updateUserPraise.likes_count,
                    'CancelYn' : CancelYn
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 
    
            except:
                ResultData = {
                    'status' : '402',
                    'error' : 'DB적재시 오류가 발생 했습니다.'
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 
        else:
            ResultData = {
                'status' : '401',
                'error' : '입력 데이터가 없습니다.'
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
def praise_list(request):
    print('### [API] praise_list ####################################################')
    
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':        
        #for key, value in request.POST.items():
        #    print('### [INPUT] ', key, value)
            
        #-------------
        # 업무로직
        #-------------
        selectUserPraise = UserPraise.objects.filter(is_active='Y')\
            .select_related('praise', 'images').annotate(
                praise_employee_name=F('praise__employee_name'),
                user_employee_name=F('user__employee_name'),
                image_path=F('images__image_path')
            ).order_by('-reg_date')
        
        # 데이터를 담을 리스트 초기화
        data_list = []

        # 필드별 데이터를 리스트에 담습니다.
        for obj in selectUserPraise:
            if obj.chg_date is not None:
                chg_date_str = obj.chg_date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                chg_date_str = None

            if obj.reg_date is not None:
                reg_date_str = obj.reg_date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                reg_date_str = None
                    
            data_list.append({
                'compliment_id': obj.compliment_id,
                'praise_id': obj.praise_id,
                'user_id': obj.user_id,
                'praise_employee_name': obj.praise_employee_name,
                'user_employee_name': obj.user_employee_name,
                'image_path': obj.image_path,
                'compliment_type': obj.compliment_type,
                'content': obj.content,
                'images_id': obj.images_id,
                'short_content': obj.short_content,
                'tag': obj.tag,
                'emotion_ratio': obj.emotion_ratio,
                'view_count': obj.view_count,
                'comment_count': obj.comment_count,
                'likes_count': obj.likes_count,
                'token_id': obj.token_id,
                'is_active': obj.is_active,
                'chg_date': chg_date_str,
                'reg_date': reg_date_str,
            })
        
        #-------------
        # 출력내용 SET
        #-------------
        # 결과 데이터에 리스트와 총 건수를 추가합니다.
        ResultData = {
            'status': '200',
            'data_count': len(data_list),
            'data_list': data_list,
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
@measure_execution_time
def get_praise_posts(request):
    # ==========================
    # 2024-12-25 Add APIs in home, search, tk_list, rankList screen.
    # 2025-04-23 add limit, offset in api get data tk_list
    # ==========================

    """
    API endpoint for fetching user praise posts.
    """
    try:
        # page and offset
        page_number = int(request.GET.get('page', 1))
        limit = 10
        offset = (page_number - 1) * limit

        # Get compliment IDs for the current user
        compliment_ids = select_my_list(request.user.id)

        # Get user praise data
        processed_queryset = get_user_praise_queryset(compliment_ids, request.user.id, limit, offset)

        # Serialize the queryset
        serialized_data = list(processed_queryset.values())

        # Convert datetime objects to string format
        for item in serialized_data:
            if 'reg_date' in item:
                item['reg_date'] = item['reg_date'].strftime('%Y-%m-%d %H:%M:%S')

        return JsonResponse({
            'status': 'success',
            'data_count': len(serialized_data),
            'data_list': serialized_data
        })

    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)


@csrf_exempt
@measure_execution_time
def get_group_data(request):
    # ==========================
    # 2024-12-25 Add APIs in home, search, tk_list, rankList screen.
    # ==========================

    """API endpoint to retrieve group data for superuser"""
    today = datetime.now().strftime('%Y%m%d')
    data_type = request.GET.get('type', 'posts')  # 'posts', 'group', or 'postsGroup'
    group = request.GET.get('group') # 'A', 'B', 'C' or 'D'
    
    # Get manage tokens
    manage_token_id = request.GET.get('manage_token_id', 0)
    basic_tokens = get_active_tokens(ManageTokens, today)
    
    if int(basic_tokens.id) == int(manage_token_id):
        manage_token_id = 0
    
    select_tokens = (
        get_active_tokens(ManageTokens, today) if manage_token_id == 0
        else ManageTokens.objects.filter(id=manage_token_id, is_active='Y').first()
    )

    # Get active staff users
    manage_user_ids = User2.objects.filter(
        is_staff=True, is_active=True
    ).values_list('id', flat=True)

    response_data = {'status': 'success', 'data': {}}
    company_id = request.user.company_id

    if data_type == 'posts':
        # Handle company specific logic
        dept_ids = []
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
            
            company_filters = {
                'user__company_id': company_id,
                'user__department_id__in': dept_ids
            }
        else:
            company_filters = {'user__company_id': company_id}
        
        # Get user praise data
        base_query = get_user_tokens_base_query(
            select_tokens.id,
            company_filters,
            manage_user_ids
        )
        posts = list(get_user_praise_query(base_query, False))
        response_data['data']['posts'] = posts

    elif data_type == 'group':
        if not group or group not in ['A', 'B', 'C', 'D']:
            return JsonResponse({'error': 'Invalid group parameter'}, status=400)

        # Handle group data
        group_tokens = get_active_tokens(ManageTokensGroup, today)
        token_ids = ManageTokens.objects.filter(
            Q(start_date__gte=group_tokens.start_date) &
            Q(end_date__lte=group_tokens.end_date),
            is_active='Y'
        ).values_list('id', flat=True)
        
        groups = get_group_mapping()
        group_companies = groups.get(group)

        if not group_companies:
            return JsonResponse({'error': 'Group not found'}, status=404)
            
        group_filters = {'user__company_id__in': group_companies}
        base_query = get_user_tokens_base_query(
            token_ids,
            group_filters,
            manage_user_ids
        )
        group_posts = list(get_user_praise_query(base_query, True))
        
        response_data['data'].update({
            'posts': group_posts,
            'group_info': {
                'companies': group_companies,
                'count': len(group_posts)
            }
        })

    elif data_type == 'postsGroup':
        # Handle group data for current user
        group_tokens = get_active_tokens(ManageTokensGroup, today)
        token_ids = ManageTokens.objects.filter(
            Q(start_date__gte=group_tokens.start_date) &
            Q(end_date__lte=group_tokens.end_date),
            is_active='Y'
        ).values_list('id', flat=True)
        
        # Determine user's group
        groups = get_group_mapping()
        user_group = next(
            (group_id for group_id, companies in groups.items() 
             if company_id in companies),
            None
        )
        
        if user_group:
            group_filters = {'user__company_id__in': groups[user_group]}
            group_base_query = get_user_tokens_base_query(
                token_ids,
                group_filters,
                manage_user_ids
            )
            posts_group = list(get_user_praise_query(group_base_query, False))
            
            response_data['data'].update({
                'posts': posts_group,
                'group_info': {
                    'group': user_group,
                    'companies': groups[user_group]
                }
            })
        else:
            response_data['data']['posts'] = []

    return JsonResponse(response_data, encoder=DjangoJSONEncoder)


@csrf_exempt
@measure_execution_time
def praise_first_page(request):
    # ==========================
    # 2024-12-25 Add APIs in home, search, tk_list, rankList screen.
    # ==========================

    # Get search parameters
    exist_todaythanks = request.GET.get('exist_todaythanks')

    # Get list of liked compliments 
    liked_compliments = UserLike.objects.filter(
        user_id=request.user.id,
        is_active='Y'
    ).values_list('compliment_id', flat=True)

    # Common annotations
    annotations = {
        'praise_employee_name': F('praise__employee_name'),
        'praise_employee_id': F('praise__employee_id'),
        'praise_department_name': F('praise__department_name'),
        'praise_position_name': F('praise__position_name'),
        'praise_company_name': F('praise__company_name'),
        'praise_image_yn': F('praise__image_yn'),
        'praise_image': F('praise__image'),
        'user_employee_name': F('user__employee_name'),
        'user_employee_id': F('user__employee_id'),
        'user_department_name': F('user__department_name'),
        'user_position_name': F('user__position_name'),
        'user_company_name': F('user__company_name'),
        'user_image_yn': F('user__image_yn'),
        'user_image': F('user__image'),
        'image_path': F('images__image_path'),
        'like_yn': Case(
            When(compliment_id__in=liked_compliments, then=1),
            default=0,
        )
    }

    # Define base query for reuse
    base_query = UserPraise.objects.filter(is_active='Y')

    if exist_todaythanks == 'Y':
        # If records exist with first condition, get 1 + 5 records
        results = list(
            base_query.filter(todaythanks_showyn='Y')
            .select_related('praise', 'images', 'user')
            .annotate(**annotations)
            .values()
            .order_by('-reg_date')[:1]
            .union(
                base_query
                .filter(Q(todaythanks_showyn='N') | Q(todaythanks_showyn__isnull=True))
                .select_related('praise', 'images', 'user')
                .annotate(**annotations)
                .values()
                .order_by('-reg_date')[:5]
            )
        )
    else:
        # If no records with first condition, get 6 records from second condition
        results = list(
            base_query
            .filter(Q(todaythanks_showyn='N') | Q(todaythanks_showyn__isnull=True))
            .select_related('praise', 'images', 'user')
            .annotate(**annotations)
            .values()
            .order_by('-reg_date')[:6]
        )
    
    # Process content
    for post in results:
        if 'content' in post:
            post['content'] = post['content'].replace('\r\n', '<br>').replace('\r', '<br>').replace('\n', '<br>')

    return JsonResponse({
        'status': '200',
        'data_count': len(results),
        'data_list': results
    }, safe=False)

@csrf_exempt
@measure_execution_time
def praise_first_page_search(request):
    # ==========================
    # 2024-12-25 Add APIs in home, search, tk_list, rankList screen.
    # ==========================

    # Get search parameters
    user_id = request.GET.get('input_search')

    # Get active users matching search criteria
    active_user_ids = User2.objects.filter(
        id=user_id,
        is_active=True
    ).values_list('id', flat=True)

    # Get current user's liked posts
    liked_compliments = UserLike.objects.filter(
        user_id=request.user.id,
        is_active='Y'
    ).values_list('compliment_id', flat=True)

    # Common annotations
    annotations = {
        'praise_employee_name': F('praise__employee_name'),
        'praise_employee_id': F('praise__employee_id'),
        'praise_department_name': F('praise__department_name'),
        'praise_position_name': F('praise__position_name'),
        'praise_company_name': F('praise__company_name'),
        'praise_image_yn': F('praise__image_yn'),
        'praise_image': F('praise__image'),
        'user_employee_name': F('user__employee_name'),
        'user_employee_id': F('user__employee_id'),
        'user_department_name': F('user__department_name'),
        'user_position_name': F('user__position_name'),
        'user_company_name': F('user__company_name'),
        'user_image_yn': F('user__image_yn'),
        'user_image': F('user__image'),
        'image_path': F('images__image_path'),
        'like_yn': Case(
            When(compliment_id__in=liked_compliments, then=1),
            default=0,
        )
    }

    # Combine queries using union
    results = list(
        UserPraise.objects.filter(
            Q(praise_id__in=active_user_ids) | 
            Q(user_id__in=active_user_ids),
            is_active='Y',
        )
        .select_related('praise', 'images', 'user')
        .annotate(**annotations)
        .values()
        .order_by('-reg_date')[:6]
    )
    
    # Process content
    for post in results:
        if 'content' in post:
            post['content'] = post['content'].replace('\r\n', '<br>').replace('\r', '<br>').replace('\n', '<br>')

    return JsonResponse({
        'status': '200',
        'data_count': len(results),
        'data_list': results
    }, safe=False)


@csrf_exempt
@measure_execution_time
def praise_page_new(request):
    # ==========================
    # 2024-12-25 refactor API praise page
    # ==========================

    # Get input parameters with default value
    user_id = request.GET.get('input_search')
    exist_todaythanks = request.GET.get('exist_todaythanks')
    page_number = int(request.GET.get('pageNumber', 0))

    # Get liked posts as list (not set) since it's used only once in Case/When
    liked_compliments = UserLike.objects.filter(
        user_id=request.user.id,
        is_active='Y'
    ).values_list('compliment_id', flat=True)

    # Start with base query
    if user_id:
        selectUserPraise = UserPraise.objects.filter(is_active='Y')
    else:
        selectUserPraise = UserPraise.objects.filter(
            Q(todaythanks_showyn='N') | Q(todaythanks_showyn__isnull=True),
            is_active='Y'
        )
    
    # Add user filter only if user_id exists
    if user_id:
        selectUser = User2.objects.filter(
            id=user_id,
            is_active=True
        ).values_list('id', flat=True)
        
        selectUserPraise = selectUserPraise.filter(
            Q(praise_id__in=selectUser) |
            Q(user_id__in=selectUser)
        )
    
    # Annotate and get paginated results
    if user_id or exist_todaythanks != 'Y':
        offset = (page_number * 10) + 6
    else:
        offset = (page_number * 10) + 5

    selectUserPraise = selectUserPraise.select_related('praise', 'images').annotate(
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
            When(compliment_id__in=liked_compliments, then=1),
            default=0,
        )  
    ).order_by('-reg_date')[offset:offset + 10]

    # Build data list
    data_list = []
    for obj in selectUserPraise:
        chg_date_str = obj.chg_date.strftime('%Y-%m-%d %H:%M:%S') if obj.chg_date else None
        reg_date_str = obj.reg_date.strftime('%Y-%m-%d %H:%M:%S') if obj.reg_date else None
        post_date = humanize.naturaltime(obj.reg_date)
        
        content = obj.content.replace('\r\n', '<br>').replace('\r', '<br>').replace('\n', '<br>')
        
        data_list.append({
            'compliment_id': obj.compliment_id,
            'praise_id': obj.praise_id,
            'user_id': obj.user_id,
            'user_employee_name': obj.user_employee_name,
            'image_path': obj.image_path,
            'compliment_type': obj.compliment_type,
            'content': escape(content),
            'images_id': obj.images_id,
            'short_content': obj.short_content,
            'tag': escape(obj.tag),
            'emotion_ratio': obj.emotion_ratio,
            'view_count': obj.view_count,
            'comment_count': obj.comment_count,
            'likes_count': obj.likes_count,
            'token_id': obj.token_id,
            'is_active': obj.is_active,
            'chg_date': chg_date_str,
            'reg_date': reg_date_str,
            'user_image_yn': obj.user_image_yn,
            'user_image': obj.user_image,
            'user_employee_id': obj.user_employee_id,
            'user_department_name': obj.user_department_name,
            'user_position_name': obj.user_position_name,
            'user_company_name': obj.user_company_name,
            'praise_image': obj.praise_image,
            'praise_image_yn': obj.praise_image_yn,
            'praise_employee_id': obj.praise_employee_id,
            'praise_employee_name': obj.praise_employee_name,
            'praise_department_name': obj.praise_department_name,
            'praise_position_name': obj.praise_position_name,
            'praise_company_name': obj.praise_company_name,
            'like_yn': obj.like_yn,
            'post_date': post_date
        })
    
    # Return response
    return HttpResponse(
        json.dumps({
            'status': '200',
            'data_count': len(data_list),
            'data_list': data_list,
        }),
        content_type="application/json"
    )

@csrf_exempt
@measure_execution_time
def praise_page(request):
    #print('### [API] praise_page ####################################################')
    
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':        
        #for key, value in request.POST.items():
        #    print('### [INPUT] ', key, value)
            
        user_id = request.POST['input_search']
        # request.POST.get('pageNumber')    
        page_number = request.POST.get('pageNumber')    
        page_number = int(page_number)
        #-------------
        # 업무로직
        #-------------
        result = UserLike.objects.filter(
            user_id = request.user.id,
            is_active = 'Y',
        ).values_list('compliment_id', flat=True)
        
        #-------------
        # 2024-12-17: Add a filter condition for user search to the `praise_page` API.
        #-------------
        selectUserPraise = UserPraise.objects.filter(is_active='Y')

        if user_id:
            selectUser = User2.objects.filter(
                    id=user_id,
                    is_active=True
                ).order_by('-reg_date')\
                .values_list('id', flat=True)
            
            selectUserPraise = UserPraise.objects.filter(
                Q(praise_id__in=selectUser.values_list('id', flat=True))|
                Q(user_id__in=selectUser.values_list('id', flat=True)),
                is_active='Y'
            )
        
        selectUserPraise = selectUserPraise.select_related('praise', 'images').annotate(
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
                #compliment_id_COUNT=Count('usercomment__compliment_id', filter=Q(usercomment__compliment_id__is_active='Y'))
            ).order_by('-reg_date')[page_number * 10:(page_number + 1) * 10]

        #print('### compliment_id_COUNT', compliment_id_COUNT)

        #for row in selectUserPraise.values():
        #    print(row)

        # 데이터를 담을 리스트 초기화
        data_list = []

        # 필드별 데이터를 리스트에 담습니다.
        for obj in selectUserPraise:
            if obj.chg_date is not None:
                chg_date_str = obj.chg_date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                chg_date_str = None

            if obj.reg_date is not None:
                reg_date_str = obj.reg_date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                reg_date_str = None
                
            # obj.reg_date는 DB에서 가져온 날짜 값입니다
            post_date = humanize.naturaltime(obj.reg_date)              
            #print('[API][LOG] formatted_date', formatted_date)
            
            chg_content = obj.content 
            chg_content = chg_content.replace('\r\n', '<br>')
            chg_content = chg_content.replace('\r\n', '<br>')
            chg_content = chg_content.replace('\r', '<br>')
            chg_content = chg_content.replace('\n', '<br>')
            #print('[VIEW][LOG] chg_content ', chg_content)
            
            data_list.append({
                'compliment_id': obj.compliment_id,
                'praise_id': obj.praise_id,
                'user_id': obj.user_id,
                'user_employee_name': obj.user_employee_name,
                'image_path': obj.image_path,
                'compliment_type': obj.compliment_type,
                'content': escape(chg_content),
                'images_id': obj.images_id,
                'short_content': obj.short_content,
                'tag': escape(obj.tag),
                'emotion_ratio': obj.emotion_ratio,
                'view_count': obj.view_count,
                'comment_count': obj.comment_count,
                'likes_count': obj.likes_count,
                'token_id': obj.token_id,
                'is_active': obj.is_active,
                'chg_date': chg_date_str,
                'reg_date': reg_date_str,
                'user_image_yn' : obj.user_image_yn,
                'user_image' : obj.user_image,
                'user_employee_id' : obj.user_employee_id,
                'user_department_name' : obj.user_department_name,
                'user_position_name' : obj.user_position_name,
                'user_company_name' : obj.user_company_name,
                'praise_image' : obj.praise_image,
                'praise_image_yn' : obj.praise_image_yn,
                'praise_employee_id' : obj.praise_employee_id,
                'praise_employee_name' : obj.praise_employee_name,
                'praise_department_name' : obj.praise_department_name,
                'praise_position_name' : obj.praise_position_name,
                'praise_company_name' : obj.praise_company_name,
                'like_yn' : obj.like_yn,
                'post_date': post_date
                
                
            })
                
        #-------------
        # 출력내용 SET
        #-------------
        # 결과 데이터에 리스트와 총 건수를 추가합니다.
        ResultData = {
            'status': '200',
            'data_count': len(data_list),
            'data_list': data_list,
        }

        # json으로 변환
        json_data = json.dumps(ResultData)
        #print("### [OUTPUT] JSON = ",json_data)   

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
    #print("### [OUTPUT] JSON = ",json_data)   
    
    return HttpResponse(json_data, content_type="application/json") 

@csrf_exempt
def praise_detail(request):
    print('### [API] praise_detail ####################################################')
    
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':        
        for key, value in request.POST.items():
            print('### [INPUT] ', key, value)
            
        #-------------
        # 업무로직
        #-------------
        if request.POST['compliment_id']:
            try:   
                
                compliment_id = request.POST.get('compliment_id')

                print('### compliment_id = ', compliment_id)
                
                selectUserPraise = UserPraise.objects.filter(pk=compliment_id, is_active='Y').prefetch_related('praise', 'images').annotate(
                    praise_employee_name=F('praise__employee_name'),
                    user_employee_name=F('user__employee_name'),
                    image_path=F('images__image_path')
                ).first()
                
                print('### selectUserPraise')
                
                #for row in selectUserPraise.values():
                #    print(row)
                
                
                #-------------
                # view 건수증가
                #-------------
                updateUserPraise = UserPraise.objects.get(compliment_id=compliment_id)
                updateUserPraise.view_count += 1
                updateUserPraise.save() 
                print('### updateUserPraise ')
                

                #-------------
                # 출력내용 SET
                #-------------
                # chg_date와 reg_date의 값을 문자열로 변환하여 ResultData에 추가
                if selectUserPraise.chg_date is not None:
                    chg_date_str = selectUserPraise.chg_date.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    chg_date_str = None

                if selectUserPraise.reg_date is not None:
                    reg_date_str = selectUserPraise.reg_date.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    reg_date_str = None
                    
                ResultData = {
                    'status': '200',
                    'compliment_id': selectUserPraise.compliment_id,
                    'praise_id': selectUserPraise.praise_id,
                    'user_id': selectUserPraise.user_id,
                    'praise_employee_name': selectUserPraise.praise_employee_name,
                    'user_employee_name': selectUserPraise.user_employee_name,
                    'image_path': selectUserPraise.image_path,
                    'compliment_type': selectUserPraise.compliment_type,
                    'content': selectUserPraise.content,
                    'images_id': selectUserPraise.images_id,
                    'short_content': selectUserPraise.short_content,
                    'tag': selectUserPraise.tag,
                    'emotion_ratio': selectUserPraise.emotion_ratio,
                    'view_count': selectUserPraise.view_count,
                    'comment_count': selectUserPraise.comment_count,
                    'likes_count': selectUserPraise.likes_count,
                    'token_id': selectUserPraise.token_id,
                    'is_active': selectUserPraise.is_active,
                    'chg_date': chg_date_str,
                    'reg_date': reg_date_str
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                #print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 
    
            except:
                ResultData = {
                    'status' : '402',
                    'error' : 'DB적재시 오류가 발생 했습니다.'
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 
        else:
            ResultData = {
                'status' : '401',
                'error' : '입력 데이터가 없습니다.'
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

def save_image(file, path):
    print('### save_image ####################################################')
    
    # 이미지 로드
    image = Image.open(file)

    # 이미지 사이즈 변경 (예시: 800x600)
    size = (800, 600)
    image = image.resize(size, Image.ANTIALIAS)

    # 이미지 화질 조정 (60%)
    quality = 40

    # 디렉토리 생성
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # 이미지 저장
    image.save(path, optimize=True, quality=quality)

    return path

@csrf_exempt
def praise_regedit(request):
    print('### [API] praise_regedit ####################################################')
    
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':        
        for key, value in request.POST.items():
            print('### [INPUT] ', key, value)
            
        # 등록자 사용가능한 토큰 개수 검증
        current_date = datetime.date.today()
        quarter = (current_date.month - 1) // 3 + 1
        if quarter == '1':
            sta_month = '01'
            end_month = '03'
        elif quarter == '2':
            sta_month = '04'
            end_month = '06'
        elif quarter == '3':
            sta_month = '07'
            end_month = '09'
        else :
            sta_month = '10'
            end_month = '12'
            
        print('### praise_regedit 함수 분기, 조회월 출력',quarter,sta_month,end_month)
            
        #UserPraise.objects.filter(id=request.user.id, is_active='Y')
        
        #-------------
        # 업무로직
        #-------------
        if request.POST['content']:
            try:                
                #------------------------------------------------
                # DB UPDATE
                #------------------------------------------------
                insertUserPraise = UserPraise()
                insertUserPraise.praise_id        = request.POST['praise_id']
                insertUserPraise.user_id          = request.user.id
                insertUserPraise.compliment_type  = request.POST['compliment_type']                
                insertUserPraise.content          = request.POST['content']
                
                insertUserPraise.images_id        = request.POST['images_id']
                
                insertUserPraise.short_content    = '' # open ai 응답
                insertUserPraise.tag              = '' # open ai 응답
                insertUserPraise.emotion_ratio    = '' # open ai 응답
                                    
                insertUserPraise.view_count       = 0
                insertUserPraise.comment_count    = 0
                insertUserPraise.likes_count      = 0
                #insertUserPraise.token_id      = 0
                
                if 'is_active' in request.POST and request.POST['is_active'] in ['on', 'Y']:
                    insertUserPraise.is_active = 'Y'
                else:
                    insertUserPraise.is_active = 'N'
                    
                print('insertUserPraise.praise_id       ', insertUserPraise.praise_id)
                print('insertUserPraise.user_id         ', insertUserPraise.user_id)
                print('insertUserPraise.compliment_type ', insertUserPraise.compliment_type)
                print('insertUserPraise.content         ', insertUserPraise.content)
                
                insertUserPraise.reg_date = datetime.now()       
                insertUserPraise.save()
                print('insertUserPraise.compliment_id   ', insertUserPraise.compliment_id)

                #-------------
                # 출력내용 SET
                #-------------
                ResultData = {
                    'status' : '200',
                    'compliment_id' : insertUserPraise.compliment_id,
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 
            
            except:
                ResultData = {
                    'status' : '402',
                    'error' : 'DB적재시 오류가 발생 했습니다.'
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 
        else:
            ResultData = {
                'status' : '401',
                'error' : '입력 데이터가 없습니다.'
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
def praise_modify(request):
    print('### [API] praise_modify ####################################################')
    
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':        
        for key, value in request.POST.items():
            print('### [INPUT] ', key, value)
            
        #-------------
        # 업무로직
        #-------------
        if request.POST['compliment_id']:
            
            try:
                compliment_id = request.POST['compliment_id']

                updateUserPraise = UserPraise.objects.get(compliment_id=compliment_id) 

                #------------------------------------------------
                # 이미지 파일 업로드
                #------------------------------------------------
                # 태그없는 원본 글값
                #inputData= request.POST['input_Contents_text']
                    
                # 등록직원
                selectUser1 = User2.objects.get(id=updateUserPraise.praise_id)
                sendUser = selectUser1.employee_name

                # 칭찬직원
                selectUser2 = User2.objects.get(id=updateUserPraise.user_id)
                recvUser = selectUser2.employee_name
                
                #updateUserPraise.org_content  = inputData 
                
                #------------------------------------------------
                # DB UPDATE
                #------------------------------------------------
                #if 'praise_id' in request.POST:
                #    updateUserPraise.praise_id = request.POST['praise_id']
                
                if 'compliment_type' in request.POST:
                    updateUserPraise.compliment_type = request.POST['compliment_type']

                if 'content' in request.POST:
                    updateUserPraise.content      = request.POST['content']
                    updateUserPraise.org_content  = request.POST['content']
                    
                    try:

                        #print("### [API] praise Modify openAI call #########################")
                        # ------------------------------------------------------------------
                        # openAI call
                        # ------------------------------------------------------------------
                        # 칭찬글
                        inputData = request.POST['content']
                        
                        # 등록직원
                        selectUser1 = User2.objects.get(id=updateUserPraise.user_id)
                        sendUser = selectUser1.employee_name

                        # 칭찬직원
                        selectUser2 = User2.objects.get(id=updateUserPraise.praise_id)
                        recvUser = selectUser2.employee_name
                        
                        #------------------------------------------------------------------
                        # openAI call (ChatGPT 2023-11-01)
                        #------------------------------------------------------------------
                        def call_openAi_GPT ():
                            outputJson = openAi_Short(inputData, sendUser, recvUser)
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

                            #단어 추출 TTT
                            #okt = Okt()
                            tag_words = [word for word in okt.nouns(text) if word not in exclude_words][:3]
                            tag       = {'tag': tag_words}

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
                                    # summarizer = Summarizer()

                                    # 텍스트 요약
                                    #short_content = summarizer(text)
                                    short_content = '' # 수정건은 요약하지 않음

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
                        updateUserPraise.short_content  = short_content
                        updateUserPraise.tag            = tag
                        #updateUserPraise.emotion_ratio  = emotion_ratio  

                    except:

                        #-------------
                        # 오류내용 SET
                        #-------------
                        print("### [API][LOG][ERROR openAi] 칭찬글 분석시 오류가 발생 했습니다.")
                        #print("에러 메시지:", str(e))

                        #-------------
                        # ERROR DB Update
                        #-------------
                        updateUserPraise = UserPraise.objects.get(compliment_id=insertUserPraise.compliment_id) 
                        updateUserPraise.short_content  = '시스템 확인 중 입니다.'
                        updateUserPraise.tag            = {'tag': ['확인중']}
                        #updateUserPraise.emotion_ratio  = ''
                    
                
                if 'images_id' in request.POST:
                    updateUserPraise.images_id = request.POST['images_id']

                if 'is_active' in request.POST:
                    if request.POST['is_active'] in ['on', 'Y']:
                        updateUserPraise.is_active = 'Y'
                    else:
                        updateUserPraise.is_active = 'N'

                updateUserPraise.chg_date = datetime.now()    
                updateUserPraise.save()

                #-------------
                # 출력내용 SET
                #-------------
                selectUserPraise = UserPraise.objects.filter(pk=compliment_id, is_active='Y').prefetch_related('praise', 'images').annotate(
                    praise_employee_name=F('praise__employee_name'),
                    user_employee_name=F('user__employee_name'),
                    image_path=F('images__image_path'),
                    praise_image_yn=F('praise__image_yn'),
                    praise_image=F('praise__image'),
                    user_image_yn=F('user__image_yn'),
                    user_image=F('user__image')
                ).first()
                
                # chg_date와 reg_date의 값을 문자열로 변환하여 ResultData에 추가
                if selectUserPraise.chg_date is not None:
                    chg_date_str = selectUserPraise.chg_date.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    chg_date_str = None

                if selectUserPraise.reg_date is not None:
                    reg_date_str = selectUserPraise.reg_date.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    reg_date_str = None
                    
                selectUserPraise.content  = selectUserPraise.content.replace('\r\n', '<br>')
                selectUserPraise.content  = selectUserPraise.content.replace('\r\n', '<br>')
                selectUserPraise.content  = selectUserPraise.content.replace('\r', '<br>')
                selectUserPraise.content  = selectUserPraise.content.replace('\n', '<br>')
                    
                ResultData = {
                    'status': '200',
                    'compliment_id': selectUserPraise.compliment_id,
                    'praise_id': selectUserPraise.praise_id,
                    'user_id': selectUserPraise.user_id,
                    'praise_employee_name': selectUserPraise.praise_employee_name,
                    'user_employee_name': selectUserPraise.user_employee_name,
                    'image_path': selectUserPraise.image_path,
                    'compliment_type': selectUserPraise.compliment_type,
                    'content': selectUserPraise.content,
                    'images_id': selectUserPraise.images_id,
                    'short_content': selectUserPraise.short_content,
                    'tag': selectUserPraise.tag,
                    'emotion_ratio': selectUserPraise.emotion_ratio,
                    'view_count': selectUserPraise.view_count,
                    'comment_count': selectUserPraise.comment_count,
                    'likes_count': selectUserPraise.likes_count,
                    'token_id': selectUserPraise.token_id,
                    'is_active': selectUserPraise.is_active,
                    'chg_date': chg_date_str,
                    'reg_date': reg_date_str,
                    'praise_image_yn': selectUserPraise.praise_image_yn,
                    'praise_image': selectUserPraise.praise_image,
                    'user_image_yn': selectUserPraise.user_image_yn,
                    'user_image': selectUserPraise.user_image

                    
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 

            except:
                ResultData = {
                    'status' : '403',
                    'error' : 'DB 갱신시 오류가 발생 했습니다.'
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                #print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 
            
        else:
            ResultData = {
                'status' : '401',
                'error' : '입력 데이터가 없습니다.'
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
def praise_comment_list(request):
    print('### [API] praise_comment_list ####################################################')
    
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':        
        for key, value in request.POST.items():
            print('### [INPUT] ', key, value)
            
        compliment_id = request.POST['compliment_id']
        
        #-------------
        # 업무로직 ttt
        #-------------
        #print('### 1', compliment_id)
        selectUserComment = UserComment.objects.filter(compliment_id = compliment_id, is_active='Y')\
                        .select_related('user')\
                        .order_by('-comment_id')
    

        # 데이터를 담을 리스트 초기화
        data_list = []
        
        # 필드별 데이터를 리스트에 담습니다.
        for obj in selectUserComment:

            if obj.chg_date is not None:
                chg_date_str = obj.chg_date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                chg_date_str = None

            if obj.reg_date is not None:
                reg_date_str = obj.reg_date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                reg_date_str = None

            data_list.append({
                'comment_id': obj.comment_id,
                'compliment_id': obj.compliment_id,
                'comment_content': obj.comment_content,
                'user_id': obj.user_id,
                'image_yn': obj.user.image_yn,
                'image': obj.user.image,
                'employee_id': obj.employee_id,
                'user_employee_name': obj.user.employee_name,
                'is_active': obj.is_active,
                'chg_date': chg_date_str,
                'reg_date': reg_date_str,
            })

        #-------------
        # 출력내용 SET
        #-------------
        ResultData = {
            'status' : '200',
            'data_count': len(data_list),
            'data_list': data_list,
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
def praise_comment_regedit(request):
    print('### [API] praise_comment_regedit ####################################################')
    
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':        
        for key, value in request.POST.items():
            print('### [INPUT] ', key, value)

        #-------------
        # 업무로직
        #-------------
        if request.POST['comment_content']:
            try:
                
                #------------------------------------------------
                # 댓글 max일련번호 가져오기
                #------------------------------------------------
                compliment_id = request.POST['compliment_id']

                result = UserComment.objects.filter(compliment_id=compliment_id).aggregate(Max('comment_id'))
                
                # 결과 값이 None이면 0 할당
                comment_id_max = result['comment_id__max'] or 0
                
                print('insertUserComment.comment_id_max      ', comment_id_max)
                
                #------------------------------------------------
                # DB INSERT
                #------------------------------------------------
                insertUserComment = UserComment()
                insertUserComment.comment_id       = comment_id_max+1
                insertUserComment.compliment_id    = compliment_id
                insertUserComment.comment_content  = request.POST['comment_content']                
                insertUserComment.user_id          = request.user.id         
                insertUserComment.employee_id      = request.POST['employee_id']
                
                if 'is_active' in request.POST and request.POST['is_active'] in ['on', 'Y']:
                    insertUserComment.is_active = 'Y'
                else:
                    insertUserComment.is_active = 'N'
                    
                print('insertUserComment.comment_id      ', insertUserComment.comment_id)
                print('insertUserComment.user_id         ', insertUserComment.user_id)
                print('insertUserComment.comment_content ', insertUserComment.comment_content)
                
                insertUserComment.reg_date = datetime.now()       
                insertUserComment.save()
                print('insertUserComment.compliment_id   ', insertUserComment.compliment_id)

                # 칭찬테이블 update 문 실행
                updateUserPraise = UserPraise.objects.get(compliment_id=compliment_id)
                updateUserPraise.comment_count += 1
                updateUserPraise.save() 
                
                #-------------
                # 출력내용 SET
                #-------------
                ResultData = {
                    'status' : '200',
                    'compliment_id' : insertUserComment.compliment_id,
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 
            
            except:
                ResultData = {
                    'status' : '402',
                    'error' : 'DB적재시 오류가 발생 했습니다.'
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 
        else:
            ResultData = {
                'status' : '401',
                'error' : '입력 데이터가 없습니다.'
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
def praise_comment_modify(request):
    print('### [API] praise_comment_modify ####################################################')
    
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':        
        for key, value in request.POST.items():
            print('### [INPUT] ', key, value)

        #-------------
        # 업무로직
        #-------------
        if 'compliment_id' in request.POST and 'comment_id' in request.POST:
        
            try:
                compliment_id = request.POST['compliment_id']
                comment_id = request.POST['comment_id']    

                updateUserComment = UserComment.objects.get(compliment_id=compliment_id,comment_id=comment_id)

                #------------------------------------------------
                # DB UPDATE
                #------------------------------------------------
                if 'comment_content' in request.POST:
                    updateUserComment.comment_content = request.POST['comment_content']
                    
                if 'is_active' in request.POST:
                    if request.POST['is_active'] in ['on', 'Y']:
                        updateUserComment.is_active = 'Y'
                    else:
                        updateUserComment.is_active = 'N'
                    
                    
                updateUserComment.chg_date = datetime.now()    
                updateUserComment.save()

                # 칭찬테이블 update 문 실행
                updateUserPraise = UserPraise.objects.get(compliment_id=compliment_id)
                updateUserPraise.save() 
                
                #-------------
                # 출력내용 SET
                #-------------
                ResultData = {
                    'status' : '200',
                    'compliment_id' : updateUserComment.compliment_id,
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 

            except:
                ResultData = {
                    'status' : '403',
                    'error' : 'DB 갱신시 오류가 발생 했습니다.'
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 
            
        else:
            ResultData = {
                'status' : '401',
                'error' : '입력 데이터가 없습니다.'
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
def praise_comment_delete(request):
    print('### [API] praise_comment_delete ####################################################')
    
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':        
        for key, value in request.POST.items():
            print('### [INPUT] ', key, value)
            
       #-------------
        # 업무로직
        #-------------
        if 'compliment_id' in request.POST and 'comment_id' in request.POST:
        
            try:
                compliment_id = request.POST['compliment_id']
                comment_id = request.POST['comment_id']    

                updateUserComment = UserComment.objects.filter(compliment_id=compliment_id,comment_id=comment_id,is_active='Y')
                
                if updateUserComment.exists():
                    #------------------------------------------------
                    # DB UPDATE
                    #------------------------------------------------
                    # 쿼리셋 결과의 is_active 값을 'N'으로 변경하기
                    updateUserComment.update(is_active='N')
                    # 쿼리셋 결과의 chg_date 값을 현재 시간으로 변경하기
                    updateUserComment.update(chg_date=datetime.now())

                    # 쿼리셋을 저장하기
                    #updateUserComment.save()
                    
                    # 칭찬테이블 update 문 실행
                    updateUserPraise = UserPraise.objects.get(compliment_id=compliment_id)

                    print('### 11 updateUserPraise.comment_count', updateUserPraise.comment_count)
                    updateUserPraise.comment_count -= 1
                    print('### 22 updateUserPraise.comment_count', updateUserPraise.comment_count)

                    updateUserPraise.save() 
        
                #-------------
                # 출력내용 SET1
                #-------------
                ResultData = {
                    'status' : '200',
                    'compliment_id' : updateUserComment.compliment_id,
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 

            except:
                ResultData = {
                    'status' : '403',
                    'error' : 'DB 갱신시 오류가 발생 했습니다.'
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 
            
        else:
            ResultData = {
                'status' : '401',
                'error' : '입력 데이터가 없습니다.'
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
def praise_card(request):
    print('### [API] praise_card ####################################################')
    
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':        
        for key, value in request.POST.items():
            print('### [INPUT] ', key, value)
            
        #-------------
        # 업무로직
        #-------------
        selectUserImages = UserImages.objects.filter(is_open='Y', is_active='Y').order_by('-reg_date')

        # 데이터를 담을 리스트 초기화
        data_list = []

        # 필드별 데이터를 리스트에 담습니다.
        for obj in selectUserImages:
                    
            data_list.append({
                'id': obj.id,
                'image_name': obj.image_name,
                'image_path': obj.image_path,
                'is_active': obj.is_active,
            })
        
        #-------------
        # 출력내용 SET
        #-------------
        # 결과 데이터에 리스트와 총 건수를 추가합니다.
        ResultData = {
            'status': '200',
            'data_count': len(data_list),
            'data_list': data_list,
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
def praise_member(request):
    #print('### [API] praise_member ####################################################')
    
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':        
        #for key, value in request.POST.items():
        #    print('### [INPUT] ', key, value)
            
        #-------------
        # 업무로직
        #-------------
        if request.POST['employee_name']:
            
            try:
                employee_name = request.POST['employee_name']
                
                #답장 2024.01
                employee_name = request.POST['employee_name']
                print('### request Post 답장 ', request.POST)
                if request.POST['id']:
                    user_chk_id = request.POST['id']
                    print('### request user_chk_id 답장 ', user_chk_id)
                    if user_chk_id == '0': #나의토큰에서 답장
                        selectUser = User2.objects.filter(
                            Q(employee_name__icontains=employee_name),
                            is_active=True,
                            ty=True,
                            department_name__isnull=False,
                            department_id__isnull=False,
                        ).exclude(id=request.user.id).order_by('employee_name')
                    
                    elif user_chk_id == '-7': #base.html에서 검색시에 자기 이름으로도 검색
                        selectUser = User2.objects.filter(
                            Q(employee_name__icontains=employee_name),
                            is_active=True,
                            ty=True,
                            department_name__isnull=False,
                            department_id__isnull=False,
                        ).order_by('employee_name')

                    else:
                        selectUser = User2.objects.filter(
                            id = user_chk_id,
                            is_active=True,
                            ty=True,
                            department_name__isnull=False,
                            department_id__isnull=False,
                        ).exclude(id=request.user.id).order_by('employee_name')

                
                else:

                    #소속장 이상 제외 직위셋
                    #reward_skip_users = ManagePosi.objects.filter(reward_skip_yn='Y').values_list('posi_id', flat=True)

                    selectUser = User2.objects.filter(
                        Q(employee_name__icontains=employee_name),
                        is_active=True,
                        ty=True,
                        department_name__isnull=False,
                        department_id__isnull=False,
                    ).exclude(id=request.user.id).order_by('employee_name')



                #for user in selectUser:
                #    print(user.employee_name, user.position_id, user.company_id)

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

                # Now you can access the reward_skip_yn field in your queryset
                #for user in selectUser:
                #    print(user.employee_name, user.position_name, user.reward_skip_yn)

                # 데이터를 담을 리스트 초기화
                data_list = []

                # 필드별 데이터를 리스트에 담습니다.
                for obj in selectUser:

                    data_list.append({
                        'id': obj.id,
                        'ty': obj.ty,
                        'employee_id': obj.employee_id,
                        'employee_name': obj.employee_name,
                        'department_name': obj.department_name,
                        'positon_name': obj.position_name,
                        'company_name': obj.company_name,
                        'image_yn': obj.image_yn,
                        'image': obj.image,                
                        'reward_skip_yn': obj.reward_skip_yn,                  
                    })

                msg = '대상직원이 없습니다.'
                if employee_name == request.user.employee_name:    
                    msg = '본인은 검색할 수 없습니다.'
                    
                    
                if not selectUser:
                    data_list.append({                        
                        'id': None,
                        'ty': None,
                        'employee_id': None,
                        'employee_name': msg,
                        'department_name': '[결과]',
                        'positon_name': '',
                        'company_name': '',
                        'image_yn': None,
                        'image': None,  
                        'reward_skip_yn': '',  
                    })
                    
                #-------------
                # 출력내용 SET
                #-------------
                # 결과 데이터에 리스트와 총 건수를 추가합니다.
                ResultData = {
                    'status': '200',
                    'data_count': len(data_list),
                    'data_list': data_list,
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                #print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 

    
            except:
                ResultData = {
                    'status' : '403',
                    'error' : 'DB 갱신시 오류가 발생 했습니다.'
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 
            
        else:
            ResultData = {
                'status' : '401',
                'error' : '입력 데이터가 없습니다.'
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
def praise_check(request):
    print('### [API] praise_check ####################################################')
    
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':        
        #for key, value in request.POST.items():
        #    print('### [INPUT] ', key, value)
            
        #-------------
        # 업무로직
        #-------------
        if request.POST['employee_id']:
            
            try:
                praise_id = request.POST['employee_id']

                # 토큰정보
                today = datetime.now().strftime('%Y%m%d')
                selectManageTokens = ManageTokens.objects.filter(
                    Q(start_date__lte=today) & Q(end_date__gte=today)
                ).first()
                
                selectTotalCount = UserPraise.objects.filter(
                    ~Q(is_senduc='Y'),
                    is_active='Y', 
                    token_id = selectManageTokens.id,
                    user_id = request.user.id,
                    praise_id = praise_id
                ).aggregate(praise_count=Count('praise_id'))
                
                if selectTotalCount:
                    praise_count = selectTotalCount['praise_count']
                else:
                    praise_count = "0"
                print('### [API][LOG] praise_count', praise_count)
                
                selectUser = User2.objects.filter(
                    id = praise_id
                ).first()

                print('### [API][LOG] selectUser', selectUser.position_id)
                # ManagePosi 모델의 reward_skip_yn을 selectUser 객체에 추가
                selectManagePosi = ManagePosi.objects.filter(
                    company_id=selectUser.company_id,
                    posi_id=selectUser.position_id
                ).first()
                
                if selectManagePosi:
                    reward_skip_yn = selectManagePosi.reward_skip_yn
                else:
                    reward_skip_yn = "N"
                print('### [API][LOG] reward_skip_yn',reward_skip_yn)
                #print('selectTotalCount count', selectTotalCount['praise_count'])

                # 데이터를 담을 리스트 초기화
                data_list = []

                # 필드별 데이터를 리스트에 담습니다.
                #for obj in selectTotalCount:
                #
                #    data_list.append({
                #        'user_id': obj.user_id,
                #        'praise_id': obj.praise_id,
                #        'praise_count': obj.praise_count 
                #    })
                    
                data_list.append({
                    'user_id': request.user.id,
                    'praise_id': praise_id,
                    'praise_count': praise_count,
                    'reward_skip_yn': reward_skip_yn,
                })
                    
                #-------------
                # 출력내용 SET
                #-------------
                # 결과 데이터에 리스트와 총 건수를 추가합니다.
                ResultData = {
                    'status': '200',
                    'data_count': len(data_list),
                    'data_list': data_list,
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                #print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 

    
            except:
                ResultData = {
                    'status' : '403',
                    'error' : 'DB 갱신시 오류가 발생 했습니다.'
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 
            
        else:
            ResultData = {
                'status' : '401',
                'error' : '입력 데이터가 없습니다.'
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
def myprofile_notice(request):
    #print('### [API] myprofile_notice ####################################################')
    
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':        
        #for key, value in request.POST.items():
        #    print('### [INPUT] ', key, value)
            
        #---------------------    
        # 1:SELECT, 2:UPDATE
        #---------------------
        if 'notice_check' in request.POST and request.POST['notice_check'] in ['Y']:    
            updateUserNotices = UserNotices.objects.get(notice_id=request.POST['notice_id'])
            updateUserNotices.check_yn = 'Y'
            updateUserNotices.save() 
            
        #-------------
        # 업무로직
        #-------------
        if request.POST['notice_type'] in ['3']:
            selectUserNotices = UserNotices.objects.filter(
                    user_id=request.user.id, is_active='Y'
                ).select_related('send').order_by('-reg_date')
        else :
            selectUserNotices = UserNotices.objects.filter(
                    user_id=request.user.id, check_yn='N', is_active='Y'
                ).select_related('send').order_by('-reg_date')
        
        selectTotCount = UserNotices.objects.filter(
                    user_id=request.user.id, check_yn='N', is_active='Y')
        
        # 데이터를 담을 리스트 초기화
        data_list = []

        # 필드별 데이터를 리스트에 담습니다.
        for obj in selectUserNotices:
            if obj.reg_date is not None:
                reg_date_str = obj.reg_date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                reg_date_str = None
                    
            data_list.append({
                'department_name': obj.send.department_name,
                'employee_name': obj.send.employee_name,
                'position_name': obj.send.position_name,
                'company_name': obj.send.company_name,
                'image_yn': obj.send.image_yn,
                'image': obj.send.image,
                'notice_id': obj.notice_id,
                'user_id': obj.user_id,
                'notice_type': obj.notice_type,
                'compliment_id': obj.compliment_id,
                'comment_id': obj.comment_id,
                'check_yn': obj.check_yn,
                'reg_date': reg_date_str,
            })
        
        #-------------
        # 출력내용 SET
        #-------------
        # 결과 데이터에 리스트와 총 건수를 추가합니다.
        ResultData = {
            'status': '200',
            'data_count': len(data_list),
            'data_list': data_list,
            'count': selectTotCount.count()
        }

        # json으로 변환
        json_data = json.dumps(ResultData)
        #print("### [OUTPUT] JSON = ",json_data)   

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
    #print("### [OUTPUT] JSON = ",json_data)   
    
    return HttpResponse(json_data, content_type="application/json") 


@csrf_exempt
def myprofile_info(request):
    print('### [API] myprofile_info ####################################################')
    
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':        
        for key, value in request.POST.items():
            print('### [INPUT] ', key, value)
            
        #-------------
        # 업무로직
        #-------------
        if request.POST['id']:
            
            try:
                member_id = request.POST['id']
                selectUser = User2.objects.filter(id=member_id)
                
                # 데이터를 담을 리스트 초기화
                data_list = []

                # 필드별 데이터를 리스트에 담습니다.
                for obj in selectUser:
                    data_list.append({
                        'id': obj.id,
                        'ty': obj.ty,
                        'employee_id': obj.employee_id,
                        'employee_name': obj.employee_name,
                        'department_name': obj.department_name,
                        'image_yn': obj.image_yn,
                        'image': obj.image,                
                    })
                                
                #-------------
                # 출력내용 SET
                #-------------
                # 결과 데이터에 리스트와 총 건수를 추가합니다.
                ResultData = {
                    'status': '200',
                    'data_count': len(data_list),
                    'data_list': data_list,
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 

    
            except:
                ResultData = {
                    'status' : '403',
                    'error' : 'DB 갱신시 오류가 발생 했습니다.'
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 
            
        else:
            ResultData = {
                'status' : '401',
                'error' : '입력 데이터가 없습니다.'
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

def openAi(data_list, employee_name):
    print("### [MODULE] openAi ")
    
    praiseText = data_list
    print('### [MODULE][LOG] employee_name', employee_name)
    #print('praiseText ### ', data_list)
    headers={"Authorization":"Bearer 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","Content-Type":"application/json"}
    link="https://api.openai.com/v1/chat/completions"

    temp=[        
        {"role": "system", "content": "assistant는 여러개의 칭찬글을 쉽고 간략하게 대답해주는 앵커 입니다."},
        {"role": "user", "content": f"""
		아래에 칭찬글은 한명에게 보낸 리스트 입니다. 칭찬리스트의 순서 상관없이 재미있는 내용으로 필요한 내용만 추출해서 글을 작성해 주세요.
        입력받은 데이터 중 이모티콘과 특수문자는 출력으로 받지 않습니다. 답변은 반드시 JSON 으로만 주세요. 
        1. JSON 답변형식은 = [ 'summary' : [답변내용] ]  2. 칭찬 주인공은 {employee_name} 입니다  3. 칭찬글 = {praiseText}
        
        2023-07-21
        재미있는 단편 시를 작성해 주세요. 
        아래의 칭찬글에서 주요태그만 추출해서 필요한 키워드만 적절하게 사용해 주세요.
        
        
        칭찬글의 내용을 잘 살펴보세요. 어떤 칭찬글이 가장 마음에 드시나요? 그 칭찬글을 중심으로 스토리를 만들어 보세요.
        스토리는 재미있고 독창적이어야 합니다. 칭찬글의 내용을 바탕으로 웃긴 이야기나 신기한 이야기, 감동적인 이야기를 만들어 보세요.
        스토리는 칭찬글을 받는 사람의 성격이나 특징을 반영해야 합니다. 그 사람의 취향이나 관심사, 성격을 고려해서 스토리를 만들어 보세요.
        답변내용은 간결한 내용으로 서론,본론,결론 식의 순서로 작성해 주시고 해당 단어는 제외해 주세요.
        
	 """}
    ]    
    messages=[        
        {"role": "system", "content": "assistant는 회사 칭찬글을 작성하는 담당자 입니다."},
        {"role": "user", "content": f"""
        칭찬 주인공은 '{employee_name}' 입니다. 직원들의 칭찬글 내용을 잘 살펴보세요. 
        어떤 칭찬글이 가장 마음에 드시나요? 그 칭찬글을 중심으로 스토리를 만들어 보세요.
        
        1) 스토리는 재미있고 독창적이어야 합니다. 
        2) 칭찬글의 내용을 바탕으로 감동적인 이야기로 새롭게 창작해서 답변 주세요.
        3) 선정된 칭찬글에 대한 언급은 없습니다. 
        4) 그의 또는 그녀의 지칭어는 사용하지 않습니다. 
        5) 이모티콘, 특수문자(따음표, 콤마), 초성은 답변에 사용하지 않습니다. 
        6) 제목은 없습니다.
        7) 답변은 500자 이내로 작성해죠 
        
        칭찬글 = {praiseText}
        
	 """}
    ]
    
    data={"model": "gpt-4", "messages": messages, "temperature": 0.8, "max_tokens": 1500}
    
    print("### [MODULE][LOG] openAi messages ", messages)
    
    response=requests.post(link,data=json.dumps(data),headers=headers)
    
    print("### [MODULE][LOG] response : ", response)
    print("### [MODULE][LOG] Response status code: ", response.status_code)
    print("### [MODULE][LOG] Response content: ", response.json())
    
    message = response.json()['choices'][0]['message']['content']   
    
    print("### [MODULE][LOG] Response message : ", message)
    
    json_data = message
    
    # json 형태의 문자열 추출
    #json_text = message[message.find("{"):message.rfind("}")+1]

    # json으로 변환
    #json_data = json.loads(json_text)
        
    #print("### openAi json_data ",json_data)   
    
    return json_data

## gpt 칭찬 요약글
@csrf_exempt
def openAi_Story(request):
    print('### [API] openAi_Story ####################################################')
    
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':        
        for key, value in request.POST.items():
            print('### [INPUT] ', key, value)
            
        #-------------
        # 업무로직
        #-------------
        if 'id' in request.POST: 
            
            user_id = request.POST['id']
            token_id = request.POST['token_id']

            
            try:
                user_id = request.POST['id']
                token_id = request.POST['token_id']
                                
                selectUserTokens = UserTokens.objects.filter(
                        user_id=user_id,    
                        is_active='Y',
                        token_id=token_id,
                    ).select_related('user').first()
                
                                
                    
                if selectUserTokens.my_story_book:
                    
                    story = selectUserTokens.my_story_book
                    image = selectUserTokens.image
                    
                    story = story.replace(r'\r\n', '<br>')
                    story = story.replace('\r\n', '<br>')
                    story = story.replace('\r\n', '<br>')
                    story = story.replace('\r', '<br>')
                    story = story.replace('\n', '<br>')
                    story = story.replace("'", "")
                    story = story.replace(",", "")
                    story = story.replace('"', "") 
                    
                    print("### story ", story)

                    # data_list를 모두 합쳐서 data_text에 저장합니다.
                    #data_text = ''.join([data['org_content'] for data in data_list])

                    # data_text 출력
                    #print('### [OUTPUT] data_text:', data_text)

                    #-------------
                    # 출력내용 SET
                    #-------------
                    # 결과 데이터에 리스트와 총 건수를 추가합니다.
                    ResultData = {
                        'status': '200',
                        'data_count': len(story),
                        'story': story,
                        'image': image,
                    }
                
                else :
                    # 결과 데이터에 리스트와 총 건수를 추가합니다.
                    ResultData = {
                        'status': '200',
                        'data_count': '0',
                        'story': {
                            'summary': '[안내] 아쉽지만 발행가능 조건에 미달해서 제공할 수 없습니다. <br><br> ※ 발행조건 : 칭찬글 2건이상'
                        },
                    }                    

                # json으로 변환
                json_data = json.dumps(ResultData)
                #print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 

    
            except:
                ResultData = {
                    'status' : '403',
                    'story': {
                            'summary': '[오류] 칭찬글 분석 중 시스템 오류가 발생했습니다. 재거래 하시기 바랍니다.'
                        },
                    'error' : 'DB 갱신시 오류가 발생 했습니다.'
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 
            
        else:
            ResultData = {
                'status' : '401',
                'error' : '입력 데이터가 없습니다.'
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

def openAi_Short(requestData, sendUser, recvUser):
    print("### [MODULE] openAi called ",sendUser, recvUser)
    
    praiseText = requestData
    print('### [MODULE][LOG] praiseText ### ', praiseText)
    
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
    
    print("### [MODULE][LOG] response : ", response)
    message = response.json()['choices'][0]['message']['content']   
    
    print("### [MODULE][LOG] message : ", message)
    message = message.replace("'", "\"")


    # 응답이 {}로 시작하고 끝나는지 확인
    # message가 {}로 시작하고 끝나는지 확인
    if not (message.startswith("{") and message.endswith("}")):
        # {}로 감싸기
        message = "{" + message + "}"
        print("### [MODULE][LOG] message22 : ", message)
    
    # json 형태의 문자열 추출
    json_text = message[message.find("{"):message.rfind("}")+1]
    json_text = json_text.replace("'", "\"")

    # json으로 변환
    json_data = json.loads(json_text)
        
    print("### [MODULE][LOG] openAi json_data ",json_data)   
    
    return json_data

@csrf_exempt
def praise_count(request):
    print('### [API] praise_count ####################################################')
    
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':
        for key, value in request.POST.items():
            print('### [INPUT] ', key, value)
            
        #-------------
        # 업무로직
        #-------------
        if request.POST['user_id']:
            try:        
                
                user_id = request.POST.get('user_id')
                print('### [user_id] ',user_id)
                            
                #-------------
                # 토큰정보 
                #------------- 
                ## ttt
                today = datetime.now().strftime('%Y%m%d')
                
                if 'token_id' in request.POST and request.POST['token_id'] :
                    selectManageTokens = ManageTokens.objects.filter(
                        id=request.POST['token_id'],
                        is_active = 'Y'
                    ).first()
                else:
                    selectManageTokens = ManageTokens.objects.filter(
                        Q(start_date__lte=today) & Q(end_date__gte=today),
                        is_active='Y'
                    ).first()

                toeknYear    = selectManageTokens.year
                toeknQuarter = selectManageTokens.quarter

                selectUserTokens = UserTokens.objects.filter(
                                user_id=user_id,
                                year=toeknYear,
                                quarter=toeknQuarter,
                                is_active='Y'
                            ).first()
                
                if selectUserTokens:
                    praise_count = selectUserTokens.received_tokens
                else:
                    praise_count = 0

                # 해당 분기에 토큰을 받은 수를 기준으로 순위 조회
                quarter = toeknQuarter
                token_rankings = UserTokens.objects.filter(
                    quarter=quarter,
                    is_active='Y'
                ).values('user_id').annotate(token_count=Count('user_id')).order_by('-received_tokens')

                
                # 특정 사용자의 순위를 찾기 위해 index 위치를 탐색합니다
                #user_rank = next((i + 1 for i, token in enumerate(token_rankings) if token_rankings.user_id == user_id), None)
                #print('user_rank', user_rank)
                
                # 조작자의 순위 조회
                operator_rank = 0
                for index, ranking in enumerate(token_rankings):
                    #print("조작자의 순위:", index, ranking, "조작자 :", ranking['user_id'], user_id) 
                    if int(user_id) == ranking['user_id']: 
                        operator_rank = index + 1
                        break

                #print("조작자의 순위:", operator_rank)                    
                    

                #-------------
                # 칭찬내역 조회 ttt
                #-------------
                selectUserPraise = UserPraise.objects.filter(is_active='Y', praise_id = user_id, token_id = selectManageTokens.id)\
                    .select_related('praise', 'images').annotate(
                        praise_employee_name=F('praise__employee_name'),
                        praise_department_name=F('praise__department_name'),
                        praise_position_name=F('praise__position_name'),
                        praise_company_name=F('praise__company_name'),
                        user_employee_name=F('user__employee_name'),
                        user_department_name=F('user__department_name'),
                        user_position_name=F('user__position_name'),
                        user_company_name=F('user__company_name'),
                        image_path=F('images__image_path')
                    ).order_by('-reg_date')

                # 데이터를 담을 리스트 초기화
                data_list = []

                # 필드별 데이터를 리스트에 담습니다.
                for obj in selectUserPraise:
                    if obj.chg_date is not None:
                        chg_date_str = obj.chg_date.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        chg_date_str = None

                    if obj.reg_date is not None:
                        reg_date_str = obj.reg_date.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        reg_date_str = None

                    obj.content  = obj.content.replace('\r\n', '<br>')
                    obj.content  = obj.content.replace('\r\n', '<br>')
                    obj.content  = obj.content.replace('\r', '<br>')
                    obj.content  = obj.content.replace('\n', '<br>')
                        
                    data_list.append({
                        'compliment_id': obj.compliment_id,
                        'praise_id': obj.praise_id,
                        'user_id': obj.user_id,
                        
                        'praise_employee_name': obj.praise_employee_name,
                        'praise_department_name': obj.praise_department_name,
                        'praise_position_name': obj.praise_position_name,
                        'praise_company_name': obj.praise_company_name,

                        'user_employee_name': obj.user_employee_name,
                        'user_department_name': obj.user_department_name,
                        'user_position_name': obj.user_position_name,
                        'user_company_name': obj.user_company_name,
                        
                        'image_path': obj.image_path,
                        'compliment_type': obj.compliment_type,
                        'content': obj.content,
                        'images_id': obj.images_id,
                        'short_content': obj.short_content,
                        'tag': obj.tag,
                        'emotion_ratio': obj.emotion_ratio,
                        'view_count': obj.view_count,
                        'comment_count': obj.comment_count,
                        'likes_count': obj.likes_count,
                        'token_id': obj.token_id,
                        'is_active': obj.is_active,
                        'chg_date': chg_date_str,
                        'reg_date': reg_date_str,
                    })
                    
                #-------------
                # 출력내용 SET 
                #-------------
                ResultData = {
                    'status' : '200',
                    'praise_count' : praise_count,
                    'operator_rank': operator_rank,
                    'data_count': len(data_list),
                    'data_list': data_list
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                #print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 
    
            except:
                ResultData = {
                    'status' : '402',
                    'error' : 'DB적재시 오류가 발생 했습니다.'
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 
        else:
            ResultData = {
                'status' : '401',
                'error' : '입력 데이터가 없습니다.'
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
def userAppl(request):
    print('### [API] userAppl ####################################################')
    
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':
        for key, value in request.POST.items():
            print('### [INPUT] ', key, value)
            
        #-------------
        # 업무로직
        #-------------
        if request.POST['user_id']:
            try:        
                user_id = request.POST.get('user_id')
                ty = request.POST['ty']
                
                if request.POST['passYn'] == "Y":
                    print("### [API][LOG] passwoord reset")
                    user = User2.objects.get(id=user_id)
                    ##new_password = user.employee_id
                    new_password = f"w{user.employee_id}@"
                    
                    print("### new_password", new_password)
                    user.set_password(new_password)
                    user.save()
                
                else :
                    print('### [user_id] ',user_id)
                    print('### [ty]', ty)

                    User2.objects.filter(id=user_id).update(ty=ty)


                #-------------
                # 출력내용 SET
                #-------------
                ResultData = {
                    'status' : '200',
                    'user_id' : user_id,
                    'ty' : ty
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 
    
            except:
                ResultData = {
                    'status' : '402',
                    'error' : 'DB적재시 오류가 발생 했습니다.'
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 
        else:
            ResultData = {
                'status' : '401',
                'error' : '입력 데이터가 없습니다.'
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

def generate_wordcloud(text, user_id):

    print('### [API] generate_wordcloud ####################################################')

    today = date.today().strftime("%Y%m%d")
    now = datetime.now()
    time_string = now.strftime("%H%M%S")

    filename = 'user_' + user_id + '/' + today + '/' + time_string + '_' + 'storyWord.png'

    filePath = os.path.join('main/media/user/', filename)
    dataPath = os.path.join(settings.MEDIA_URL, filename)
    
    # 디렉토리 생성
    os.makedirs(os.path.dirname(filePath), exist_ok=True)

    #print("### filename", filename)
    print("### filePath", filePath)
    print("### dataPath", dataPath)
    #print('### settings.MEDIA_URL', settings.MEDIA_URL)

    #-------------------

    font_path = "/workspace/thankyou/font/NanumSquareR.ttf"
    heart_mask = np.array(Image.open("/workspace/thankyou/main/static/assets/img/main/word_mask.png"))

    # 워드 클라우드 객체 생성
    wordcloud = WordCloud(width=800, height=400,
                          background_color='white',
                          colormap='viridis',
                          max_font_size=150,
                          font_path=font_path,  # 한글 폰트 설정
                          random_state=42,
                          mask=heart_mask).generate(text)

    # 워드 클라우드 이미지를 파일로 저장
    #image_path = os.path.join(save_path, 'wordcloud2.png')
    #image_path = os.path.join('main/media/user/', 'wordcloud2.png')
    #print('### image_path 1', image_path)

    image_path = filePath
    #print('### [API][LOG] image_path ', image_path)
    wordcloud.to_file(image_path)

    # 워드 클라우드 이미지 파일 경로 출력
    print("### [API][LOG] Save File path : ", image_path)

    return dataPath

@csrf_exempt
def userStory(request):
    print('### [API] userStory ####################################################')
    
    #-------------
    # 사용자 검증
    #-------------
    if request.user.is_superuser :
        print("### 관리자 접속")
    else :
        print("### 사용자 접속")
        error = "[101] 관리자 외 접속 불가합니다."
        return render(request, 'page_error.html', {'error': error})  
    
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':
        for key, value in request.POST.items():
            print('### [API][INPUT] ', key, value)
                        
        #-------------
        # 업무로직
        #-------------
        if request.POST['user_id']:
            try :     
                user_id = request.POST.get('user_id')
                token_id = request.POST.get('token_id')
                
                selectUserPraise = UserPraise.objects.filter(
                    praise_id=user_id,
                    is_active='Y',
                    token_id = token_id
                ).order_by('-reg_date')#[2:7]
                
                if selectUserPraise.exists():
                    # 데이터를 담을 리스트 초기화
                    data_list = []

                    # 필드별 데이터를 리스트에 담습니다.
                    for obj in selectUserPraise:
                        data_list.append({
                            '칭찬글': obj.org_content,  
                        })
                        
                    # 한개의 칭찬글을 it직원 설명추가
                    if len(selectUserPraise) == 1:
                        data_list.append({
                            '칭찬글': '회사에서 많은 지원과 도움을 받았습니다. 항상 도움을 주신점 감사드리고 칭찬드립니다.',  
                        })

                    #print("### data_list ", data_list)
                    selectUser = User2.objects.filter(id=user_id).first()

                    #임시
                    result_story = openAi(data_list, selectUser.employee_name)    
                    #result_story = ''
                    
                    #print("### openai result_story ", result_story)
                    
                    print('### [API][LOG] openAi success')

                else :
                    print('### [API][LOG] NOT EXIST')
                      
                    ResultData = {
                        'status' : '402',
                        'error' : 'DB적재시 오류가 발생 했습니다.'
                    }

                    # json으로 변환
                    json_data = json.dumps(ResultData)
                    print("### [OUTPUT] JSON = ",json_data)   

                    return HttpResponse(json_data, content_type="application/json") 
                
                
                result_story = result_story.replace(r'\r\n', '<br>')
                result_story = result_story.replace('\r\n', '<br>')
                result_story = result_story.replace('\r\n', '<br>')
                result_story = result_story.replace('\r', '<br>')
                result_story = result_story.replace('\n', '<br>')
                result_story = result_story.replace("'", "")
                result_story = result_story.replace(",", "")
                result_story = result_story.replace('"', "") 
                result_story = result_story.replace("그의", "")
                result_story = result_story.replace("그는", "")
                result_story = result_story.replace("그녀의", "")
                result_story = result_story.replace("그녀는", "")

                
                #--------------------
                #image make
                #--------------------
                
                
                #selectUserTokens = UserTokens.objects.filter(
                #        user_id = user_id,
                #        is_active='Y',
                #        token_id=token_id
                #    ).first()
                #result_story = selectUserTokens.my_story_book
                #result_story = '테스트 내용 입니다'
                #print('### test call')

                #---------------------
                image_story = result_story
                image_story = image_story.replace('<br>', "")
                image_path = generate_wordcloud(image_story, user_id)
                                
                #--------------------
                #state update 
                #--------------------
                UserTokens.objects.filter(
                    user_id=user_id,
                    is_active='Y',
                    token_id=token_id
                ).update(
                    my_story_stcd = 1,
                    my_story_book = result_story,
                    my_story_date = datetime.now(),
                    image_yn = 'Y',
                    image    = image_path
                )
                
                #--------------------
                # selectUserTokens
                #--------------------
                selectUserTokens = UserTokens.objects.filter(
                        user_id = user_id,
                        is_active='Y',
                        token_id=token_id
                    ).first()
                                   
                my_story_stcd = selectUserTokens.my_story_stcd
                my_story_book = selectUserTokens.my_story_book
                my_story_date = selectUserTokens.my_story_date
                
                my_story_book = my_story_book.replace(r'\r\n', '<br>')
                my_story_book = my_story_book.replace('\r\n', '<br>')
                my_story_book = my_story_book.replace('\r\n', '<br>')
                my_story_book = my_story_book.replace('\r', '<br>')
                my_story_book = my_story_book.replace('\n', '<br>')
                my_story_book = my_story_book.replace("'", "")
                my_story_book = my_story_book.replace(",", "")
                my_story_book = my_story_book.replace('"', "")      
                
                if my_story_date is not None:
                    my_story_date = my_story_date.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    my_story_date = None
                    
                #print('### my_story_stcd', my_story_stcd)
                #print('### my_story_book', my_story_book)
                #print('### my_story_date', my_story_date)
                
                #-------------
                # 출력내용 SET
                #-------------
                # 결과 데이터에 리스트와 총 건수를 추가합니다.
                ResultData = {
                    'status': '200',
                    'my_story_stcd': escape(my_story_stcd),
                    'my_story_book': escape(my_story_book),
                    'my_story_date': escape(my_story_date),
                    'image': image_path,
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                #print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 
    
            except:
                ResultData = {
                    'status' : '402',
                    'error' : 'DB적재시 오류가 발생 했습니다.'
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 
        else:
            ResultData = {
                'status' : '401',
                'error' : '입력 데이터가 없습니다.'
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
def search_dept(request):
    print('### [API] search_dept ####################################################')
    
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':        
        for key, value in request.POST.items():
            print('### [INPUT] ', key, value)
            
        #-------------
        # 업무로직
        #-------------
        if request.POST['dept_name']:
            
            try:
                dept_name = request.POST['dept_name']
                company_id = request.POST['company_id']

                selectManageDept = ManageDept.objects.filter(
                    Q(dept_name__icontains=dept_name),
                    is_active='Y', company_id = company_id
                ).order_by('dept_name')


                # 데이터를 담을 리스트 초기화
                data_list = []

                # 필드별 데이터를 리스트에 담습니다.
                for obj in selectManageDept:

                    data_list.append({
                        'dept_id': obj.dept_id,
                        'dept_name': obj.dept_name,
                        'dept_level': obj.dept_level,
                        'parent_dept_id': obj.parent_dept_id,
                    })

                if not selectManageDept:
                    data_list.append({
                        'dept_id': None,
                        'dept_name': '[결과] 대상이 없습니다',
                        'dept_level': 0,
                        'parent_dept_id': None,
                    })
                    
                #-------------
                # 출력내용 SET
                #-------------
                # 결과 데이터에 리스트와 총 건수를 추가합니다.
                ResultData = {
                    'status': '200',
                    'data_count': len(data_list),
                    'data_list': data_list,
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 

    
            except:
                ResultData = {
                    'status' : '403',
                    'error' : 'DB 갱신시 오류가 발생 했습니다.'
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 
            
        else:
            ResultData = {
                'status' : '401',
                'error' : '입력 데이터가 없습니다.'
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
def search_posi(request):
    print('### [API] search_posi ####################################################')
    
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':        
        for key, value in request.POST.items():
            print('### [INPUT] ', key, value)
            
        #-------------
        # 업무로직
        #-------------
        if request.POST['posi_name']:
            
            try:
                posi_name = request.POST['posi_name']
                company_id = request.POST['company_id']

                selectManagePosi = ManagePosi.objects.filter(
                    Q(posi_name__icontains=posi_name),
                    is_active='Y', company_id = company_id
                ).order_by('posi_name')


                # 데이터를 담을 리스트 초기화
                data_list = []

                # 필드별 데이터를 리스트에 담습니다.
                for obj in selectManagePosi:

                    data_list.append({
                        'posi_id': obj.posi_id,
                        'posi_name': obj.posi_name,
                    })

                if not selectManagePosi:
                    data_list.append({
                        'posi_id': None,
                        'posi_name': '[결과] 대상이 없습니다',
                    })
                    
                #-------------
                # 출력내용 SET
                #-------------
                # 결과 데이터에 리스트와 총 건수를 추가합니다.
                ResultData = {
                    'status': '200',
                    'data_count': len(data_list),
                    'data_list': data_list,
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 

    
            except:
                ResultData = {
                    'status' : '403',
                    'error' : 'DB 갱신시 오류가 발생 했습니다.'
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 
            
        else:
            ResultData = {
                'status' : '401',
                'error' : '입력 데이터가 없습니다.'
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
def manage_user(request):
    print('### [API] manage_user ####################################################')
    
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':        
        
        # json 데이터를 수신합니다.
        data = json.loads(request.body)

        # 데이터를 출력합니다.
        print("Received Data:", data)
                    
        #-------------
        # 업무로직
        #-------------
        if data :
            
            #-----------------------------------------------
            # 입력변수 SET
            #-----------------------------------------------
            
            #거래구분 (신규/갱신/삭제)
            trn_cd        = data.get('trn_cd', None)
            username      = data.get('employee_id', None)    
            password      = username
            employee_id   = data.get('employee_id', None)      
            employee_name = data.get('employee_name', None)  
            position_id   = data.get('position_id', None)      
            department_id = data.get('department_id', None)  
            company_id    = data.get('company_id', None)        
            org_username  = data.get('pre_employee_id', None)
                        
            selectManageDept = ManageDept.objects.filter(
                company_id = company_id,
                dept_id = department_id,
                is_active='Y'
            ).first()
            if selectManageDept:
                department_name = selectManageDept.dept_name
            else:
                department_name = None
            
            selectManageDept2 = ManageDept.objects.filter(
                company_id = company_id,
                is_active='Y'
            ).first()
            if selectManageDept2:
                company_name = selectManageDept2.company_name
            else:
                company_name = None
                
            selectManagePosi = ManagePosi.objects.filter(
                company_id = company_id,
                posi_id = position_id,
                is_active='Y'
            ).first()
            if selectManagePosi:
                position_name = selectManagePosi.posi_name
            else:
                position_name = None
                
            if username == org_username:
                org_username = "same"    
                
            print('### [LOG] trn_cd', trn_cd)
            print('### [LOG] username', username)
            print('### [LOG] employee_id', employee_id)
            print('### [LOG] employee_name', employee_name)
            print('### [LOG] department_id', department_id)
            print('### [LOG] department_name', department_name)
            print('### [LOG] position_id', position_id)
            print('### [LOG] position_name', position_name)
            print('### [LOG] company_id', company_id)
            print('### [LOG] company_name', company_name)
            print('### [LOG] org_username', org_username)
                
            if department_name is None:
                ResultData = {
                    'status' : '202',
                    'error' : '[오류] 부서코드 오류 입니다.'
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                print("### [OUTPUT] JSON = ",json_data)   

                # 응답전문
                response = HttpResponse(json_data, content_type="application/json")
                # CORS 헤더 추가
                response["Access-Control-Allow-Credentials"] = "true"
                # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
                response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

                return response

            if position_name is None:
                ResultData = {
                    'status' : '203',
                    'error' : '[오류] 직급코드 오류 입니다.'
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                print("### [OUTPUT] JSON = ",json_data)   

                # 응답전문
                response = HttpResponse(json_data, content_type="application/json")
                # CORS 헤더 추가
                response["Access-Control-Allow-Credentials"] = "true"
                # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
                response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

                return response

            if company_name is None:
                ResultData = {
                    'status' : '204',
                    'error' : '[오류] 회사코드 오류 입니다.'
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                print("### [OUTPUT] JSON = ",json_data)   

                # 응답전문
                response = HttpResponse(json_data, content_type="application/json")
                # CORS 헤더 추가
                response["Access-Control-Allow-Credentials"] = "true"
                # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
                response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

                return response
            
            #-----------------------------------------------
            # [신규] 업무로직
            #-----------------------------------------------
            if trn_cd == 'I' :
                
                try:
                    
                    if User2.objects.filter(username=username).exists():

                        ResultData = {
                            'status' : '201',
                            'error' : '[오류] 이미 존재하는 사번ID 입니다.'
                        }

                        # json으로 변환
                        json_data = json.dumps(ResultData)
                        print("### [OUTPUT] JSON = ",json_data)   

                        # 응답전문
                        response = HttpResponse(json_data, content_type="application/json")
                        # CORS 헤더 추가
                        response["Access-Control-Allow-Credentials"] = "true"
                        # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
                        response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

                        return response
                    
                    #////////////////////////////////////////////////////////////
                    # (기존직원) 데이터 이행처리
                    #////////////////////////////////////////////////////////////
                    user_skip_yn = "N" # 신규적재 SKIP 대상직원
                    
                    if org_username :
                        print('### [LOG] org_username ', org_username)
                        selectOrgUser = User2.objects.filter(username=org_username).first()

                        if selectOrgUser :
                            print('### [LOG] selectOrgUser1 update', org_username, username)
                            updateUser = User2.objects.get(id=selectOrgUser.id)
                            
                            updateUser.username        = username
                            updateUser.ty              = 1
                            updateUser.is_active       = 1
                            updateUser.employee_id     = employee_id
                            updateUser.employee_name   = employee_name
                            updateUser.department_id   = department_id
                            updateUser.department_name = department_name
                            updateUser.position_id     = position_id
                            updateUser.position_name   = position_name
                            updateUser.company_id      = company_id
                            updateUser.company_name    = company_name
                            updateUser.org_username    = org_username
                            updateUser.chg_date        = datetime.now() 
                            
                            updateUser.save()
                            print('### [LOG] user updateUser1 success', username)
                            
                            user_skip_yn = "Y" # 신규적재 SKIP 대상직원
                        else :
                            print('### [LOG] org_username update skip', org_username, username)
                            
                    # ----------------------------
                    # 전직자 정보검증 추가 (2024-01-23)
                    # ----------------------------
                    selectMigrationUser = MigrationUser.objects.filter(
                        new_employee=username,
                        is_active='Y'
                    ).first()
                    if selectMigrationUser :
                        print('### [LOG] selectMigrationUser ', selectMigrationUser.org_employee, selectMigrationUser.new_employee)
                        
                        selectOrgUser = User2.objects.filter(username=selectMigrationUser.org_employee).first()
                        if selectOrgUser :
                            print('### [LOG] selectOrgUser2 ', selectOrgUser.username)
                            updateUser = User2.objects.get(id=selectOrgUser.id)
                            
                            updateUser.username        = username
                            updateUser.ty              = 1
                            updateUser.is_active       = 1
                            updateUser.employee_id     = employee_id
                            updateUser.employee_name   = employee_name
                            updateUser.department_id   = department_id
                            updateUser.department_name = department_name
                            updateUser.position_id     = position_id
                            updateUser.position_name   = position_name
                            updateUser.company_id      = company_id
                            updateUser.company_name    = company_name
                            updateUser.org_username    = org_username
                            updateUser.chg_date        = datetime.now() 
                            
                            updateUser.save()
                            print('### [LOG] user updateUser2 success', username)
                            user_skip_yn = "Y" # 신규적재 SKIP 대상직원
                            
                    #////////////////////////////////////////////////////////////
                    # (신규직원) 데이터 적재처리
                    #////////////////////////////////////////////////////////////
                    if user_skip_yn == "Y" :   
                        print('### [LOG] user insert SKIP', username)
                        
                    else :
                      
                        # ----------------------------
                        # 전직자 정보검증 추가 (2024-01-23)
                        # ----------------------------
                        selectMigrationUser = MigrationUser.objects.filter(
                            org_employee=username,
                            is_active='Y'
                        ).first()
                        if selectMigrationUser :
                            print('### [LOG] selectMigrationUser ', selectMigrationUser.org_employee, selectMigrationUser.new_employee)
                            
                            selectNewUser = User2.objects.filter(username=selectMigrationUser.new_employee).first()
                            if selectNewUser :
                                print('### [LOG] selectNewUser ', selectNewUser.username)
                            
                                ResultData = {
                                        'status' : '202',
                                        'error' : '[오류] 이미 신규행번ID가 있니다.'
                                    }

                                # json으로 변환
                                json_data = json.dumps(ResultData)
                                print("### [OUTPUT] JSON = ",json_data)   

                                # 응답전문
                                response = HttpResponse(json_data, content_type="application/json")
                                # CORS 헤더 추가
                                response["Access-Control-Allow-Credentials"] = "true"
                                # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
                                response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

                                return response
                      
                        print('### [LOG] user insert', username)
                        insertUser = User2.objects.create_user(
                            username        = username,
                            password        = 'woori7799$$',
                            ty              = 1,
                            employee_id     = employee_id,
                            employee_name   = employee_name,
                            department_id   = department_id,
                            department_name = department_name,
                            position_id     = position_id,
                            position_name   = position_name,
                            company_id      = company_id,
                            company_name    = company_name,
                            org_username    = org_username,
                            reg_date        = datetime.now() 
                        )
                    
                    print('### [LOG] user insert success', username)
                    #-------------
                    # 출력내용 SET
                    #-------------
                    # 결과 데이터에 리스트와 총 건수를 추가합니다.
                    ResultData = {
                        'status': '000',
                        'error': ''
                    }

                    # json으로 변환
                    json_data = json.dumps(ResultData)
                    print("### [OUTPUT] JSON = ",json_data)   

                    # 응답전문
                    response = HttpResponse(json_data, content_type="application/json")
                    # CORS 헤더 추가
                    response["Access-Control-Allow-Credentials"] = "true"
                    # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
                    response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

                    return response

                except:
                    ResultData = {
                        'status' : '200',
                        'error' : '신규회원 처리시 오류가 발생 했습니다.'
                    }

                    # json으로 변환
                    json_data = json.dumps(ResultData)
                    print("### [OUTPUT] JSON = ",json_data)   

                    # 응답전문
                    response = HttpResponse(json_data, content_type="application/json")
                    # CORS 헤더 추가
                    response["Access-Control-Allow-Credentials"] = "true"
                    # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
                    response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

                    return response
                
            #-----------------------------------------------
            # [갱신] 업무로직
            #-----------------------------------------------
            elif trn_cd == 'U' :

                try:
                    
                    selectUser = User2.objects.filter(username=username).first()
                    
                    if not selectUser:

                        ########################
                        # 2024-01-05 이행작업 예외처리
                        ########################
                        user_skip_yn = "N" # 신규적재 SKIP 대상직원
                        
                        if org_username :
                            selectOrgUser = User2.objects.filter(username=org_username).first()

                            if selectOrgUser :
                                print('### [LOG] org_username update', org_username, username)
                                updateUser = User2.objects.get(id=selectOrgUser.id)
                                
                                updateUser.username        = username
                                updateUser.ty              = 1
                                updateUser.is_active       = 1
                                updateUser.employee_id     = employee_id
                                updateUser.employee_name   = employee_name
                                updateUser.department_id   = department_id
                                updateUser.department_name = department_name
                                updateUser.position_id     = position_id
                                updateUser.position_name   = position_name
                                updateUser.company_id      = company_id
                                updateUser.company_name    = company_name
                                updateUser.org_username    = org_username
                                updateUser.chg_date        = datetime.now() 
                                
                                updateUser.save()
                                print('### [LOG] user updateUser1 success', username)
                                
                                user_skip_yn = "Y" # 신규적재 SKIP 대상직원
                                
                                #-------------
                                # 출력내용 SET
                                #-------------
                                # 결과 데이터에 리스트와 총 건수를 추가합니다.
                                ResultData = {
                                    'status': '000',
                                    'error': ''
                                }

                                # json으로 변환
                                json_data = json.dumps(ResultData)
                                print("### [OUTPUT] JSON = ",json_data)   

                                # 응답전문
                                response = HttpResponse(json_data, content_type="application/json")
                                # CORS 헤더 추가
                                response["Access-Control-Allow-Credentials"] = "true"
                                # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
                                response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

                                return response
                                
                            else :
                                print('### [LOG] org_username update skip', org_username, username)                           

                        ResultData = {
                            'status' : '201',
                            'error' : '[오류] 존재하는 않는 사번ID 입니다.'
                        }

                        # json으로 변환
                        json_data = json.dumps(ResultData)
                        print("### [OUTPUT] JSON = ",json_data)   

                        # 응답전문
                        response = HttpResponse(json_data, content_type="application/json")
                        # CORS 헤더 추가
                        response["Access-Control-Allow-Credentials"] = "true"
                        # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
                        response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

                        return response
                    
                    
                    #////////////////////////////////////////////////////////////
                    # (기존직원) 데이터 이행처리
                    #////////////////////////////////////////////////////////////
                    user_skip_yn = "N" # 신규적재 SKIP 대상직원
                    
                    if org_username :
                        selectOrgUser = User2.objects.filter(username=org_username).first()

                        if selectOrgUser :
                            print('### [LOG] org_username update', org_username, username)
                            
                            # ------------------
                            # 신행번은 BACK 처리
                            # ------------------
                            updateUser = User2.objects.get(id=selectUser.id)
                            current_time = datetime.now().strftime("%H%M%S")
                            
                            updateUser.username        = username + "_backup_" + current_time
                            updateUser.ty              = 0
                            updateUser.is_active       = 0
                            updateUser.org_username    = org_username
                            updateUser.chg_date        = datetime.now() 
                            
                            updateUser.save()
                            print('### [LOG] user updateUser2 Backup success', username)
                                                       
                            # ------------------
                            # 구행번를 신행번으로  데이터 이행
                            # ------------------
                            updateUser = User2.objects.get(id=selectOrgUser.id)
                            
                            updateUser.username        = username
                            updateUser.ty              = 1
                            updateUser.is_active       = 1
                            updateUser.employee_id     = employee_id
                            updateUser.employee_name   = employee_name
                            updateUser.department_id   = department_id
                            updateUser.department_name = department_name
                            updateUser.position_id     = position_id
                            updateUser.position_name   = position_name
                            updateUser.company_id      = company_id
                            updateUser.company_name    = company_name
                            updateUser.org_username    = org_username
                            updateUser.chg_date        = datetime.now() 
                            
                            updateUser.save()
                            print('### [LOG] user updateUser2 Final success', username)
                            user_skip_yn = "Y" # 신규적재 SKIP 대상직원
                            
                        else :
                            print('### [LOG] org_username update skip', org_username, username)
                            
                    #////////////////////////////////////////////////////////////
                    # (기존직원) 데이터 갱신처리
                    #////////////////////////////////////////////////////////////
                    if user_skip_yn == "Y" :   
                        print('### [LOG] user update SKIP', username)
                        
                    else :
                        updateUser = User2.objects.get(id=selectUser.id)
                        
                        updateUser.ty              = 1
                        updateUser.is_active       = 1
                        updateUser.employee_id     = employee_id
                        updateUser.employee_name   = employee_name
                        updateUser.department_id   = department_id
                        updateUser.department_name = department_name
                        updateUser.position_id     = position_id
                        updateUser.position_name   = position_name
                        updateUser.company_id      = company_id
                        updateUser.company_name    = company_name
                        updateUser.org_username    = org_username
                        updateUser.chg_date        = datetime.now() 
                        
                        updateUser.save()
                        print('### [LOG] user updateUser3 success', username)
                    
                    #-------------
                    # 출력내용 SET
                    #-------------
                    # 결과 데이터에 리스트와 총 건수를 추가합니다.
                    ResultData = {
                        'status': '000',
                        'error': ''
                    }

                    # json으로 변환
                    json_data = json.dumps(ResultData)
                    print("### [OUTPUT] JSON = ",json_data)   

                    # 응답전문
                    response = HttpResponse(json_data, content_type="application/json")
                    # CORS 헤더 추가
                    response["Access-Control-Allow-Credentials"] = "true"
                    # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
                    response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

                    return response

                except:
                    ResultData = {
                        'status' : '200',
                        'error' : '갱신회원 처리시 오류가 발생 했습니다.'
                    }

                    # json으로 변환
                    json_data = json.dumps(ResultData)
                    print("### [OUTPUT] JSON = ",json_data)   

                    # 응답전문
                    response = HttpResponse(json_data, content_type="application/json")
                    # CORS 헤더 추가
                    response["Access-Control-Allow-Credentials"] = "true"
                    # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
                    response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

                    return response
                
            #-----------------------------------------------
            # [삭제] 업무로직
            #-----------------------------------------------
            elif trn_cd == 'D' :                
                
                try:
                    
                    selectUser = User2.objects.filter(username=username).first()
                    
                    if not selectUser:

                        ResultData = {
                            'status' : '201',
                            'error' : '[오류] 존재하는 않는 사번ID 입니다.'
                        }

                        # json으로 변환
                        json_data = json.dumps(ResultData)
                        print("### [OUTPUT] JSON = ",json_data)   

                        # 응답전문
                        response = HttpResponse(json_data, content_type="application/json")
                        # CORS 헤더 추가
                        response["Access-Control-Allow-Credentials"] = "true"
                        # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
                        response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

                        return response
                        
                    #////////////////////////////////////////////////////////////
                    # (기존직원) 데이터 삭제처리
                    #////////////////////////////////////////////////////////////
                    print('### [LOG] user delete')
                    deleteUser = User2.objects.get(id=selectUser.id)
                    
                    deleteUser.username        = deleteUser.id
                    deleteUser.ty              = 0
                    deleteUser.is_active       = 1
                    deleteUser.employee_id     = ' '
                    deleteUser.employee_name   = ' '
                    deleteUser.department_id   = ' '
                    deleteUser.department_name = ' '
                    deleteUser.position_id     = ' '
                    deleteUser.position_name   = ' '
                    deleteUser.company_id      = ' '
                    deleteUser.company_name    = ' '
                    deleteUser.chg_date        =  datetime.now() 
                    
                    # 변경된 필드 값을 저장합니다.
                    deleteUser.save()
                    print('### [LOG] user delete update success', username)
                    
                    #-------------
                    # 출력내용 SET
                    #-------------
                    # 결과 데이터에 리스트와 총 건수를 추가합니다.
                    ResultData = {
                        'status': '000',
                        'error': ''
                    }

                    # json으로 변환
                    json_data = json.dumps(ResultData)
                    print("### [OUTPUT] JSON = ",json_data)   

                    # 응답전문
                    response = HttpResponse(json_data, content_type="application/json")
                    # CORS 헤더 추가
                    response["Access-Control-Allow-Credentials"] = "true"
                    # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
                    response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

                    return response

                except:
                    ResultData = {
                        'status' : '200',
                        'error' : '삭제회원 처리시 오류가 발생 했습니다.'
                    }

                    # json으로 변환
                    json_data = json.dumps(ResultData)
                    print("### [OUTPUT] JSON = ",json_data)   

                    # 응답전문
                    response = HttpResponse(json_data, content_type="application/json")
                    # CORS 헤더 추가
                    response["Access-Control-Allow-Credentials"] = "true"
                    # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
                    response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

                    return response
                
            else :
                ResultData = {
                    'status' : '102',
                    'error' : '[거래구분] 코드의 포맷 오류입니다.'
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                print("### [OUTPUT] JSON = ",json_data)   

                # 응답전문
                response = HttpResponse(json_data, content_type="application/json")
                # CORS 헤더 추가
                response["Access-Control-Allow-Credentials"] = "true"
                # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
                response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

                return response

            
        else:
            ResultData = {
                'status' : '101',
                'error' : '입력 데이터 포맷 오류입니다.'
            }

            # json으로 변환
            json_data = json.dumps(ResultData)
            print("### [OUTPUT] JSON = ",json_data)   

            # 응답전문
            response = HttpResponse(json_data, content_type="application/json")
            # CORS 헤더 추가
            response["Access-Control-Allow-Credentials"] = "true"
            # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
            response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

            return response
        
    #######################################
    # POST 수신아닌 경우
    #######################################    
    ResultData = {
        'status' : '100',
        'error' : '잘못된 호출 입니다.'
    }
    
    # json으로 변환
    json_data = json.dumps(ResultData)
    print("### [OUTPUT] JSON = ",json_data)   
    
    # 응답전문
    response = HttpResponse(json_data, content_type="application/json")
    # CORS 헤더 추가
    response["Access-Control-Allow-Credentials"] = "true"
    # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
    response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

    return response

@csrf_exempt
def manage_department(request):
    print('### [API] manage_department ####################################################')
    
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':        
        
        # json 데이터를 수신합니다.
        data = json.loads(request.body)

        # 데이터를 출력합니다.
        print("Received Data:", data)
                    
        #-------------
        # 업무로직
        #-------------
        if data :
            
            #-------------
            # 입력변수 SET
            #-------------
            
            #거래구분 (신규/갱신/삭제)
            trn_cd        = data.get('trn_cd', None)
            company_id    = data.get('company_id', None)        
            company_name  = data.get('company_name', None)        
            department_id = data.get('department_id', None)  
            department_name = data.get('department_name', None)  
            department_lev = data.get('department_lev', None)  
            parent_department_id = data.get('parent_department_id', None)  
            peer_no = data.get('peer_no', None)  
                                    
            print('### [LOG] trn_cd', trn_cd)
            print('### [LOG] department_id', department_id)
            print('### [LOG] department_name', department_name)
            print('### [LOG] company_id', company_id)
            print('### [LOG] company_name', company_name)
            print('### [LOG] department_lev', department_lev)
            print('### [LOG] parent_department_id', parent_department_id)
            print('### [LOG] peer_no', peer_no)
            
            #-----------------------------------
            # [신규] 업무로직
            #-----------------------------------
            if trn_cd == 'I' :
                
                try:
                    if ManageDept.objects.filter(dept_id=department_id, company_id=company_id, is_active = 'Y').exists():

                        ResultData = {
                            'status' : '201',
                            'error' : '[오류] 이미 존재하는 부서ID 입니다.'
                        }

                        # json으로 변환
                        json_data = json.dumps(ResultData)
                        print("### [OUTPUT] JSON = ",json_data)   
                        
                        # 응답전문
                        response = HttpResponse(json_data, content_type="application/json")
                        # CORS 헤더 추가
                        response["Access-Control-Allow-Credentials"] = "true"
                        # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
                        response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

                        return response

                    print('### [LOG] ManageDept insert')
                    insertManageDept = ManageDept.objects.create(
                        company_id = company_id,
                        company_name = company_name,
                        dept_id = department_id,
                        dept_name = department_name,
                        dept_level = department_lev,
                        parent_dept_id = parent_department_id,
                        peer_no =peer_no,
                        is_active = 'Y',
                        reg_date =  datetime.now() 
                    )
                    print('### [LOG] ManageDept insert success', insertManageDept.id)
                    #-------------
                    # 출력내용 SET
                    #-------------
                    # 결과 데이터에 리스트와 총 건수를 추가합니다.
                    ResultData = {
                        'status': '000',
                        'error': ''
                    }

                    # json으로 변환
                    json_data = json.dumps(ResultData)
                    print("### [OUTPUT] JSON = ",json_data)   

                    # 응답전문
                    response = HttpResponse(json_data, content_type="application/json")
                    # CORS 헤더 추가
                    response["Access-Control-Allow-Credentials"] = "true"
                    # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
                    response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

                    return response


                except:
                    ResultData = {
                        'status' : '200',
                        'error' : '신규부서 처리시 오류가 발생 했습니다.'
                    }

                    # json으로 변환
                    json_data = json.dumps(ResultData)
                    print("### [OUTPUT] JSON = ",json_data)   

                    # 응답전문
                    response = HttpResponse(json_data, content_type="application/json")
                    # CORS 헤더 추가
                    response["Access-Control-Allow-Credentials"] = "true"
                    # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
                    response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

                    return response
                
            #-----------------------------------
            # [갱신] 업무로직
            #-----------------------------------
            elif trn_cd == 'U' :

                try:
                    
                    selectManageDept = ManageDept.objects.filter(dept_id=department_id, company_id=company_id).first()
                    
                    if not selectManageDept:

                        ResultData = {
                            'status' : '201',
                            'error' : '[오류] 존재하는 않는 부서ID 입니다.'
                        }

                        # json으로 변환
                        json_data = json.dumps(ResultData)
                        print("### [OUTPUT] JSON = ",json_data)   

                        # 응답전문
                        response = HttpResponse(json_data, content_type="application/json")
                        # CORS 헤더 추가
                        response["Access-Control-Allow-Credentials"] = "true"
                        # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
                        response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

                        return response
                    
                    print('### [LOG] selectManageDept.id', selectManageDept.id)
                    print('### [LOG] ManageDept update')
                    updateManageDept = ManageDept.objects.get(id=selectManageDept.id)
                    
                    updateManageDept.company_id = company_id
                    updateManageDept.company_name = company_name
                    updateManageDept.dept_id = department_id
                    updateManageDept.dept_name = department_name
                    updateManageDept.dept_level = department_lev
                    updateManageDept.parent_dept_id = parent_department_id
                    updateManageDept.peer_no = peer_no
                    updateManageDept.is_active = 'Y'
                    updateManageDept.chg_date =  datetime.now() 
                    
                    updateManageDept.save()
                    print('### [LOG] ManageDept update success')
                    
                    User2.objects.filter(
                        company_id=company_id,
                        department_id=department_id,
                        is_active=1
                    ).update(
                        department_name=department_name
                    )
                    print('### [LOG] User2 update success')
                    
                    #-------------
                    # 출력내용 SET
                    #-------------
                    # 결과 데이터에 리스트와 총 건수를 추가합니다.
                    ResultData = {
                        'status': '000',
                        'error': ''
                    }

                    # json으로 변환
                    json_data = json.dumps(ResultData)
                    print("### [OUTPUT] JSON = ",json_data)   

                    # 응답전문
                    response = HttpResponse(json_data, content_type="application/json")
                    # CORS 헤더 추가
                    response["Access-Control-Allow-Credentials"] = "true"
                    # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
                    response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

                    return response

                except:
                    ResultData = {
                        'status' : '200',
                        'error' : '갱신부서 처리시 오류가 발생 했습니다.'
                    }

                    # json으로 변환
                    json_data = json.dumps(ResultData)
                    print("### [OUTPUT] JSON = ",json_data)   

                    # 응답전문
                    response = HttpResponse(json_data, content_type="application/json")
                    # CORS 헤더 추가
                    response["Access-Control-Allow-Credentials"] = "true"
                    # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
                    response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

                    return response
                
            #-----------------------------------
            # [삭제] 업무로직
            #-----------------------------------
            elif trn_cd == 'D' :                
                
                try:
                    
                    selectManageDept = ManageDept.objects.filter(dept_id=department_id, company_id=company_id).first()
                    
                    if not selectManageDept:

                        ResultData = {
                            'status' : '201',
                            'error' : '[오류] 존재하는 않는 부서ID 입니다.'
                        }

                        # json으로 변환
                        json_data = json.dumps(ResultData)
                        print("### [OUTPUT] JSON = ",json_data)   

                        # 응답전문
                        response = HttpResponse(json_data, content_type="application/json")
                        # CORS 헤더 추가
                        response["Access-Control-Allow-Credentials"] = "true"
                        # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
                        response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

                        return response

                    print('### [LOG] selectManageDept.id', selectManageDept.id)
                    print('### [LOG] ManageDept delete')
                    deleteManageDept = ManageDept.objects.get(id=selectManageDept.id)
                    
                    deleteManageDept.company_id = selectManageDept.id
                    deleteManageDept.company_name = ' '
                    deleteManageDept.dept_id = ' '
                    deleteManageDept.dept_name = ' '
                    deleteManageDept.dept_level = '0'
                    deleteManageDept.parent_dept_id = ' '
                    deleteManageDept.peer_no = ' '
                    deleteManageDept.is_active = ' '
                    deleteManageDept.chg_date =  datetime.now() 
                    
                    deleteManageDept.save()
                    print('### [LOG] ManageDept delete update success')
                    
                    #-------------
                    # 출력내용 SET
                    #-------------
                    # 결과 데이터에 리스트와 총 건수를 추가합니다.
                    ResultData = {
                        'status': '000',
                        'error': ''
                    }

                    # json으로 변환
                    json_data = json.dumps(ResultData)
                    print("### [OUTPUT] JSON = ",json_data)   

                    # 응답전문
                    response = HttpResponse(json_data, content_type="application/json")
                    # CORS 헤더 추가
                    response["Access-Control-Allow-Credentials"] = "true"
                    # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
                    response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

                    return response

                except:
                    ResultData = {
                        'status' : '200',
                        'error' : '삭제부서 처리시 오류가 발생 했습니다.'
                    }

                    # json으로 변환
                    json_data = json.dumps(ResultData)
                    print("### [OUTPUT] JSON = ",json_data)   

                    # 응답전문
                    response = HttpResponse(json_data, content_type="application/json")
                    # CORS 헤더 추가
                    response["Access-Control-Allow-Credentials"] = "true"
                    # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
                    response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

                    return response
                
            else :
                ResultData = {
                    'status' : '102',
                    'error' : '[거래구분] 코드의 포맷 오류입니다.'
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                print("### [OUTPUT] JSON = ",json_data)   

                # 응답전문
                response = HttpResponse(json_data, content_type="application/json")
                # CORS 헤더 추가
                response["Access-Control-Allow-Credentials"] = "true"
                # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
                response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

                return response

            
        else:
            ResultData = {
                'status' : '101',
                'error' : '입력 데이터 포맷 오류입니다.'
            }

            # json으로 변환
            json_data = json.dumps(ResultData)
            print("### [OUTPUT] JSON = ",json_data)   

            # 응답전문
            response = HttpResponse(json_data, content_type="application/json")
            # CORS 헤더 추가
            response["Access-Control-Allow-Credentials"] = "true"
            # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
            response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

            return response
        
    #######################################
    # POST 수신아닌 경우
    #######################################    
    ResultData = {
        'status' : '100',
        'error' : '잘못된 호출 입니다.'
    }
    
    # json으로 변환
    json_data = json.dumps(ResultData)
    print("### [OUTPUT] JSON = ",json_data)   
    
    # 응답전문
    response = HttpResponse(json_data, content_type="application/json")
    # CORS 헤더 추가
    response["Access-Control-Allow-Credentials"] = "true"
    # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
    response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

    return response


@csrf_exempt
def manage_position(request):
    print('### [API] manage_position ####################################################')
        
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':        
        
        # json 데이터를 수신합니다.
        data = json.loads(request.body)

        # 데이터를 출력합니다.
        print("Received Data:", data)
                    
        #-------------
        # 업무로직
        #-------------
        if data :
            
            #-------------
            # 입력변수 SET
            #-------------
            
            #거래구분 (신규/갱신/삭제)
            trn_cd        = data.get('trn_cd', None)
            company_id    = data.get('company_id', None)        
            position_id   = data.get('position_id', None)  
            position_name = data.get('position_name', None)  
            reward_skip_yn = data.get('reward_skip_yn', None)
                                    
            print('### [LOG] trn_cd', trn_cd)
            print('### [LOG] company_id', company_id)
            print('### [LOG] position_id', position_id)
            print('### [LOG] position_name', position_name)
            print('### [LOG] reward_skip_yn', reward_skip_yn)
            selectManageDept = ManageDept.objects.filter(
                company_id = company_id,
                is_active='Y'
            ).first()
            if selectManageDept:
                company_name = selectManageDept.company_name
            else:
                company_name = None
            
            #-----------------------------------
            # [신규] 업무로직
            #-----------------------------------
            if trn_cd == 'I' :
                
                try:
                    if ManagePosi.objects.filter(company_id=company_id, posi_id=position_id).exists():

                        ResultData = {
                            'status' : '201',
                            'error' : '[오류] 이미 존재하는 직급ID 입니다.'
                        }

                        # json으로 변환
                        json_data = json.dumps(ResultData)
                        print("### [OUTPUT] JSON = ",json_data)   

                        # 응답전문
                        response = HttpResponse(json_data, content_type="application/json")
                        # CORS 헤더 추가
                        response["Access-Control-Allow-Credentials"] = "true"
                        # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
                        response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

                        return response

                    print('### [LOG] ManagePosi insert')
                    insertManagePosi    = ManagePosi.objects.create(
                        company_id      = company_id,
                        company_name    = company_name,
                        posi_id         = position_id,
                        posi_name       = position_name,
                        reward_skip_yn  = reward_skip_yn,
                        is_active       = 'Y',
                        reg_date        =  datetime.now() 
                    )
                    print('### [LOG] ManagePosi insert success', insertManagePosi.id)
                    #-------------
                    # 출력내용 SET
                    #-------------
                    # 결과 데이터에 리스트와 총 건수를 추가합니다.
                    ResultData = {
                        'status': '000',
                        'error': ''
                    }

                    # json으로 변환
                    json_data = json.dumps(ResultData)
                    print("### [OUTPUT] JSON = ",json_data)   

                    # 응답전문
                    response = HttpResponse(json_data, content_type="application/json")
                    # CORS 헤더 추가
                    response["Access-Control-Allow-Credentials"] = "true"
                    # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
                    response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

                    return response

                except:
                    ResultData = {
                        'status' : '200',
                        'error' : '신규직급 처리시 오류가 발생 했습니다.'
                    }

                    # json으로 변환
                    json_data = json.dumps(ResultData)
                    print("### [OUTPUT] JSON = ",json_data)   

                    # 응답전문
                    response = HttpResponse(json_data, content_type="application/json")
                    # CORS 헤더 추가
                    response["Access-Control-Allow-Credentials"] = "true"
                    # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
                    response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

                    return response
                
            #-----------------------------------
            # [갱신] 업무로직
            #-----------------------------------
            elif trn_cd == 'U' :

                try:
                    
                    selectManagePosi = ManagePosi.objects.filter(company_id=company_id, posi_id=position_id).first()
                    
                    if not selectManagePosi:

                        ResultData = {
                            'status' : '201',
                            'error' : '[오류] 존재하는 않는 직급ID 입니다.'
                        }

                        # json으로 변환
                        json_data = json.dumps(ResultData)
                        print("### [OUTPUT] JSON = ",json_data)   

                        # 응답전문
                        response = HttpResponse(json_data, content_type="application/json")
                        # CORS 헤더 추가
                        response["Access-Control-Allow-Credentials"] = "true"
                        # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
                        response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

                        return response
                    
                    print('### [LOG] selectManagePosi.id', selectManagePosi.id)
                    print('### [LOG] ManagePosi update')
                    updateManagePosi = ManagePosi.objects.get(id=selectManagePosi.id)
                    
                    updateManagePosi.company_id     = company_id
                    updateManagePosi.company_name   = company_name
                    updateManagePosi.posi_id        = position_id
                    updateManagePosi.posi_name      = position_name
                    updateManagePosi.reward_skip_yn = reward_skip_yn
                    updateManagePosi.is_active      = 'Y'
                    updateManagePosi.chg_date       =  datetime.now() 
                    
                    updateManagePosi.save()
                    print('### [LOG] ManagePosi update success')
                    #-------------
                    # 출력내용 SET
                    #-------------
                    # 결과 데이터에 리스트와 총 건수를 추가합니다.
                    ResultData = {
                        'status': '000',
                        'error': ''
                    }

                    # json으로 변환
                    json_data = json.dumps(ResultData)
                    print("### [OUTPUT] JSON = ",json_data)   

                    # 응답전문
                    response = HttpResponse(json_data, content_type="application/json")
                    # CORS 헤더 추가
                    response["Access-Control-Allow-Credentials"] = "true"
                    # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
                    response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

                    return response

                except:
                    ResultData = {
                        'status' : '200',
                        'error' : '갱신직급 처리시 오류가 발생 했습니다.'
                    }

                    # json으로 변환
                    json_data = json.dumps(ResultData)
                    print("### [OUTPUT] JSON = ",json_data)   

                    # 응답전문
                    response = HttpResponse(json_data, content_type="application/json")
                    # CORS 헤더 추가
                    response["Access-Control-Allow-Credentials"] = "true"
                    # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
                    response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

                    return response
                
            #-----------------------------------
            # [삭제] 업무로직
            #-----------------------------------
            elif trn_cd == 'D' :                
                
                try:
                    
                    selectManagePosi = ManagePosi.objects.filter(company_id=company_id, posi_id=position_id).first()
                    
                    if not selectManagePosi:

                        ResultData = {
                            'status' : '201',
                            'error' : '[오류] 존재하는 않는 직급ID 입니다.'
                        }

                        # json으로 변환
                        json_data = json.dumps(ResultData)
                        print("### [OUTPUT] JSON = ",json_data)   

                        # 응답전문
                        response = HttpResponse(json_data, content_type="application/json")
                        # CORS 헤더 추가
                        response["Access-Control-Allow-Credentials"] = "true"
                        # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
                        response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

                        return response
                    
                    print('### [LOG] selectManagePosi.id', selectManagePosi.id)
                    print('### [LOG] ManagePosi delete')
                    deleteManagePosi = ManagePosi.objects.get(id=selectManagePosi.id)
                    
                    deleteManagePosi.company_id = selectManagePosi.id
                    deleteManagePosi.company_name = ' '
                    deleteManagePosi.posi_id = ' '
                    deleteManagePosi.posi_name = ' '
                    deleteManagePosi.reward_skip_yn = ' '
                    deleteManagePosi.is_active = ' '
                    deleteManagePosi.chg_date =  datetime.now() 
                    
                    deleteManagePosi.save()
                    print('### [LOG] ManagePosi delete update success')
                    
                    #-------------
                    # 출력내용 SET
                    #-------------
                    # 결과 데이터에 리스트와 총 건수를 추가합니다.
                    ResultData = {
                        'status': '000',
                        'error': ''
                    }

                    # json으로 변환
                    json_data = json.dumps(ResultData)
                    print("### [OUTPUT] JSON = ",json_data)   

                    # 응답전문
                    response = HttpResponse(json_data, content_type="application/json")
                    # CORS 헤더 추가
                    response["Access-Control-Allow-Credentials"] = "true"
                    # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
                    response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

                    return response

                except:
                    ResultData = {
                        'status' : '200',
                        'error' : '삭제직급 처리시 오류가 발생 했습니다.'
                    }

                    # json으로 변환
                    json_data = json.dumps(ResultData)
                    print("### [OUTPUT] JSON = ",json_data)   

                    # 응답전문
                    response = HttpResponse(json_data, content_type="application/json")
                    # CORS 헤더 추가
                    response["Access-Control-Allow-Credentials"] = "true"
                    # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
                    response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

                    return response
                
            else :
                ResultData = {
                    'status' : '102',
                    'error' : '[거래구분] 코드의 포맷 오류입니다.'
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                print("### [OUTPUT] JSON = ",json_data)   

                # 응답전문
                response = HttpResponse(json_data, content_type="application/json")
                # CORS 헤더 추가
                response["Access-Control-Allow-Credentials"] = "true"
                # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
                response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

                return response

            
        else:
            ResultData = {
                'status' : '101',
                'error' : '입력 데이터 포맷 오류입니다.'
            }

            # json으로 변환
            json_data = json.dumps(ResultData)
            print("### [OUTPUT] JSON = ",json_data)   

            # 응답전문
            response = HttpResponse(json_data, content_type="application/json")
            # CORS 헤더 추가
            response["Access-Control-Allow-Credentials"] = "true"
            # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
            response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

            return response
        
    #######################################
    # POST 수신아닌 경우
    #######################################    
    ResultData = {
        'status' : '100',
        'error' : '잘못된 호출 입니다.'
    }
    
    # json으로 변환
    json_data = json.dumps(ResultData)
    print("### [OUTPUT] JSON = ",json_data)   
    
    # 응답전문
    response = HttpResponse(json_data, content_type="application/json")
    # CORS 헤더 추가
    response["Access-Control-Allow-Credentials"] = "true"
    # 요청 origin 그대로 사용하거나 허용된 origin 중 하나로 설정
    response["Access-Control-Allow-Origin"] = request.headers.get("Origin", "http://localhost:3000")

    return response
    
@csrf_exempt
def AllexportToExcel(request):
    print('### [API] AllexportToExcel ####################################################')
    
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':        
        for key, value in request.POST.items():
            print('### [INPUT] ', key, value)
            
        #-------------
        # 업무로직
        #-------------
        if request.POST['export_data'] == 'member':
            
            try:
                manage_token_id = request.POST['manage_token_id']
                companyId      = request.POST['companyId']
                searchCode     = request.POST['searchCode']
                searchDeptName = request.POST['searchDeptName']
                searchUserName = request.POST['searchUserName']
                if searchCode == "B":
                    token_Count = 1
                else:
                    token_Count = -1
                    

                selectUserTokens = UserTokens.objects.filter(
                    is_active='Y',
                    token_id=manage_token_id,
                    received_tokens__gt=token_Count,  # 이상으로 조건 변경
                    user__is_active=True,
                    user__department_name__icontains=searchDeptName,
                    user__employee_name__icontains=searchUserName,
                    user__company_id = companyId
                ).select_related('user').order_by('-received_tokens')

                # 데이터를 담을 리스트 초기화
                data_list = []

                # 필드별 데이터를 리스트에 담습니다.
                for obj in selectUserTokens:

                    data_list.append({
                        #'user_id': obj.user.id,
                        'employee_name': obj.user.department_name,
                        'employee_name': obj.user.employee_name,
                        'employee_name': obj.user.position_name,
                        'employee_name': obj.user.employee_id,
                        'received_tokens': obj.received_tokens,
                        'my_send_tokens': obj.my_send_tokens,
                        'my_current_tokens': obj.my_current_tokens,
                    })

                if not selectUserTokens:
                    data_list.append({
                        'error': '[결과] 대상이 없습니다',
                    })
                    
                #-------------
                # 출력내용 SET
                #-------------
                # 결과 데이터에 리스트와 총 건수를 추가합니다.
                ResultData = {
                    'status': '200',
                    'data_count': len(data_list),
                    'data_list': data_list,
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 

    
            except:
                ResultData = {
                    'status' : '403',
                    'error' : 'DB 갱신시 오류가 발생 했습니다.'
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 
            
        else:
            ResultData = {
                'status' : '401',
                'error' : '입력 데이터가 없습니다.'
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



#2024.02 My땡큐 마이땡큐
@csrf_exempt
def mythankyou_list_page(request):
    print('### [API] mythankyou_list_page ####################################################')
    
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':        
        for key, value in request.POST.items():
           print('### mythankyou_list_page request.user.id [INPUT] ', request.user.id)
            
        # request.POST.get('pageNumber')    
        page_number = request.POST.get('pageNumber')    
        page_number = int(page_number)
        page_size = 6
        offset = page_number * page_size

        print('### mythankyou_list_page [offset] ', offset)
        #-------------
        # 업무로직
        #-------------
        # result = UserLike.objects.filter(
        #     user_id = request.user.id,
        #     is_active = 'Y',
        # ).values_list('compliment_id', flat=True)
        
        
        # selectUserPraise = UserPraise.objects.filter(is_active='Y')\
        #     .select_related('praise', 'images').annotate(
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
        #             When(compliment_id__in=result, then=1),
        #             default=0,
        #         )  
        #         #compliment_id_COUNT=Count('usercomment__compliment_id', filter=Q(usercomment__compliment_id__is_active='Y'))
        #     ).order_by('-reg_date')[page_number * 10:(page_number + 1) * 10]


        # selectUserPraise = UserPraise.objects.filter(
        #                         is_active='Y',
        #                         praise_id=request.user.id
        #                     ).select_related(
        #                         'praise', 'user'
        #                     ).annotate(
        #                         praise_employee_name=F('praise__employee_name'),
        #                         praise_employee_id=F('praise__employee_id'),
        #                         praise_department_name=F('praise__department_name'),
        #                         praise_position_name=F('praise__position_name'),
        #                         praise_company_name=F('praise__company_name'),
        #                         praise_image_yn=F('praise__image_yn'),
        #                         praise_image=F('praise__image'),
        #                         user_employee_name=F('user__employee_name'),
        #                         user_employee_id=F('user__employee_id'),
        #                         user_department_name=F('user__department_name'),
        #                         user_position_name=F('user__position_name'),
        #                         user_company_name=F('user__company_name'),
        #                         user_image_yn=F('user__image_yn'),
        #                         user_image=F('user__image'),
        #                         image_path=F('images__image_path')
        #                     ).order_by('-reg_date')[page_number * 10:(page_number + 1) * 10]

        # Subquery to get total_notices
        total_notices_subquery = UserNotices.objects.filter(
                                user_id=request.user.id,
                                send_id=OuterRef('user_id'),
                                check_yn='N'
                                ).values('user_id').annotate(notice_count=Count('notice_id')).values('notice_count')[:1]

        # Main query
        selectUserPraise = UserPraise.objects.filter(
            praise_id=request.user.id,
            is_active='Y',
        ).annotate(
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
            total_notices=Subquery(total_notices_subquery),
        ).filter(
            ~Exists(
                UserPraise.objects.filter(
                    user_id=F('user__id'),
                    praise_id=praise_id,
                    is_active='Y',
                    reg_date__gt=F('reg_date')
                )
            )
        ).order_by('-reg_date')[page_number * 5:(page_number + 1) * 5]

        # Execute the query
        
        
        # [page_number * 5:(page_number + 1) * 5]

        print('### !!!!!!!! selectUserPraise', selectUserPraise)

        for row in selectUserPraise.values():
           print(row)

        # 데이터를 담을 리스트 초기화
        data_list = []

        # 필드별 데이터를 리스트에 담습니다.
        for obj in selectUserPraise:
            if obj.chg_date is not None:
                chg_date_str = obj.chg_date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                chg_date_str = None

            if obj.reg_date is not None:
                reg_date_str = obj.reg_date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                reg_date_str = None
                
            # obj.reg_date는 DB에서 가져온 날짜 값입니다
            post_date = humanize.naturaltime(obj.reg_date)              
            #print('[API][LOG] formatted_date', formatted_date)
            
            chg_content = obj.content 
            chg_content = chg_content.replace('\r\n', '<br>')
            chg_content = chg_content.replace('\r\n', '<br>')
            chg_content = chg_content.replace('\r', '<br>')
            chg_content = chg_content.replace('\n', '<br>')
            #print('[VIEW][LOG] chg_content ', chg_content)
            
            data_list.append({
                'compliment_id': obj.compliment_id,
                'praise_id': obj.praise_id,
                'user_id': obj.user_id,
                'user_employee_name': obj.user_employee_name,
                'image_path': obj.image_path,
                'compliment_type': obj.compliment_type,
                'content': escape(chg_content),
                'images_id': obj.images_id,
                'short_content': obj.short_content,
                'tag': escape(obj.tag),
                'emotion_ratio': obj.emotion_ratio,
                'view_count': obj.view_count,
                'comment_count': obj.comment_count,
                'likes_count': obj.likes_count,
                'token_id': obj.token_id,
                'is_active': obj.is_active,
                'chg_date': chg_date_str,
                'reg_date': reg_date_str,
                'user_image_yn' : obj.user_image_yn,
                'user_image' : obj.user_image,
                'user_employee_id' : obj.user_employee_id,
                'user_department_name' : obj.user_department_name,
                'user_position_name' : obj.user_position_name,
                'user_company_name' : obj.user_company_name,
                'praise_image' : obj.praise_image,
                'praise_image_yn' : obj.praise_image_yn,
                'praise_employee_id' : obj.praise_employee_id,
                'praise_employee_name' : obj.praise_employee_name,
                'praise_department_name' : obj.praise_department_name,
                'praise_position_name' : obj.praise_position_name,
                'praise_company_name' : obj.praise_company_name,
                'post_date': post_date
            })
                
        #-------------
        # 출력내용 SET
        #-------------
        # 결과 데이터에 리스트와 총 건수를 추가합니다.
        ResultData = {
            'status': '200',
            'data_count': len(data_list),
            'data_list': data_list,
        }

        # json으로 변환
        json_data = json.dumps(ResultData)
        print("### mythankyou_list_page [OUTPUT] JSON = ",json_data)   

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
    #print("### [OUTPUT] JSON = ",json_data)   
    
    return HttpResponse(json_data, content_type="application/json") 


#2024.02 My땡큐 마이땡큐
@csrf_exempt
def notice_modify(request):
    print('### [API] notice_modify ####################################################')
    
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':        
        for key, value in request.POST.items():
            print('### [notice_modify] ', key, value)
            
        #-------------
        # 업무로직
        #-------------
        if request.POST['sendId']:
            
            try:
                sendId = request.POST['sendId']
                userId = request.POST['userId']
                print("chck notice sendId : " + sendId)
                print("chck notice userId : " + userId)


                UserNotices.objects.filter(user_id=userId, send__id=sendId).update(check_yn='Y')
                
                checkYn = 'N'

                # ORM으로 변경된 부분
                count_result = UserNotices.objects.filter(user_id=userId, send__id=sendId, check_yn=checkYn).count()

                print(count_result)

                ResultData = {
                    'status': '200',
                    'notice_count' : count_result
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 

            except:
                ResultData = {
                    'status' : '403',
                    'error' : 'DB 갱신시 오류가 발생 했습니다.'
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                #print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 
            
        else:
            ResultData = {
                'status' : '401',
                'error' : '입력 데이터가 없습니다.'
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


#2024.02 출석체크 5개 체크
@csrf_exempt
def check_five(request):
    # print('### [API] check_five ####################################################')
    
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':        
        # for key, value in request.POST.items():
        #     print('### [notice_modify] ', key, value)
            
        #-------------
        # 업무로직
        #-------------

        try:
            # 본인 아이디
            myId = request.user.id 

            # 금일 칭찬한 건수
            count = UserPraise.objects.filter(~Q(is_senduc='Y'), user_id=myId, is_active='Y', reg_date__date=timezone.now().date()).aggregate(count=Count('compliment_id')) 
            
            # 출석체크 여부 확인
            afterAddToken = User2.objects.get(id=myId)
            
            # 출석체크 안했으면 N
            addedTokenYn = 'N'
            
            # 출석체크를 한 번도 안했으면 addtoken_date 컬럼의 값이 Null
            if afterAddToken.addtoken_date is None :
                addedTokenYn = 'N'
            else :
                # addtoken_date 컬럼의 일자와 현재일자가 같으면 이미 출석체크함
                if(afterAddToken.addtoken_date.strftime("%Y-%m-%d") == timezone.now().date().strftime("%Y-%m-%d")):
                    addedTokenYn = 'Y'

            # print(count['count'])
            # print("afterAddToken.addtoken_date.strftime()" , afterAddToken.addtoken_date.strftime("%Y-%m-%d"))
            # print("timezone.now().date().strftime()" , timezone.now().date().strftime("%Y-%m-%d"))
            # print(addedTokenYn)

            ResultData = {
                'status': '200',
                'check_five' : count,
                'addedTokenYn' : addedTokenYn
            }

            # json으로 변환
            json_data = json.dumps(ResultData)
            # print("### [OUTPUT] JSON = ",json_data)   

            return HttpResponse(json_data, content_type="application/json") 

        except:
            ResultData = {
                'status' : '202',
                'error' : 'check_five 조회시 오류가 발생 했습니다.'
            }

            # json으로 변환
            json_data = json.dumps(ResultData)
            #print("### [OUTPUT] JSON = ",json_data)   

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
    # print("### [OUTPUT] JSON = ",json_data)   
    
    return HttpResponse(json_data, content_type="application/json") 


#2024.02 출석체크 토큰 충전 +1
@csrf_exempt
def add_token(request):
    # print('### [API] add_token ####################################################')
    
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':        
        # for key, value in request.POST.items():
        #     print('### [notice_modify] ', key, value)
            
        #-------------
        # 업무로직
        #-------------

        try:
            # 본인 아이디 확인
            myId = request.user.id
            
            # 금일 칭찬한 건수
            # praise_count = UserPraise.objects.filter(user_id=myId, is_active='Y', reg_date__date=timezone.now().date()).aggregate(count=Count('compliment_id'))
            # praise_count = UserTokens.objects.get(
            #                 year=datetime.now().strftime("%Y"),
            #                 quarter=datetime.now().strftime("%m"),
            #                 user_id=myId,
            #                 is_active='Y'
            #             )

            # 토큰정보
            today = datetime.now().strftime('%Y%m%d')
            selectManageTokens = ManageTokens.objects.filter(
                Q(start_date__lte=today) & Q(end_date__gte=today)
            ).first()
            
            selectTotalCount = UserPraise.objects.filter(
                ~Q(is_senduc='Y'),
                is_active='Y', 
                token_id = selectManageTokens.id,
                user_id = request.user.id
            ).aggregate(praise_count=Count('praise_id'))
            
            praise_count  = selectTotalCount['praise_count']

            # 출석체크를 한 번도 안했으면 addtoken_date 컬럼의 값이 Null
            user = User2.objects.get(id=myId)
            addtoken_date = user.addtoken_date
            
            chk_addtoken_date = '';
            if(addtoken_date is not None):
                chk_addtoken_date = addtoken_date.strftime("%Y-%m-%d")

            current_date = datetime.now().strftime("%Y-%m-%d")
            addNeedtoken_yn = 'Y'

            if(chk_addtoken_date == current_date): #이미 출석체크함
                addNeedtoken_yn = 'N' 
            
            if(praise_count < 20):
                addNeedtoken_yn = 'A'  # 칭찬 5개 하고 나서 토큰 충전 가능함 > 20개 다 써야 가능함
        

            if(addNeedtoken_yn == 'Y'): #출석체크 대상으로 토큰 부여대상

                chk_update_yn = 'Y'

                if(addNeedtoken_yn == 'Y'):
                    try:
                        user = User2.objects.get(id=myId)
                        user.addtoken_date = timezone.now()
                        user.save()

                        chkYear = datetime.now().strftime("%Y")
                        # print("chk yerar ", chkYear)
                        chkMonth = datetime.now().strftime("%m")
                        # print("chk yerar ", chkMonth)
                        user_tokens = UserTokens.objects.filter(
                            year=datetime.now().strftime("%Y"),
                            quarter=datetime.now().strftime("%m"),
                            user_id=myId,
                            is_active='Y'
                        )
                        # print("chk user_tokens : ", user_tokens)

                        # 필터링된 행의 my_tot_tokens와 my_current_tokens를 각각 1씩 증가시킵니다.
                        user_tokens.update(
                            my_tot_tokens=F('my_tot_tokens') + 1,
                            my_current_tokens=F('my_current_tokens') + 1
                        )

                        chk_update_yn = 'Y'

                    except:
                        chk_update_yn = 'E'
                    

                if(chk_update_yn == 'Y'):
                    user_tokens = UserTokens.objects.filter(
                        year=datetime.now().strftime("%Y"),
                        quarter=datetime.now().strftime("%m"),
                        user_id=myId,
                        is_active='Y'
                    )

                    af_curr_tokens = list(user_tokens.values_list('my_current_tokens', flat=True))
                    af_send_tokens = list(user_tokens.values_list('my_send_tokens', flat=True))
                    af_recv_tokens = list(user_tokens.values_list('received_tokens', flat=True))
                    
                    ResultData = {
                        'status': '200',
                        'chk_update_yn'  : chk_update_yn,
                        'af_curr_tokens' : af_curr_tokens,
                        'af_send_tokens' : af_send_tokens,
                        'af_recv_tokens' : af_recv_tokens,
                        'addNeedtoken_yn'  : addNeedtoken_yn
                    }

                else:

                    ResultData = {
                        'status': '200',
                        'chk_update_yn'  : chk_update_yn,
                        # 'af_curr_tokens' : af_curr_tokens,
                        # 'af_send_tokens' : af_send_tokens,
                        # 'af_recv_tokens' : af_recv_tokens,
                        'addNeedtoken_yn'  : addNeedtoken_yn
                    }

                # json으로 변환
                json_data = json.dumps(ResultData)
                # print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 

            else:

                ResultData = {
                    'status': '200',
                    'chk_update_yn' : 'N', # chk_update_yn = 'N' 출석체크 이미 한 사람
                    'addNeedtoken_yn'  : addNeedtoken_yn
                }

                # json으로 변환
                json_data = json.dumps(ResultData)
                # print("### [OUTPUT] JSON = ",json_data)   

                return HttpResponse(json_data, content_type="application/json") 

        except:
            ResultData = {
                'status' : '202',
                'error' : 'addtoken_date 조회시 오류가 발생 했습니다.'
            }

            # json으로 변환
            json_data = json.dumps(ResultData)
            #print("### [OUTPUT] JSON = ",json_data)   

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
    # print("### [OUTPUT] JSON = ",json_data)   
    
    return HttpResponse(json_data, content_type="application/json") 


#2024.02 크라운 왕관 프로필
@csrf_exempt
def crown_profile(request):
    # print('### [API] crown_profile ####################################################')
    
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':        
        # for key, value in request.POST.items():
        #     print('### [notice_modify] ', key, value)
            
        #-------------
        # 업무로직
        #-------------

        try:
            
            # select * from wbntt.account_manage_tokens where is_active ='Y' order by reg_date desc 
            # 당월의 tokend_id를 확인
            today = datetime.now().strftime('%Y%m%d')
            selectManageTokens = ManageTokens.objects.filter(
                                    Q(start_date__lte=today) & Q(end_date__gte=today),
                                    is_active = 'Y'
                                ).first()
            # print('selectManageTokens.id', selectManageTokens.id)
            
            # 특정 사용자가 속한 회사 ID를 가져오는 서브쿼리
            myId = request.user.id
            subquery_company_id = User2.objects.filter(id=myId).values('company_id')
            company_id = subquery_company_id[0]['company_id']
            # print('subquery_company_id.company_id', subquery_company_id)
            # print('subquery_company_id :: ', company_id)


            selectManageUser = User2.objects.filter(
                is_staff=True,
                is_active=True
            )
                        
            ManageUser_ids = [ManageUser.id for ManageUser in selectManageUser]
            # print('### [LOG] ManageUser_ids', ManageUser_ids)          

            # 메인 쿼리
            subqueryGroupTop3 = UserTokens.objects.filter(
            token_id = selectManageTokens.id,
            is_active='Y',
            user__company_id = company_id
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
                    send_point=ExpressionWrapper(F('my_send_tokens') * 1, output_field=fields.IntegerField())
                ).exclude(
                    user_id__in=ManageUser_ids
                ).values(
                    'user_id', 'chg_date', 'employee_id', 'employee_name', 'company_id', 'company_name', 'department_name','position_id','position_name', 'user_image_yn', 'user_image','recev_point', 'send_point'
                )
                    
            selectUserPraiseGroupTOP3 = subqueryGroupTop3.values('user_id', 'employee_id', 'employee_name', 'company_id', 'company_name', 'department_name', 'position_id', 'position_name', 'user_image_yn', 'user_image').annotate(
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
                
            # 페이지네이션 적용 전 상위 10개 결과만 가져오기
            top_3_selectUserPraiseGroup = selectUserPraiseGroupTOP3[:3]

            # print("top_3_selectUserPraiseGroup : ", top_3_selectUserPraiseGroup)

            my_position = None
            for index, item in enumerate(top_3_selectUserPraiseGroup):
                if item['user_id'] == myId:
                    my_position = index + 1
                    break

            # if my_position is not None:
            #     print(f"내 아이디({myId})는 상위 10에 있으며, {my_position}번째입니다.")
            # else:
            #     print(f"내 아이디({myId})는 상위 10에 없습니다.")            

            ResultData = {
                'status': '200',
                'my_position' : my_position,
            }

            # json으로 변환
            json_data = json.dumps(ResultData)
            # print("### [OUTPUT] JSON = ",json_data)   

            return HttpResponse(json_data, content_type="application/json") 

        except:
            ResultData = {
                'status' : '202',
                'error' : 'DB 조회시 오류가 발생 했습니다.'
            }

            # json으로 변환
            json_data = json.dumps(ResultData)
            #print("### [OUTPUT] JSON = ",json_data)   

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
    # print("### [OUTPUT] JSON = ",json_data)   
    
    return HttpResponse(json_data, content_type="application/json") 


#2024.04 투데이 땡큐 등록 및 해제
@csrf_exempt
def change_todaythankyou(request):
    print('### [API] change_todaythankyou ####################################################')
    
    #######################################
    # POST 수신
    #######################################
    if request.method == 'POST':        
        # for key, value in request.POST.items():
        #     print('### [notice_modify] ', key, value)
            
        #-------------
        # 업무로직
        #-------------

        try:

            # print("######## change_todaythankyou compliment_id", request.POST['compliment_id'])
            # print("######## change_todaythankyou chg_yn", request.POST['chg_yn'])
            
            chgComplimentId = request.POST['compliment_id']

            if  request.POST['chg_yn'] == 'Y' :
                UserPraise.objects.filter(compliment_id=chgComplimentId).update(
                                                                                    todaythanks_date=timezone.now(),
                                                                                    todaythanks_showyn='Y'
                                                                                )
                updated = 'Y'

            elif  request.POST['chg_yn'] == 'N' :
                UserPraise.objects.filter(compliment_id=chgComplimentId).update(
                                                                                    todaythanks_showyn=None
                                                                                )
                updated = 'N'
                            

            ResultData = {
                'status': '200',
                'updated' : updated,
            }

            # json으로 변환
            json_data = json.dumps(ResultData)
            # print("### [OUTPUT] JSON = ",json_data)   

            return HttpResponse(json_data, content_type="application/json") 

        except:
            ResultData = {
                'status' : '202',
                'error' : 'DB 조회시 오류가 발생 했습니다.'
            }

            # json으로 변환
            json_data = json.dumps(ResultData)
            #print("### [OUTPUT] JSON = ",json_data)   

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
    # print("### [OUTPUT] JSON = ",json_data)   
    
    return HttpResponse(json_data, content_type="application/json") 