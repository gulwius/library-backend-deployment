from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
import datetime
from django.core.mail import send_mail
from .email_templates import BORROW_CONFIRMATION, REMINDER, OVERDUE

# Create your models here.
class Author(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name

class Subject(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=64)
    author = models.ManyToManyField(Author)
    publication_year = models.IntegerField()
    subject = models.ManyToManyField(Subject)
    description = models.TextField(blank=True)
    cover_image = models.TextField(max_length=64, blank=True, null=True, help_text="file name in static/books/images/(bookcover.png/.jpeg)")
    cover_url = models.URLField(blank=True, null=True, help_text="Full url to book cover")
    quantity = models.PositiveIntegerField(default=1)
    def __str__(self):
        authors = ", ".join(author.name for author in self.author.all())
        subjects = ", ".join(subject.name for subject in self.subject.all())
        return f"{self.title} by {authors} ({self.publication_year}) ({subjects})"

class Student(models.Model):
    first = models.CharField(max_length=64)
    last = models.CharField(max_length=64)
    tup_id = models.CharField(max_length=64, unique=True)
    email = models.EmailField(unique=True)

    def __str__(self):
        return f"{self.first} {self.last} ({self.tup_id})"

class Borrow(models.Model):
    DAILY_LIMIT = 100

    borrowing = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="borrowing")
    borrower = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="borrower")
    borrowed_date = models.DateTimeField(default=timezone.now)
    due_date = models.DateTimeField(null=True, blank=True)
    duration_hours = models.IntegerField(default=24)
    returned = models.BooleanField(default=False)
    
    @staticmethod
    def get_today_borrow_count():
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + datetime.timedelta(days=1)

        count = Borrow.objects.filter(
            borrowed_date__gte = today_start,
            borrowed_date__lt = today_end
        ).values('borrower').distinct().count()

        return count
    
    @staticmethod
    def get_daily_limit_remaining():
        return Borrow.DAILY_LIMIT - Borrow.get_today_borrow_count()
    
    def clean(self):
        if self.pk is None:

            current_active_loans=Borrow.objects.filter(borrower=self.borrower, returned=False).count()
            if current_active_loans >= 3:
                raise ValidationError(f"{self.borrower.first} has already borrowed the limit of 3 books.")
            
            # today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            # today_end = today_start + datetime.timedelta(days=1)

            # already_borrowed_today = Borrow.objects.filter(
            #     borrower = self.borrower,
            #     borrowed_date__gte = today_start,
            #     borrowed_date__lt = today_end
            # ).exists()

            # if already_borrowed_today:
            #     raise ValidationError(f"{self.borrower.first} has already borrowed a book today. Only 1 book per student per day allowed.")
            
            if Borrow.get_today_borrow_count() >= Borrow.DAILY_LIMIT:
                raise ValidationError(
                    f"Daily borrowing limit ({Borrow.DAILY_LIMIT} students) has been reached. "
                    f"Please try again tomorrow."
                )

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        if not self.due_date:
            start_time = self.borrowed_date if self.borrowed_date else timezone.now()
            self.due_date = start_time + datetime.timedelta(hours=max(self.duration_hours, 1))
        super().save(*args, **kwargs)

        if is_new:
            self.send_borrow_confirmation()
    
    def send_borrow_confirmation(self):
        message = BORROW_CONFIRMATION.format(
            first_name = self.borrower.first,
            book_title = self.borrowing.title,
            due_date = self.due_date.strftime('%B %d, %Y at %I:%M %p'),
            duration = self.duration_hours,
        )
        send_mail(
            subject = f"You borrowed: {self.borrowing.title}",
            message = message.strip(),
            from_email = "TUP Student Library <adamconcepcion25@gmail.com>",
            recipient_list = [self.borrower.email],
            fail_silently = False,
        )

    def send_reminder(self):
        if self.returned:
            return
        hours_left = (self.due_date - timezone.now()).total_seconds() / 3600
        if 3<= hours_left <= 6:
            message = REMINDER.format(
                first_name = self.borrower.first,
                book_title = self.borrowing.title,
                hours_left = f"{hours_left:.1f}",
                due_date = self.due_date.strftime('%B %d, %Y at %I:%M %p'),
            )
            send_mail(
                subject = "Reminder to Return Book Soon!",
                message = message.strip(),
                from_email = "TUP Student Library <adamconcepcion25@gmail.com>",
                recipient_list = [self.borrower.email],
                fail_silently=False,
            )

    def send_overdue_notice(self):
        if self.returned or self.due_date > timezone.now():
            return
        
        message = OVERDUE.format(
            first_name = self.borrower.first,
            book_title = self.borrowing.title,
            due_date = self.due_date.strftime('%B %d, %Y at %I:%M %p'),
        )
        send_mail(
            subject = "Overdue Notice.",
            message = message.strip(),
            from_email = "TUP Student Library <adamconcepcion25@gmail.com>",
            recipient_list = [self.borrower.email],
            fail_silently=False,
            )

    def __str__(self):
        return f"{self.borrowing} is borrowed by {self.borrower.first} {self.borrower.last} ({self.borrower.tup_id})"