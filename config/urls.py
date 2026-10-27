"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/

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

from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include
from dmr.openapi import build_schema
from dmr.openapi.views import (
    OpenAPIJsonView,
    StoplightView,
    SwaggerView,
)
from dmr.openapi.views.yaml import OpenAPIYamlView
from dmr.routing import Router, path

from comments.views import CaptchaController, CommentController
from config import settings

router = Router(
    "api/",
    [
        path("comments/", CommentController.as_view(), name="comments"),
        path("captcha/", CaptchaController.as_view(), name="captcha"),
    ],
)

schema = build_schema(router)

urlpatterns = [
    path("admin/", admin.site.urls),
    router.to_urlpatterns(namespace="api"),
    path("api/captcha/", include("captcha.urls")),
    path(
        "docs/openapi.json/",
        OpenAPIJsonView.as_view(schema),
        name="openapi_json",
    ),
    path(  # Requires the `django-modern-rest[openapi]` extra.
        "docs/openapi.yaml/",
        OpenAPIYamlView.as_view(schema),
        name="openapi_yaml",
    ),
    path("docs/stoplight/", StoplightView.as_view(schema), name="stoplight"),
    path("docs/swagger/", SwaggerView.as_view(schema), name="swagger"),
]
# if settings.DEBUG:
#     urlpatterns += [
#         *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
#     ]
urlpatterns += [
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
]
