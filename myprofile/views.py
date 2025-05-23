####################################################################
# 업무제목 : 땡큐토큰 myprofile/view 업무
# 프로그램 : view.py
# ------------------------------------------------------------------
# 2023-12-11 김대영 최초개발
# 2024-01-04 김대영 관리자 회원정보 수정기능 추가
# 2024-03-04 윤준영 출석체크 기능
# 2024-04-01 윤준영 보낸토큰 분기처리
# 2024-06-20 윤준영 UC메신저 기능
# 2024-12-10 VTI   compress image when upload
# 2024-12-18 VTI   integrate feature upload image to CDN
# 2025-04-24 VTI   fix logout flow and change initial record limit from 6 to 12
####################################################################
from django.shortcuts import render, redirect, HttpResponse
from myprofile.models import User
from myprofile.models import UserTokens, UserPraise, UserNotices, UserComment, UserImages
from myprofile.models import ManageTokens, ManageDept, ManagePosi, AccessLog, UserLike, BefInsUcmsg
from myprofile.models import User as User2
from django.db.models import Subquery, OuterRef


from django.db.models import Q, BooleanField, When as When2, Case as Case2
from django.db.models import QuerySet
from django.db.models.query import RawQuerySet
from django.db.models.expressions import Case
from django.db.models.query import When

from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required

# from django.contrib.auth import login as django_login, logout as django_logout, authenticate
from django.contrib import auth
from .forms import LoginForm
from datetime import datetime
import math

from django.conf import settings
from django.core.files.storage import FileSystemStorage

from django.core.files.base import ContentFile
from PIL import Image
from io import BytesIO
import os
from django.db.models import F, Sum
from django.db.models.functions import Coalesce

from datetime import date
from django.utils.html import strip_tags
#import datetime
from django.middleware.csrf import rotate_token
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.html import escape

#def signin(request):
#    return render(request, 'accounts/signin.html')

#def signup(request):
#    return render(request, 'accounts/signup.html')

from django.views.decorators.csrf import csrf_protect

#@csrf_protect


from django.views.decorators.csrf import csrf_exempt

import hashlib
from cryptography.fernet import Fernet
#pip install pycryptodome
#import Crypto
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import binascii
import base64

import json

import logging
from django.urls import reverse
from django.contrib.sessions.models import Session
import time

from django.utils import timezone
from datetime import datetime, timedelta  # timedelta를 import 추가

from home.decorators import measure_execution_time, block_profiler
from home.utils import compress_image, upload_to_cdn
from home.services.tk_list import get_unprocessed_messages, process_single_message
from home.services.rankList import get_active_tokens

logger = logging.getLogger('django')
#logger.info("test-info")
#logger.error('This is an error message')

#----------------------\
# 암호화
#----------------------\
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

#----------------------\
# 패딩 함수 추가 (PKCS7 패딩 구현)
#----------------------\
def pad(data, block_size):
    padding = block_size - (len(data) % block_size)
    return data + bytes([padding] * padding)

#----------------------\
# 복호화
#----------------------\
def DecryptByAES256(encrypted_text, password):
    ue = "utf-8"

    # key 및 iv 설정 (동일한 크기 유지)
    pwdBytes = password.encode(ue)
    keyBytes = pwdBytes.ljust(32, b'\0')  # 키를 32 바이트로 맞춥니다.
    IVBytes = pwdBytes.ljust(16, b'\0')  # 초기화 벡터를 16 바이트로 맞춥니다.

    # Base64 디코딩
    encrypted_data = base64.b64decode(encrypted_text)

    # 복호화 수행
    rijndael = AES.new(keyBytes, AES.MODE_CBC, IVBytes)
    decrypted_data = rijndael.decrypt(encrypted_data)

    # PKCS7 언패딩 수행
    decrypted_data = unpad(decrypted_data)

    # 결과를 문자열로 디코딩
    decrypted_text = decrypted_data.decode(ue)

    return decrypted_text

