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
    path('signin/', views.signin, name='signin'),
    #path('signCheck/', views.signCheck, name='signCheck'),
    path('signup/', views.signup, name='signup'),
    path('signManager/', views.signManager, name='signManager'),
    path('logout/', views.logout, name='logout'),
    path('myprofile/', views.myprofile, name='myprofile'),
    path('myprofileModify/', views.myprofileModify, name='myprofileModify'),
    path('signprofileModify/', views.signprofileModify, name='signprofileModify'),
    
    ##################################################
    # API 업무처리
    ##################################################
    path('apis/myprofile_modify/', apis.myprofile_modify, name='myprofile_modify'),
    path('apis/myprofile_praise_recive_list/', apis.myprofile_praise_recive_list, name='myprofile_praise_recive_list'),
    path('apis/myprofile_praise_send_list/', apis.myprofile_praise_send_list, name='myprofile_praise_send_list'),
    path('apis/myprofile_praise_detail/', apis.myprofile_praise_detail, name='myprofile_praise_detail'),
    path('apis/myprofile_praise_modify/', apis.myprofile_praise_modify, name='myprofile_praise_modify'),
    
    
] + static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
#accounts/login/social/naver/callback/
urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)