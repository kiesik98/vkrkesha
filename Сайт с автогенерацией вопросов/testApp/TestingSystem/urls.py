from django.contrib import admin
from django.contrib.auth import views
from django.urls import path, include

urlpatterns = [
    # переопределили своим шаблоном
    path('admin/login/', views.LoginView.as_view(template_name='admin/login.html'), name='login'),
    path('admin/', admin.site.urls),
    path('', include('app.urls', namespace='app'))
]
