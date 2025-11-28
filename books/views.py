from django.shortcuts import render, get_object_or_404
from django.utils import timezone

from django.http import HttpResponseRedirect, Http404
from django.urls import reverse
import re

from .models import Borrow, Book, Student

from rest_framework import generics
from .serializers import BookDetailsSerializer, LibraryBooksSerializer, StudentHistorySerializer, StudentSerializer

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.core.exceptions import ValidationError

from django.contrib.auth import authenticate

# Create your views here.

class BookListsView(generics.ListAPIView):
   queryset = Book.objects.all()
   serializer_class = LibraryBooksSerializer

class BookDetailsView(generics.RetrieveAPIView):
    queryset = Book.objects.all()
    serializer_class = BookDetailsSerializer
    lookup_field = "pk"

class StudentHistoryView(generics.ListAPIView):
    serializer_class = StudentHistorySerializer

    def get_queryset(self):
        tup_id = self.kwargs['tup_id']
        return Borrow.objects.filter(borrower__tup_id=tup_id).order_by('-borrowed_date')

def index(request):
    if request.method == "POST":
        year = request.POST.get('tup_id_year', '').strip()
        digits = request.POST.get('tup_id_digits', '').strip()
        if re.match(r'^\d{2}$', year) and re.match(r'^\d{4}$', digits):
            tup_id = f"TUPM-{year}-{digits}"
            try:
                Student.objects.get(tup_id=tup_id)
                return HttpResponseRedirect(reverse('library:student', args=[digits]))
            except Student.DoesNotExist:
                error_message = "Student ID not found"
        else:
            error_message = "Invalid format (select year and enter 4 digits)"
        return render(request, "books/index.html", {
            "books": Book.objects.all(),
            "error_message": error_message
        })
    
    books = Book.objects.all()
    for book in books:
        borrow = Borrow.objects.filter(borrowing=book, returned=False).first()
        book.status = "Borrowed" if borrow else "Available"
    
    return render(request, "books/index.html", {
        "books": books 
    })

def book(request, book_id):
    book = Book.objects.get(id=book_id)
    now = timezone.now()
    borrow = Borrow.objects.filter(borrowing=book, returned=False).first()

    if borrow:
        remaining_hours = (borrow.due_date - now).total_seconds() / 3600
        borrow.status = "Overdue" if remaining_hours < 0 else f"{remaining_hours:.1f} hours left"
    
    return render(request, "books/book.html", {
        "book": book,
        "borrow": borrow
    })

def student(request, tup_id):
    try:
        student = Student.objects.filter(tup_id__endswith=f"-{tup_id}").first()
        if not student:
            raise Student.DoesNotExist
    except Student.DoesNotExist:
        raise Http404("Student not found")
    
    borrows = Borrow.objects.filter(borrower=student).order_by('-borrowed_date')
    now = timezone.now()
    for borrow in borrows:
        if not borrow.returned:
            remaining_hours = (borrow.due_date - now).total_seconds() / 3600
            borrow.status = "Overdue" if remaining_hours < 0 else f"{remaining_hours:.1f} hours left (Duration: {borrow.duration_hours} hours)"
        else:
            borrow.status = "Returned"
    return render(request, "books/student.html", {
        "student": student,
        "borrows": borrows
    })

class CirculationView(APIView):
    def post(self, request):
        action = request.data.get('action') #"BORROW" OR "RETURN"
        tup_id = request.data.get('tup_id')
        book_ids = request.data.get('book_ids', [])

        #1. FIND STUDENT
        student = get_object_or_404(Student, tup_id=tup_id)

        results = []

        #2. PROCESS EACH BOOK
        for book_id in book_ids:
            book = get_object_or_404(Book, id=book_id)

            if action == 'borrow':
                #CHECK IF BORROWED
                if Borrow.objects.filter(borrower=student, borrowing=book, returned=False).exists():
                    results.append(f"❌{book.title}: Already borrowed")
                    continue
                
                borrow_instance=Borrow(borrower=student, borrowing=book)
                try:
                    borrow_instance.full_clean()
                    borrow_instance.save()
                    results.append(f"✅ {book.title}: Successfully Borrowed")
                except ValidationError as e:
                    error_msg = e.messages[0] if e.messages else "Validation Error"
                    results.append(f"⛔ {book.title}: Failed - {error_msg}")

            elif action == 'return':
                #FIND ACTIVE BORROW BOOKS
                record = Borrow.objects.filter(borrower=student, borrowing=book, returned=False).first()
                if record:
                    record.returned = True
                    record.save()
                    results.append(f"↩️ {book.title}: Successfully Returned")
                else:
                    results.append(f"⚠️ {book.title}: Was not borrowed by this student")

        return Response({"status": "success", "results": results}, status=status.HTTP_200_OK)


class StudentListView(generics.ListAPIView):
    queryset=Student.objects.all()
    serializer_class=StudentSerializer


class loginView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        user = authenticate(username=username, password=password)
        
        if user is not None:
            return Response({
                "status": "success", 
                "username": user.username,
                "is_staff": user.is_staff
            }, status=status.HTTP_200_OK)
        else:
            return Response({"status": "error", "message": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)