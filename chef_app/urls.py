"""
URL configuration for chef_app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.urls import path, include, re_path
from rest_framework.authtoken.views import obtain_auth_token
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from drf_yasg.utils import swagger_auto_schema
from rest_framework.decorators import api_view
from rest_framework.authtoken.serializers import AuthTokenSerializer
from chef_co.apiutils import token_response, tags

# Decorate token view for swagger docs
decorated_obtain_auth_token = swagger_auto_schema(
    method='post',
    operation_description="Obtain an authentication token with username and password",
    operation_summary="Get authentication token",
    responses={200: token_response},
    tags=[tags['auth']]
)(obtain_auth_token)

# Create a schema view for Swagger UI
schema_view = get_schema_view(
    openapi.Info(
        title="Chef Co API",
        default_version='v1',
        description="API for Chef Co menu and quantity prediction service",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('chef_co.urls')),  # Include our app's URLs
    path('api-auth/', include('rest_framework.urls')),  # DRF browsable API auth
    path('api-token-auth/', decorated_obtain_auth_token),  # Token authentication
    
    # Swagger UI endpoints
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
