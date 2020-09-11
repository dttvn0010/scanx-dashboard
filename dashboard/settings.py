"""
Django settings for dashboard project.

Generated by 'django-admin startproject' using Django 3.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
from datetime import timedelta

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'ckixciqlf4w5qj_3tb$z8z00sp$6kyx$^ox@lvt#y8@t(dx36c'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Application definition

INSTALLED_APPS = [
    'rest_framework',
    'app',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'dashboard.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'app.context_processors.google_api_key',
            ],
        },
    },
]

WSGI_APPLICATION = 'dashboard.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    #'default': {
    #    'ENGINE': 'django.db.backends.sqlite3',
    #    'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    #}

    'default': {
       'ENGINE': 'django.db.backends.mysql',
       'NAME': 'dashboard',
       'USER': 'dashboard',
       'PASSWORD': 'abc@123',
       'HOST': 'localhost',
       'PORT': '',
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LOCALE_PATHS = ( os.path.join(BASE_DIR, 'locale'), )
LANGUAGE_CODE = 'en'

TIME_ZONE = 'Europe/London'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'

# New
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

AUTH_USER_MODEL = 'app.User'


REST_FRAMEWORK = {
   'DEFAULT_AUTHENTICATION_CLASSES': [
       'rest_framework.authentication.SessionAuthentication',
       'rest_framework_simplejwt.authentication.JWTAuthentication',
   ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}

MAIL_TEMPLATE_CODES = {
    'ADMIN_INVITATION': 'ADMIN_INVITATION',
    'USER_INVITATION': 'USER_INVITATION',
    'RESET_PASSWORD': 'RESET_PASSWORD',
    'ADMIN_CREATE_NOTIFICATION': 'ADMIN_CREATE_NOTIFICATION'
}

ROLES = {
    'ADMIN': 'ADMIN',
    'STAFF': 'STAFF',
    'USER': 'USER'
}

HOST_URL =  "https://scanx.cloud"
INVITE_URL = HOST_URL + "/accounts/initial_setup"
RESET_PASSWORD_URL = HOST_URL + "/accounts/reset_password"
PROFILE_IMAGE_SIZE = 300

POST_CODER_API_KEY = "PCWJ7-LXWC9-ZGHHK-LFD5B"
POST_CODER_API_URL = f"https://ws.postcoder.com/pcw/{POST_CODER_API_KEY}/address/UK/"
GMAP_API = "AIzaSyAl-bO6JsKLkpOZ9tUEqMuy8Emt6Uds-yg"
GMAP_ADDRESS_API_URL = f"https://maps.googleapis.com/maps/api/geocode/json?key={GMAP_API}"

SCAN_TIME_DELAY = 60
MAP_VIEW_FLUSH_TIME = '00:00'
MAX_TIME_DIFF_ALLOW = 300
NFC_BUTTON_TEXT = 'NFC Scan'
QR_BUTTON_TEXT = 'QR Scan'
SET_DEVICE_UID_BUTTON_TEXT = 'Set Device UID'
UPDATE_DEVICE_COORDINATES_BUTTON_TEXT = 'Update Device Coordinates'

SCAN_CODE_PREFIX = "SCANX"