#----------------------\
# 언패딩 함수 추가 (PKCS7 언패딩 구현)
#----------------------\
def unpad(data):
    padding = data[-1]
    return data[:-padding]

@csrf_exempt
def signin(request):
    # print("### [VIEW][LOGIN] signin ####################################################")
    
    #if  request.user.is_authenticated:
    #    # 로그인 상태라면, 메인페이지로 이동합니다.
    #    return redirect("/")
    
    # print('### [VIEW][LOGIN] request.method', request.method)
    
    
    if request.method == 'POST':
        #print('username = ', request.POST['username'])
        
        if request.POST.get('username', None):
            # print('### [VIEW][LOGIN] post get')
            username = request.POST['username']
            
        else:
            #print('json data ', request.body)
            # -----------------------------
            # POST 요청에서 JSON 데이터를 추출합니다.
            # -----------------------------
            try:
                data = json.loads(request.body)
                
                # 데이터를 출력합니다.
                #print("Received Data:", data)

                # 'key1'의 결과를 가져옵니다.
                username = data.get('userId', None)
                
            except:
                if  request.user.is_authenticated:
                  
                    # print('### [VIEW][LOGIN] re btn login success', request.user.username)           
                    return redirect('/')
              
                error = "[안내] 로그인 후 이용 가능 합니다."
                return render(request, 'page_error.html', {'error': error})
            
            #if username is not None:
            #    # 결과를 출력합니다.
            #    print("Username Result:", username)
            
            ######################################################
            # SSO 개발 START
            ######################################################
            #print('username ', username)        

            encrypted_username     = username
            password = 'ThankyouToken!@#'

            #encrypted_result = EncryptByAES256(text, password)
            #print('Encrypted:', encrypted_result)

            decrypted_result = DecryptByAES256(encrypted_username, password)
            #print('Decrypted:', decrypted_result)

            username = decrypted_result
            #print('username Decrypted:', username)

            # 접속 IP
            client_ip = request.META.get('REMOTE_ADDR')
            # 웹 정보
            user_agent = request.META.get('HTTP_USER_AGENT')
            # 로그기록        
            logger.info(f'### User Login : {username} {client_ip} {user_agent}')


            #----------------------------------------
            # 현재 로그인 여부체크
            #----------------------------------------            
            if  request.user.is_authenticated:
                if request.user.username != username:
                    print('### [VIEW][LOGIN] logout ',request.user.username)
                    # 로그인 상태라면, 로그아웃 처리
                    auth.logout(request)
                    
                else :
                    # print('### [VIEW][LOGIN] re login success ', username)           
                    return redirect('/')
                    
            selectUser2 = User2.objects.filter(username=username).first()

            if selectUser2 is None:
                print('### [VIEW][LOGIN] login error', username)  
                
                # ---------------
                # AccessLog 적재
                # ---------------
                try :
                    # AccessLog 모델에 데이터 추가
                    insertAccessLog = AccessLog(
                        user_id='0',
                        user_name=username,
                        user_ip=client_ip,  # 예시: IPv4 주소를 바이트 형태로 저장
                        user_agent=user_agent,
                        user_access_time=datetime.now(),
                        requested_url='signin'
                    )
                    insertAccessLog.save()  # 데이터베이스에 저장
                except:
                    print("[LOG] Access Log Error")
                
                return render(request, 'accounts/signin.html', {'error': f'[오류] 존재하지 않는 사번ID 입니다.'})

            if selectUser2 is not None:
                # print('### [VIEW][LOGIN] login success', username)     
                              
                # ---------------
                # AccessLog 적재
                # ---------------
                try :
                    # AccessLog 모델에 데이터 추가
                    insertAccessLog = AccessLog(
                        user_id=selectUser2.id,
                        user_name=username,
                        user_ip=client_ip,  # 예시: IPv4 주소를 바이트 형태로 저장
                        user_agent=user_agent,
                        user_access_time=datetime.now(),
                        requested_url='signin'
                    )
                    insertAccessLog.save()  # 데이터베이스에 저장
                except:
                    print("[LOG] Access Log Error")
                
                rotate_token(request)
                auth.login(request, selectUser2)
                return redirect('/')

            else:
                return render(request, 'accounts/signin.html', {'error': '[오류] 로그인 검증이 잘못 되었습니다.'})
        
            ######################################################
            # SSO 개발 END
            ######################################################
            
        #----------------------------------------
        # [일반로그인] 업무처리
        #----------------------------------------
        
        username = request.POST['username']
        password = request.POST['password']
        
        # 접속 IP
        client_ip = request.META.get('REMOTE_ADDR')
        # 웹 정보
        user_agent = request.META.get('HTTP_USER_AGENT')
        # 로그기록        
        logger.info(f'### [VIEW][LOGIN] User Login : {username} {client_ip} {user_agent}')

        #----------------------------------------
        # User2 모델에 username이 존재하는지 확인하기
        #----------------------------------------
        selectUser2 = User2.objects.filter(username=username).first()

        if selectUser2 is None:
            return render(request, 'accounts/signin.html', {'error': f'[오류] 존재하지 않는 사번ID 입니다.'})

        #-------------
        # 비밀번호 검증
        #-------------
        user = auth.authenticate(request, username=username, password=password)
        
        if user is None :
            error_count = request.session.get('error_count', 0)
            print('[VIEW][LOG] error_count POST ', error_count)
            
            if error_count >= 5:
                return render(request, 'accounts/signin.html', {'error': '[오류] 비밀번호 가능 횟수를 초과 했습니다 관리자에게 문의 바랍니다.'})
            else:
                request.session['error_count'] = error_count + 1
                prt_error_count = request.session.get('error_count', 0)
                return render(request, 'accounts/signin.html', {'error': f'[오류] 비밀번호가 불일치 합니다. (최대 5회 중 {prt_error_count}회 시도 했습니다.)'})

        # print('### login ty', user.ty)
        #-------------
        # 회원대기 페이지 이동
        #-------------
        if user.ty == 0 or user.ty is None:
            return render(request, 'accounts/signCheck.html')
        
        if user is not None:
            # 로그인 성공 후 CSRF 토큰 갱신
            # rotate_token(request)
            
            auth.login(request, user)
            # print('### [VIEW][LOGIN] Basic login ', user)           
            
            return redirect('/')
        else:
            return render(request, 'accounts/signin.html', {'error': '[오류] 로그인 정보가 잘못 되었습니다.'})
    else:
        
        if  request.user.is_authenticated:
            # 로그인 상태라면, 메인페이지로 이동합니다.
            # print("### [VIEW][LOGIN] re login user (get)", request.user.username)
            return redirect('/')

        else:
            # print("### [VIEW][LOGIN] login not user")
            # 1초 동안 대기
            time.sleep(2)
            
            return render(request, 'accounts/signin.html')
            
