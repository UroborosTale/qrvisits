from django.contrib import admin
from django.urls import path
from cards import views

urlpatterns = [
    path('manage/preview/<uuid:pk>/', views.preview, name='card-preview'),
    path('manage/preview/<uuid:pk>/photo/', views.preview_photo, name='preview-photo'),
    path('manage/', admin.site.urls),
    path('', views.home, name='home'),
    path('robots.txt', views.robots),
    path('c/<uuid:pk>/', views.card, name='card'),
    path('c/<uuid:pk>/photo/', views.photo, name='card-photo'),
    path('c/<uuid:pk>/contact.vcf', views.contact_file, name='card-vcard'),
    path('c/<uuid:pk>/qr.png', views.qr_file, {'format': 'png'}, name='card-qr-png'),
    path('c/<uuid:pk>/qr.svg', views.qr_file, {'format': 'svg'}, name='card-qr-svg'),
]
handler404 = 'cards.views.not_found'
