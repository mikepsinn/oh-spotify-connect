from django.conf import settings
from django.urls import path, include

from app import views

urlpatterns = [
    path('admin/', include('admin.urls')),
    path('', views.info, name='info'),
    path('authorize/', views.authorize, name='authorize'),
    path('authenticate/', views.authenticate, name='authenticate'),
    path('spotify_authorize/', views.spotify_authorize, name='spotify_authorize'),
    path('spotify_authenticate/', views.spotify_authenticate, name='spotify_authenticate'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('recommendations/', views.recommendations, name='recommendations'),
    path('logout/', views.log_out, name='logout')
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns.append(path('__debug__/', include(debug_toolbar.urls)))