def signup(request):
    # print("### [VIEW] signup ####################################################")
    
    # 로그인 성공 후 CSRF 토큰 갱신
    rotate_token(request)
    
    if request.method == 'POST':
        #print("password1", request.POST['password1'])
        #print("password2", request.POST['password2'])
        
        #for key, value in request.POST.items():
        #    print(key, value)
        
        if request.POST['password1'] == request.POST['password2']:
            
            # request.POST['username'] 값을 가져오기
            username = request.POST['username']
            # User2 모델에 username이 존재하는지 확인하기
            if User2.objects.filter(username=username).exists():
                error = "[오류] 이미 존재하는 사번ID 입니다."
                return render(request, 'accounts/signup.html', {'error': error})
            
            try:
                #부서명 SET
                dept_id = request.POST['department_id']
                company_id = request.POST['company_id']
                posi_id = request.POST['position_id']

                selectManageDept = ManageDept.objects.get(dept_id=dept_id, company_id = company_id)
                dept_name  = selectManageDept.dept_name
                company_name  = selectManageDept.company_name
                
                # print('### [VIEW][LOG] dept_name', dept_name)
                # print('### [VIEW][LOG] company_name', company_name)
                
                selectManagePosi = ManagePosi.objects.get(posi_id=posi_id, company_id = company_id)
                posi_name =  selectManagePosi.posi_name
                
                # print('### [VIEW][LOG] posi_name', posi_name)

                
                #if 'email' in request.POST and request.POST['email']:
                #   input_email = request.POST['email']
                #else :
                #    input_email = ''
                    
                #print('### [VIEW][LOG] input_email', input_email)
                
                user = User.objects.create_user(
                    request.POST['username'],
                	password=request.POST['password1'],
                	ty = '1', # 승인여부 판단
                    email=' ',
                    birth_date = '00010101',
                    employee_id = request.POST['username'],
                    employee_name = request.POST['employee_name'],
                    department_id = request.POST['department_id'],
                    department_name = dept_name,
                    position_id = request.POST['position_id'],
                    position_name = posi_name,
                    company_id = request.POST['company_id'],
                    company_name = company_name
                )
                
                # 회원대기 페이지 이동 ty=0 수동승인 - 2023-07-24
                #print('### login.ty sign up ', user.ty)    
                #print('### check ###')
                #return render(request, 'accounts/signCheck.html')
                
                # 정상등록
                auth.login(request, user)
                return redirect('/')
            
            except:
                error = "[오류] 입력된 내용이 잘못 되었습니다."
                return render(request, 'accounts/signup.html', {'error': error})
        else:
            error = "비밀번호가 일치하지 않습니다."
            return render(request, 'accounts/signup.html', {'error': error})
        
    return render(request, 'accounts/signup.html')

