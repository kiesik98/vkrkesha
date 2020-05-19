from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required
from django.urls import path

from TestingSystem import settings
from accounts.views import login_view, logout_view, signup_view, generate_view
from app import views

app_name = 'app'
auth_patterns = [
    path('accounts/signup/', signup_view, name='signup'),
    path('accounts/login/', login_view, name='login'),
    path('accounts/logout/', logout_view, name='logout'),
    path('generate', generate_view, name='generate')
]

test_patterns = [
    path('test/<int:pk>/question/<int:q>/',  views.test_view, name='test'),
    path('test/<int:pk>/finish/',  views.finish, name='finish'),
    path('', login_required(views.HomeView.as_view()), name='home'),
]

urlpatterns = auth_patterns + test_patterns + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
