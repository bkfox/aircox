from django.conf.urls import url

import aircox_liquidsoap.views as views

urlpatterns = [
    url('^controller/', views.LiquidControl.as_view(),  name = 'liquid-controller'),
]