@csrf_exempt
def signManager(request):
    # print("### [VIEW][LOGIN] signManager ####################################################")
    
    #if  request.user.is_authenticated:
    #    # 로그인 상태라면, 메인페이지로 이동합니다.
    #    return redirect("/")
    
    # print('### [VIEW][LOGIN] request.method', request.method)
    
    if request.method == 'POST':           
            
        #----------------------------------------
        # [일반로그인] 업무처리
        #----------------------------------------
        
        username = request.POST['username']
        password = request.POST['password']
        
        # 접속 IP
        client_ip = request.META.get('REMOTE_ADDR')
        # 웹 정보
        user_agent = request.META.get('HTTP_USER_AGENT')
        # 로그기록        
        logger.info(f'### [VIEW][LOGIN] User Login : {username} {client_ip} {user_agent}')

        #----------------------------------------
        # User2 모델에 username이 존재하는지 확인하기
        #----------------------------------------
        selectUser2 = User2.objects.filter(username=username).first()

        if selectUser2 is None:
            return render(request, 'accounts/signin.html', {'error': f'[오류] 존재하지 않는 사번ID 입니다.'})

        #-------------
        # 비밀번호 검증
        #-------------
        user = auth.authenticate(request, username=username, password=password)
        
        if user is None :
            error_count = request.session.get('error_count', 0)
            print('[VIEW][LOG] error_count POST ', error_count)
            
            if error_count >= 5:
                return render(request, 'accounts/signin.html', {'error': '[오류] 비밀번호 가능 횟수를 초과 했습니다 관리자에게 문의 바랍니다.'})
            else:
                request.session['error_count'] = error_count + 1
                prt_error_count = request.session.get('error_count', 0)
                return render(request, 'accounts/signin.html', {'error': f'[오류] 비밀번호가 불일치 합니다. (최대 5회 중 {prt_error_count}회 시도 했습니다.)'})

        # print('### login ty', user.ty)
        #-------------
        # 회원대기 페이지 이동
        #-------------
        if user.ty == 0 or user.ty is None:
            return render(request, 'accounts/signCheck.html')
        
        if user is not None:
            # 로그인 성공 후 CSRF 토큰 갱신
            # rotate_token(request)
            
            auth.login(request, user)
            # print('### [VIEW][LOGIN] Basic login ', user)           
            
            return redirect('/')
        else:
            return render(request, 'accounts/signin.html', {'error': '[오류] 로그인 정보가 잘못 되었습니다.'})
    else:
        
        print("### [VIEW][LOGIN] login not user")
        return render(request, 'accounts/signManager.html')

