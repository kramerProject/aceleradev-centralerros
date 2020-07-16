from django.urls import include, path, re_path

from rest_framework.authtoken.views import obtain_auth_token

from rest_framework import routers

from api import views

router = routers.DefaultRouter()
router.register(r'user', views.UserApiViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('login', views.login, name='login'),
    path('group', views.GroupApiViewSet.as_view()),
    path('agent', views.AgentApiViewSet.as_view()),
    path('event', views.EventApiViewSet.as_view()),
    path('get_token', obtain_auth_token),
    path('details', views.details, name='details'),
    path('cadastro', views.cadastro, name='cadastro'),
]
