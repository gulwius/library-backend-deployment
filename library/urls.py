"""
URL configuration for library project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.contrib.auth.models import User

from django_otp.admin import OTPAdminSite
from django_otp.plugins.otp_email.models import EmailDevice
from django_otp.plugins.otp_email.admin import EmailDeviceAdmin

def is_verified(self):
    """Check if user has a verified OTP device"""
    try:
        return EmailDevice.objects.filter(user=self, confirmed=True).exists()
    except:
        return False

if not hasattr(User, 'is_verified'):
    User.add_to_class('is_verified', is_verified)

class OTPAdmin(OTPAdminSite):
    pass
admin_site = OTPAdmin(name='OTPAdmin')
admin_site.register(User)
admin_site.register(EmailDevice, EmailDeviceAdmin)

for model_cls, model_admin in admin.site._registry.items():
    if model_cls not in admin_site._registry:
        admin_site.register(model_cls, model_admin.__class__)

urlpatterns = [
    path('admin/', admin_site.urls),
    path('books/', include("books.urls"))
]
