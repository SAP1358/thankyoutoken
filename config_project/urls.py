from django.contrib import admin
from django.urls import path, include
import home.views
import home.apis

from django.conf import settings
from django.conf.urls import url
from django.views.static import serve

from django.conf.urls.static import static




urlpatterns = [
    path('check/', admin.site.urls),
    path('', home.views.home_new, name='home'),
    path('',include('home.urls')),
    path('accounts/', include('myprofile.urls')),
    
    url(r'^media/user/(?P<path>.*)$', serve, {'document_root':settings.MEDIA_ROOT}),
    url(r'^static/(?P<path>.*)$', serve, {'document_root':settings.STATIC_ROOT}),
        
    #url(r'^media/(?P<path>.*)$', serve, {'document_root':settings.MEDIA_ROOT}),
    #url(r'^static/(?P<path>.*)$', serve, {'document_root':settings.STATIC_ROOT}),
    
]

#urlpatterns += [
#    url(r'^media/(?P<path>.*)$', serve, {
#        'document_root': settings.MEDIA_ROOT,
#    }),
#]

#urlpatterns += [
#    url(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}),
#]

#urlpatterns += [
#    url(r'^media/user/(?P<path>.*)$', serve, {'document_root':settings.MEDIA_ROOT}),
#    url(r'^static/(?P<path>.*)$', serve, {'document_root':settings.STATIC_ROOT}),
    
   # url(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}),
   # url(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),
    
#]

    

