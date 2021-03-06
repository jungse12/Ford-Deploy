from django.urls import path
from . import views

urlpatterns = [
    path('',views.dashboard, name='dashboard'),
    path('login',views.loginPage, name='login'),
    path('calc', views.calc, name='calc'),
    path('apitest', views.apitest, name='apitest'),
    path('resulttest', views.resulttest, name="resulttest"),
    path('comparison', views.comparison, name="comparison"),
    path('compare', views.compare, name="compare"),
    path('load', views.load, name="load"),
    path('matrixDatabase', views.matrixDatabase, name="matrixDatabase"),
]