def logout(request):
    print("### [VIEW] logout ####################################################")
    
    # 로그인 성공 후 CSRF 토큰 갱신
    rotate_token(request)
    
    if request.method == 'POST':
        auth.logout(request)
        return redirect('/')
    return render(request, 'accounts/signManager.html')


@login_required(login_url='/accounts/signManager/')
@measure_execution_time
def myprofile(request):
    print("### [VIEW] myprofile ####################################################")
    
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
    else : 
        manage_token_id = 0


    if request.user.id != 15893:

        one_month_ago = timezone.now() - timedelta(days=61) #20240814에 모모콘 활성화 때문에 61로 변경

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

    # print('[VIEW][LOG] manage_token_id ', manage_token_id)                
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
        # print("### 토큰 정상필요")
        baiscManageTokens = ManageTokens.objects.filter(
            is_active='Y'
        ).order_by('-end_date').first()
        
        #error = "[안내] 관리자에게 문의 요청 드립니다. 발행된 토큰이 없습니다"
        #return render(request, 'page_error.html', {'error': error})
    
    # print('### baiscManageTokens.id', baiscManageTokens.id)
    
    if int(baiscManageTokens.id) == int(manage_token_id):
        manage_token_id = 0
        # print('### chg manage_token_id', manage_token_id)
    
    if manage_token_id == 0:
        selectManageTokens = ManageTokens.objects.filter(
            Q(start_date__lte=today) & Q(end_date__gte=today),
            is_active = 'Y'
        ).first()
        
        if not selectManageTokens:
            # print("### 토큰 정상필요 selectManageTokens")
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

    # print('### selectManageTokens id ', selectManageTokens.id)
    # print('### selectManageTokens token_prev ', token_prev)
    # print('### selectManageTokens token_next ', token_next)

    #-------------
    # 칭찬정보
    #-------------
    
    result = UserLike.objects.filter(
        user_id = request.user.id,
        is_active = 'Y',
    ).values_list('compliment_id', flat=True)
        
    selectUserPraise = UserPraise.objects.filter(is_active='Y', user_id = request.user.id, token_id = selectManageTokens.id)\
        .select_related('praise', 'images').annotate(
            praise_employee_name=F('praise__employee_name'),
            praise_position_name=F('praise__position_name'),
            praise_company_name=F('praise__company_name'),
            praise_department_name=F('praise__department_name'),
            praise_image_yn=F('praise__image_yn'),
            praise_image=F('praise__image'),
            user_employee_name=F('user__employee_name'),
            user_position_name=F('user__position_name'),
            user_company_name=F('user__company_name'),
            user_department_name=F('user__department_name'),
            user_image_yn=F('user__image_yn'),
            user_image=F('user__image'),
            image_path=F('images__image_path'),
            like_yn=Case(
                When(compliment_id__in=result, then=1),
                default=0,
            ) 
        ).order_by('-reg_date')


    paginator = Paginator(selectUserPraise, 500)
    page = request.GET.get('page')
    send_posts = paginator.get_page(page)
    
    # 특수문자 개선
    for post in send_posts:
        post.content = post.content.replace('\r\n', '<br>')
        post.content = post.content.replace('\r\n', '<br>')
        post.content = post.content.replace('\r', '<br>')
        post.content = post.content.replace('\n', '<br>')
    
    selectUserPraise = UserPraise.objects.filter(is_active='Y', praise_id = request.user.id, token_id = selectManageTokens.id)\
        .select_related('praise', 'images').annotate(
            praise_employee_name=F('praise__employee_name'),
            praise_position_name=F('praise__position_name'),
            praise_company_name=F('praise__company_name'),
            praise_department_name=F('praise__department_name'),
            praise_image_yn=F('praise__image_yn'),
            praise_image=F('praise__image'),
            user_employee_name=F('user__employee_name'),
            user_position_name=F('user__position_name'),
            user_company_name=F('user__company_name'),
            user_department_name=F('user__department_name'),
            user_image_yn=F('user__image_yn'),
            user_image=F('user__image'),
            image_path=F('images__image_path'),
            like_yn=Case(
                When(compliment_id__in=result, then=1),
                default=0,
            ) 
        ).order_by('-reg_date')
        
            
    paginator = Paginator(selectUserPraise, 500)
    page = request.GET.get('page')
    recv_posts = paginator.get_page(page)
    
    # 특수문자 개선
    for post in recv_posts:
        #print('### before ', post.content )       
        post.content = post.content.replace('\r\n', '<br>')
        post.content = post.content.replace('\r\n', '<br>')
        post.content = post.content.replace('\r', '<br>')
        post.content = post.content.replace('\n', '<br>')
        #print('### after ', post.content )
        
        
    #for post in recv_posts:
    #    print('### post ', post.content)        
            
    #-------------
    # 사용자정보
    #-------------
    selectUser = User2.objects.get(id=request.user.id)
    
    #-------------
    # 토큰정보
    #-------------
    #today = datetime.now().strftime('%Y%m%d')
    #selectManageTokens = ManageTokens.objects.filter(
    #    Q(start_date__lte=today) & Q(end_date__gte=today)
    #).first()

    toeknYear    = selectManageTokens.year
    toeknQuarter = selectManageTokens.quarter
    
    selectUserTokens = UserTokens.objects.filter(
                    user_id=request.user.id,
                    year=toeknYear,
                    quarter=toeknQuarter,
                    is_active='Y'
                ).first()
                
    # -----------    
    # 진척률 계산  
    # -----------
    # 시작일과 종료일
    start_date = selectManageTokens.start_date
    end_date = selectManageTokens.end_date 

    # 오늘 날짜
    today = datetime.now().date()

    # 종료일까지 남은 기간 계산
    start_date = datetime.strptime(start_date, '%Y%m%d')
    end_date = datetime.strptime(end_date, '%Y%m%d')
    
    if manage_token_id == 0:
        remaining_days = (end_date.date() - today).days + 1
    else :
        remaining_days = 0
    
    # 진행률 계산
    total_days = (end_date.date() - start_date.date()).days
    progress_percentage = ((total_days - remaining_days) / total_days) * 100
    progress_percentage = math.ceil(progress_percentage) # math.ceil() 함수는 소수점 이하를 올림하여 정수로 반환

    # 결과 출력z
    #print(f"진행률: {progress_percentage:.2f}%")
    #print(f"종료까지 남은 기간: {remaining_days}일")
        
    #-------------
    # 이미지 출력SET
    #-------------
    selectUserImages = UserImages.objects.filter(is_open='Y', is_active='Y').order_by('-reg_date')
    
    paginator = Paginator(selectUserImages, 100)
    page = request.GET.get('page')
    images = paginator.get_page(page)
                   
    #-------------
    # 소속장여부 출력SET
    #-------------
    selectuserReward = ManagePosi.objects.filter(
        is_active  = 'Y',
        company_id = request.user.company_id,
        posi_id    = request.user.position_id
    ).first()

    if selectuserReward:
        # print('### user selectuserReward', selectuserReward.reward_skip_yn)
        if selectuserReward.reward_skip_yn == "Y" :
            reward_skip_yn = "Y"
        else :
            reward_skip_yn = "N"
    else :  
        reward_skip_yn = "N"
    
    # userPositionName = selectUser.position_name # 본부장 직급이면 100개 표시 2024.04.04
    chkInsTokYn = User2.objects.filter(
                                        Q(position_name__contains='본부장') | Q(position_name__contains='부행장'),
                                        ~Q(id=5256),
                                        id=request.user.id,
                                        company_id=20    
                                    ).count()

    if request.user.id == 15893 : #회장님
        remainTokYn = "Y"
    else :
        if chkInsTokYn > 0 :
            remainTokYn = "Y"
        else :
            remainTokYn = "N"
    
    #-------------
    # 모모콘P 7, 8월 포인트 합
    #-------------

    total_momocon_tokens = UserTokens.objects.filter(
                    user_id=request.user.id,
                    is_active='Y',
                    token_id__in=['19', '20'],
                    ).aggregate(total_momocon_tokens=Sum(F('my_send_tokens') + F('received_tokens')))['total_momocon_tokens']

    # total_tokens 값이 None이면 기본값 0으로 설정
    total_momocon_tokens = total_momocon_tokens or 0
    # print("$$$ total_momocon_tokens : ", total_momocon_tokens)
                        
    return render(request, 'myprofile.html', {'info':selectUser, 'remainTokYn':remainTokYn, 'reward_skip_yn':reward_skip_yn,'tokens':selectUserTokens,'images':images ,'recv':recv_posts,'send':send_posts, 'manageToken':selectManageTokens, 'progress':progress_percentage,'remaining_days':remaining_days,'token_prev':token_prev,'token_next':token_next, 'total_momocon_tokens':total_momocon_tokens})


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

