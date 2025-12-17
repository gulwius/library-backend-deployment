from rest_framework import serializers
from .models import Book, Borrow, Student
from django.utils import timezone

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ['tup_id', 'first', 'last', 'email']

class LibraryBooksSerializer(serializers.ModelSerializer):
    # This controls the MAIN DASHBOARD STATS (Borrowed/Available/Total)
    author = serializers.StringRelatedField(many=True)
    status = serializers.SerializerMethodField()
    available_copies = serializers.SerializerMethodField()

    class Meta:
        model = Book
        # Ensure these fields match your model exactly
        fields = ["id", "author", "title", "cover_image", "cover_url", "status", "quantity", "available_copies"]

    def get_available_copies(self, obj):
        active_borrows = Borrow.objects.filter(borrowing=obj, returned=False).count()
        return max(0, obj.quantity - active_borrows)

    def get_status(self, obj):
        active_borrows = Borrow.objects.filter(borrowing=obj, returned=False).count()
        # # This logic ensures the "Borrowed" count on the dashboard is correct
        # if Borrow.objects.filter(borrowing=obj, returned=False).exists():
        if active_borrows >= obj.quantity:
            return "Borrowed"
        return "Available"

class BookDetailsSerializer(serializers.ModelSerializer):
    # This controls the individual book page
    author = serializers.StringRelatedField(many=True)
    subject = serializers.StringRelatedField(many=True)
    status = serializers.SerializerMethodField()
    available_copies = serializers.SerializerMethodField()
    active_loans = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = ["id", "title", "author", "publication_year", "subject", "description", "cover_image", "cover_url", "status", "quantity", "available_copies", "active_loans"]

    def get_available_copies(self, obj):
        active_borrows = Borrow.objects.filter(borrowing=obj, returned=False).count()
        return max(0, obj.quantity - active_borrows)

    def get_status(self, obj):
        active_borrows = Borrow.objects.filter(borrowing=obj, returned=False).count()
        if active_borrows >= obj.quantity:
            return "Out of Stock"
        return "Available"
    
    def get_active_loans(self, obj):
        borrows = Borrow.objects.filter(borrowing=obj, returned=False)
        return [
            {
                "borrower": f"{b.borrower.first} {b.borrower.last} ({b.borrower.tup_id})",
                "due_date": b.due_date,
                "borrowed_date": b.borrowed_date
            }
            for b in borrows
        ]
    
    # def get_current_borrow(self, obj):
    #     borrow = Borrow.objects.filter(borrowing=obj, returned=False).first()
    #     if borrow:
    #         return {
    #             "borrower": borrow.borrower.tup_id,
    #             "borrowed_date": borrow.borrowed_date,
    #             "due_date": borrow.due_date,
    #             # I assumed your model uses .first and .last based on your code
    #             "name": f"{borrow.borrower.first} {borrow.borrower.last}" 
    #         }
    #     return None

class StudentHistorySerializer(serializers.ModelSerializer):
    # This controls the STUDENT HISTORY PAGE & PROFILE
    book_title = serializers.CharField(source='borrowing.title', read_only=True)
    status = serializers.SerializerMethodField()

    # We restore these fields so the Profile Card doesn't say "undefined"
    student_first = serializers.CharField(source='borrower.first')
    student_last = serializers.CharField(source='borrower.last')
    student_email = serializers.CharField(source='borrower.email')
    student_tup_id = serializers.CharField(source='borrower.tup_id')

    class Meta:
        model = Borrow
        fields = [
            "student_first", "student_last", "student_email", "student_tup_id", # Profile Data
            "book_title", "borrowed_date", "due_date", "status"                 # Table Data
        ]
        
    def get_status(self, obj):    
        if obj.returned:
            return "Returned"
        
        # Check for Overdue status
        if obj.due_date < timezone.now():
            return "Overdue"
            
        return "Active"