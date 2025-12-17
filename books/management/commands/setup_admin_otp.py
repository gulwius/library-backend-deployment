from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django_otp.plugins.otp_email.models import EmailDevice

class Command(BaseCommand):
    help = 'Ensures the admin user has an OTP Email Device configured'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        
        # Change 'admin' below if your superuser has a different username
        username = 'admin' 

        try:
            admin_user = User.objects.get(username=username)
            
            # Try to get the device, or create it if it doesn't exist
            device, created = EmailDevice.objects.get_or_create(
                user=admin_user, 
                name='default',
                defaults={
                    'email': admin_user.email,
                    'confirmed': True
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f"✅ OTP Device created for {admin_user.email}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"ℹ️ OTP Device already exists for {admin_user.email}"))
                
        except User.DoesNotExist:
            self.stdout.write(self.style.WARNING(f"⚠️ User '{username}' not found. Skipping OTP setup."))