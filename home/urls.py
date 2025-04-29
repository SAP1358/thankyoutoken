####################################################################
# 업무제목 : 땡큐토큰 API 업무
# 프로그램 : urls.py
# ------------------------------------------------------------------
# 2023-12-11 김대영 최초개발
# 2023-12-22 김대영 엑셀일괄 다운로드 추가
# 2024       윤준영 개선 및 추가
####################################################################

from django.contrib import admin
from django.urls import path, include
from myprofile.models import User
from . import views, apis

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    ##################################################
    # VIEW 업무처리
    ##################################################
    path('dev/'     , views.dev, name = "dev"),
    path('apitest/' , views.apitest, name = "apitest"),
    path('htmltest/', views.htmltest, name = "htmltest"),
    
    path('praiseList/'       , views.praiseList, name="praiseList"),
    path('praiseRegedit/'    , views.praiseRegedit, name="praiseRegedit"),
    
    path('praiseModify/<int:compliment_id>', views.praiseModify, name="praiseModify"),
    path('praiseDetail/<int:compliment_id>', views.praiseDetail, name="praiseDetail"),
    path('praiseDelete/<int:compliment_id>', views.praiseDelete, name="praiseDelete"),
    
    
    path('manageMain/'       , views.manageMain, name="manageMain"),
    path('manageImage/'      , views.manageImage, name="manageImage"),
    
    path('manageTokens/'     , views.manageTokens, name="manageTokens"),
    path('manageTokensGroup/'      , views.manageTokensGroup,   name="manageTokensGroup"),
    
    path('manageThankyouWeeks/'    , views.manageThankyouWeeks, name="manageThankyouWeeks"),

    path('manageUcExcelupload/'    , views.manageUcExcelupload, name="manageUcExcelupload"),
    
    path('manageMember/'     , views.manageMember, name="manageMember"),
    path('manageRank/'       , views.manageRank, name="manageRank"),
    path('manageSingup/'     , views.manageSingup, name="manageSingup"),
    
    path('manageDepartment/' , views.manageDepartment, name="manageDepartment"),
    path('managePosition/'   , views.managePosition, name="managePosition"),
    
    path('search/'           , views.search_new, name="search"),
    path('rankList/'         , views.rankList_new, name="rankList"),

    path('tk_list/'         , views.thankyouList_new, name="tk_list"),
    path('tk_talk/'         , views.thankyouTalk, name="tk_talk"),
    
    ##################################################
    # API 업무처리
    ##################################################
    path('apis/notice_modify/' , apis.notice_modify, name="notice_modify"),
    path('apis/mythankyou_list_page/' , apis.mythankyou_list_page, name="mythankyou_list_page"),
    path('apis/check_five/' , apis.check_five, name="check_five"),
    path('apis/add_token/' , apis.add_token, name="add_token"),
    path('apis/crown_profile/' , apis.crown_profile, name="crown_profile"),
    path('apis/change_todaythankyou/' , apis.change_todaythankyou, name="change_todaythankyou"),

    path('apis/praise_like/'   , apis.praise_like, name="praise_like"),
    path('apis/praise_detail/' , apis.praise_detail, name="praise_detail"),
    path('apis/praise_regedit/', apis.praise_regedit, name="praise_regedit"),
    path('apis/praise_modify/' , apis.praise_modify, name="praise_modify"), 
    path('apis/praise_list/'   , apis.praise_list, name="praise_list"),
    
    path('apis/praise_page/'   , apis.praise_page_new, name="praise_page"),
    path('apis/praise_first_page/'   , apis.praise_first_page, name="praise_first_page"),
    path('apis/praise_first_page_search/'   , apis.praise_first_page_search, name="praise_first_page_search"),
    
    path('apis/praise_comment_list/'   , apis.praise_comment_list, name="praise_comment_list"),
    path('apis/praise_comment_regedit/', apis.praise_comment_regedit, name="praise_comment_regedit"),
    path('apis/praise_comment_modify/' , apis.praise_comment_modify, name="praise_comment_modify"),
    path('apis/praise_comment_delete/' , apis.praise_comment_delete, name="praise_comment_delete"),
    
    path('apis/praise_card/'       , apis.praise_card, name="praise_card"),
    path('apis/praise_member/'     , apis.praise_member, name="praise_member"),
    path('apis/praise_check/'      , apis.praise_check, name="praise_check"),

    path('apis/tk_list/get_praise_posts'        , apis.get_praise_posts, name="tk_list_get_praise_posts"),
    path('apis/rank_list/get_group_data'      , apis.get_group_data, name="rank_list_get_group_data"),
    
    path('apis/myprofile_info/'    , apis.myprofile_info, name="myprofile_info"),
    path('apis/myprofile_notice/'  , apis.myprofile_notice, name="myprofile_notice"),
    path('apis/openAi_Story/'      , apis.openAi_Story, name="openAi_Story"),
    
    path('apis/praise_count/'      , apis.praise_count, name="praise_count"),
    path('apis/userAppl/'          , apis.userAppl, name="userAppl"),
    path('apis/userStory/'         , apis.userStory, name="userStory"),

    path('apis/search_dept/'       , apis.search_dept, name="search_dept"),
    path('apis/search_posi/'       , apis.search_posi, name="search_posi"),
    
    path('apis/manage_user/'       , apis.manage_user, name="manage_user"),
    path('apis/manage_department/' , apis.manage_department, name="manage_department"),
    path('apis/manage_position/'   , apis.manage_position, name="manage_position"),
    
    path('apis/AllexportToExcel/'  , apis.AllexportToExcel, name="AllexportToExcel"),
    
    
] + static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
#accounts/login/social/naver/callback/
urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)

