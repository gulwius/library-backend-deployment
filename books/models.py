from django.db import models
from django.utils import timezone
import datetime

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
    borrowing = models.ForeignKey(Book, on_delete=models.CASCADE)
    borrower = models.ForeignKey(Student, on_delete=models.CASCADE)
    borrowed_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField(null=True, blank=True)
    duration_hours = models.IntegerField(default=24)
    returned = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        if not self.due_date:
            self.due_date = timezone.now() + datetime.timedelta(hours=max(self.duration_hours, 1))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.borrowing} is borrowed by {self.borrower.first} {self.borrower.last} ({self.borrower.tup_id})"