@login_required(login_url='/accounts/signManager/')
def myprofileModify(request):
    print("### [VIEW] myprofileModify ####################################################")
    
    if request.method == 'POST':
        
        #for key, value in request.POST.items():
        #    print(key, value)
            
        #for key, file in request.FILES.items():
        #    print(key, file)
                
        if 'form_password' in request.POST:
            print('### [VIEW][LOG] Password')
            
            cur_password = request.POST["password0"]
            new_password = request.POST["password1"]

            # 현재 비밀번호 확인
            user = auth.authenticate(request, username=request.user.username, password=cur_password)
            if user is not None:
                print('### [VIEW][LOG] User Change Password')
                
                # Check if the old password is correct.
                user = User.objects.get(username=request.user.username)

                # Change the user's password.
                user.set_password(new_password)
                user.save()

                return redirect('/')
            else:
                print('### [VIEW][LOG] User Fail Password')
                
                # 현재 비밀번호가 일치하지 않는 경우
                error = "[001] 현재 비밀번호가 불일치 합니다."
                return render(request, 'page_error.html', {'error': error}) 
            
        else :
            
            try:
                updateUser = User2.objects.get(id=request.user.id)

                #################################################
                # 이미지 파일 업로드
                #################################################
                # print("###!!!!@@@@@@@@@@@@@@ input_formFile ==========", request.FILES.get('input_formFile'))
                
                if (request.FILES.get('input_formFile') != None):
                    # print("### [VIEW][Image] input_formFile ==========")
                    formFile = request.FILES['input_formFile']
                    today = date.today().strftime("%Y%m%d")
                    now = datetime.now()
                    time_string = now.strftime("%H%M%S")
                    path = 'user_' + str(request.user.id) + '/' + today
                    filename = time_string + '_' + formFile.name
                        
                    # 저장될 파일 경로
                    if ('profile_bee' in formFile.name):
                        path = '/static/assets/img/' + formFile.name
                        updateUser.image_yn         = 'Y'
                        updateUser.image            = path
                    else:
                        # 파일 저장 후, 저장된 경로를 출력
                        filePath = save_image(formFile, path, filename)
                        fileYn   = 'Y'
                        updateUser.image_yn         = fileYn
                        updateUser.image            = filePath
                    
                    # 이미지 저장                   
                    

                #################################################
                # DB UPDATE
                #################################################
                #print('### updateUser ')
                if request.user.is_superuser :
                    updateUser.employee_name    = request.POST['input_employee_name']
                    updateUser.employee_id      = request.POST['base_employee_id']                    
                    company_id                  = request.POST['input_company_id']                    
                    #부서명 SET
                    dept_id                     = request.POST['input_department_id']    
                    #print (dept_id)
                    #print (company_id)
                    selectManageDept = ManageDept.objects.get(dept_id=dept_id,company_id = company_id )
                    #print('### selectManageDept.dept_name', selectManageDept.dept_name )
                    updateUser.department_id    = dept_id
                    updateUser.department_name  = selectManageDept.dept_name
                    
                    updateUser.company_id       = selectManageDept.company_id
                    updateUser.company_name     = selectManageDept.company_name
                    
                    posi_id = request.POST['input_position_id']    
                    selectManagePosi = ManagePosi.objects.get(posi_id=posi_id, company_id = company_id)
                    #print('### selectManagePosi.posi_name', selectManagePosi.posi_name )
                    updateUser.position_id       = posi_id
                    updateUser.position_name     = selectManagePosi.posi_name
                
                #updateUser.email            = request.POST['input_email']
                updateUser.chg_date         = datetime.now()
                updateUser.save()
            
                return redirect('/')
            
            except Exception as e:
                print (str(e))
                error = "[오류] 입력이 잘못 되었습니다."
                info = {'error': error,
                           'employee_name': request.POST.get('input_employee_name', ''),
                           'employee_id': request.POST.get('base_employee_id', ''),
                           'department_name': request.POST.get('input_department_name', ''),
                           'email': request.POST.get('input_email', '')}

                return render(request, 'myprofileModify.html', {'info':info,})
            
    
    #----------
    # 업무로직
    #----------
    info = User2.objects.get(id=request.user.id)
    
    return render(request, 'myprofileModify.html', {'info':info,})


