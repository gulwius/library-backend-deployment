from rest_framework import serializers
from .models import Book, Borrow, Student
from django.utils import timezone

class BookDetailsSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(many=True)
    subject = serializers.StringRelatedField(many=True)
    status = serializers.SerializerMethodField()
    current_borrow = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = ["id", "title", "author", "publication_year", "subject", "description", "cover_image", "cover_url", "status", "current_borrow"]

    def get_status(self, obj):
        borrow = Borrow.objects.filter(borrowing=obj, returned=False).first()
        return "Borrowed" if borrow else "Available"
    
    def get_current_borrow(self, obj):
        borrow = Borrow.objects.filter(borrowing=obj, returned=False).first()
        if borrow:
            return{
                "borrower": borrow.borrower.tup_id,
                "borrowed_date": borrow.borrowed_date,
                "due_date": borrow.due_date
            }
        return None

class LibraryBooksSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = ["id", "title", "cover_image", "cover_url", "status"]

    def get_status(self, obj):
        borrow = Borrow.objects.filter(borrowing=obj, returned=False).first()
        return "Borrowed" if borrow else "Available"

class StudentHistorySerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source='borrowing.title')
    status = serializers.SerializerMethodField()
    borrower_name = serializers.SerializerMethodField()
    class Meta:
        model = Borrow
        fields = ["borrower_name", "book_title", "borrowed_date", "due_date", "status", "duration_hours"]
        
    def get_status(self, obj):    
        if obj.returned:
            return "Returned"
        hours_left = (obj.due_date - timezone.now()).total_seconds()/3600
        if hours_left <= 0:
            return "Overdue"
        return f"{hours_left:.1f}hr left"
    
    def get_borrower_name(self, obj):
        try:
            student = Student.objects.get(tup_id=obj.borrower.tup_id)
            return student.first.strip() or obj.borrower.tup_id
        except Student.DoesNotExist:
            return obj.borrower.tup_idW
        