from django.urls import path

import aircox.views as views

urls = [
    path('on_air', views.on_air, name='aircox.on_air'),
    path('monitor', views.Monitor.as_view(), name='aircox.monitor'),
    path('stats', views.StatisticsView.as_view(), name='aircox.stats'),
]

