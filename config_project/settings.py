import os
from django.contrib.messages import constants as messages
        
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '9dw*m)yj@fpmkt_2e0n794c^tbc4t&ul3cq#%c4y2gqin2@1q4'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

SERVER_NAME = 'TEST'

######################################################
# Application definition
######################################################
INSTALLED_APPS = [
    'home',
    'myprofile',
    'corsheaders',
    'sslserver',
    'management.apps.managementConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',

    'django.middleware.clickjacking.XFrameOptionsMiddleware', # 이 줄 유지
    'corsheaders.middleware.CorsMiddleware',


]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    # 다른 허용하려는 origin들을 필요에 따라 추가
]

#CORS_ALLOW_ALL_ORIGINS = True  # 모든 도메인에서의 요청을 허용하려면 True로 설정
CORS_ALLOW_CREDENTIALS = True  # 인증 정보를 전송할 경우 True로 설정

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_METHODS = (
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
)
CORS_ALLOW_HEADERS = (
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
)


X_FRAME_OPTIONS = 'ALLOWALL' # 추가
#X_FRAME_OPTIONS = 'ALLOW-FROM https://example.com' # example.com 대신 허용할 도메인을 지정

ROOT_URLCONF = 'config_project.urls'

SESSION_COOKIE_SAMESITE = 'None'
CSRF_COOKIE_SAMESITE = 'None'

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

TEMPLATES = [
                     
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config_project.wsgi.application'

######################################################
# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases
######################################################
#DATABASES = {
#        'default': {
#        'ENGINE': 'django.db.backends.sqlite3',
#        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#    }
#}


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'wbntt',
        'USER': 'wbntt',
        'PASSWORD': 'wbnTT!23$',
        'HOST': '49.247.44.76',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'sql_mode': 'traditional',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"
        },
        'CONN_MAX_AGE': 0,
    }
}

######################################################
# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators
######################################################
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

######################################################
# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/
######################################################
LANGUAGE_CODE = 'ko-kr'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_L10N = True
#USE_TZ = True

#-------------
#USE_TZ TRUE
#-------------
#장고 개발시 datetime 객체를 사용
#import datetime
#now = datetime.datetime.now()

#-------------
#USE_TZ False
#-------------
#장고 개발시 time-zone-aware datetime 객체를 사용
#from django.utils
#import timezone now = timezone.now()


######################################################
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/
######################################################
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
)

AUTH_USER_MODEL = 'myprofile.User'

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

MEDIA_ROOT = os.path.join(BASE_DIR,'media','user')

MEDIA_URL = '/media/user/'

######################################################
#MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'
######################################################
MESSAGE_TAGS = {
    messages.DEBUG: 'alert-info',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}


SESSION_COOKIE_AGE = 18000
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

import logging
import os
import datetime

# 로그 디렉토리 생성
LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# 파일 핸들러 정의를 함수로 감싸서 동적으로 파일 이름을 생성할 수 있도록 합니다.
def get_log_file_path():
    return os.path.join(LOG_DIR, f'{datetime.date.today()}-LogFile.log')



LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,      #디폴트 : True, 장고의 디폴트 로그 설정을 대체. / False : 장고의 디폴트 로그 설정의 전부 또는 일부를 다시 정의
    'formatters': {                        # message 출력 포맷 형식
        'verbose': {
            'format' : "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            'datefmt' : "%d/%b/%Y %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': get_log_file_path(),  # 함수를 호출하여 파일명을 동적으로 생성
            'formatter': 'verbose'
        }, 
    },
    'loggers': {
        'django': {
            'handlers':['file'],        # 'file' : handler의 이름
            'propagate': True,         
            'level':'INFO',            # DEBUG 및 그 이상의 메시지를 file 핸들러에게 보내줍니다.
        },
        'app_name': {                   # Project에서 생성한 app의 이름
            'handlers': ['file'],          # 다른 app을 생성 후 해당 app에서도
            'level': 'INFO',          # 사용하고자 할 경우 해당 app 이름으로
        },                                   # 좌측 코드를 추가 작성해서 사용
    }
}