@login_required(login_url='/accounts/signManager/')
def signprofileModify(request):
    print("### [VIEW] signprofileModify ####################################################")
    
    if request.method == 'POST':
        
        for key, value in request.POST.items():
            print(key, value)
            
        for key, file in request.FILES.items():
            print(key, file)

            
        try:
            updateUser = User2.objects.get(id=request.POST['sign_id'])

            #################################################
            # 이미지 파일 업로드
            #################################################
            if request.FILES.get('sign_formFile'):
                # print("### [VIEW][Image] sign_formFile ==========")
                formFile = request.FILES['sign_formFile']
                today = date.today().strftime("%Y%m%d")
                now = datetime.now()
                time_string = now.strftime("%H%M%S")
                path = 'user_' + str(request.user.id) + '/' + today
                filename = time_string + '_' + formFile.name

                # 저장될 파일 경로
                if ('profile_bee' in formFile.name):
                    path = '/static/assets/img/' + formFile.name
                    updateUser.image_yn         = 'Y'
                    updateUser.image            = path
                else:
                    # 파일 저장 후, 저장된 경로를 출력
                    filePath = save_image(formFile, path, filename)
                    fileYn   = 'Y'
                    updateUser.image_yn         = fileYn
                    updateUser.image            = filePath

            #################################################
            # DB UPDATE
            #################################################
            
            if request.user.is_superuser :
                updateUser.employee_id      = request.POST['sign_employee_id']
                updateUser.employee_name    = request.POST['sign_employee_name']
                
                updateUser.department_id    = request.POST['sign_department_id']    
                updateUser.department_name  = request.POST['sign_department_name']    

                updateUser.position_id       = request.POST['sign_position_id']    
                updateUser.position_name     = request.POST['sign_position_name']    
            
            updateUser.chg_date         = datetime.now()
            updateUser.save()
        
            print('### update User success')
            return redirect('manageSingup')
        
        except:
            print('### update User error')
            
            error = "[오류] 입력이 잘못 되었습니다."
            return render(request, 'page_error.html', {'error': error})  
            
    
    #----------
    # 업무로직
    #----------    
    error = "[오류] 입력이 잘못 되었습니다."
    return render(request, 'page_error.html', {'error': error})  