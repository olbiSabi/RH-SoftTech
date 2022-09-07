from django.urls import path

from .views import *

urlpatterns = [
    path('projet/', projet, name='projet'),
    path('detail-projet/', detailProjet, name='detail-projet'),
]