from django.contrib import admin
from django.urls import path
from app import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', views.login, name='login'),
    path('', views.home, name='home'),
    path('recommend/', views.recommend, name='recommend'),
    path('articles/<int:pk>/like/', views.toggle_like, name='toggle_like'),
    path('articles/<int:pk>/', views.article_detail, name='article_detail'),
    path('articles/<int:pk>/similar/', views.similar_articles, name='article_similar'),
    path('logout/', views.logout, name='logout'),
    path('profile/edit', views.profile_edit, name='profile.edit')
]
