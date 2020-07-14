"""dashboard URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt import views as jwt_views 
from django.conf.urls import (
handler400, handler403, handler404, handler500
)

handler400 = 'app.views.handlerBadRequest'
handler403 = 'app.views.handlerBadRequest'
handler404 = 'app.views.handlerBadRequest'
#handler500 = 'app.views.handlerBadRequest'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),    
    path('', include('app.urls')),    
    path('api/token', jwt_views.TokenObtainPairView.as_view()),      # new
    path('api/token/refresh', jwt_views.TokenRefreshView.as_view()), # new
]
