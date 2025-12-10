from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from books.models import Borrow

class Command(BaseCommand):
    help = 'Sends email reminders for overdue books'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        # Find books that are NOT returned and due date is in the past
        overdue_borrows = Borrow.objects.filter(returned=False, due_date__lt=now)

        count = 0

        if not overdue_borrows.exists():
            self.stdout.write(self.style.WARNING('No overdue books found.'))
            return

        for borrow in overdue_borrows:
            student = borrow.borrower
            if student.email:
                try:
                    send_mail(
                        subject="URGENT: Overdue Library Book",
                        message=f"""
                        Dear {student.first},
                        
                        This is a reminder that the book '{borrow.borrowing.title}' was due on {borrow.due_date.date()}.
                        
                        Please return it to the library immediately to avoid penalties.
                        
                        Thank you.
                        """,
                        from_email=settings.EMAIL_HOST_USER,
                        recipient_list=[student.email],
                        fail_silently=False,
                    )
                    count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Failed to send to {student.tup_id}: {str(e)}"))
        
        self.stdout.write(self.style.SUCCESS(f'Successfully sent {count} overdue emails.'))