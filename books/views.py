from django_otp.plugins.otp_email.models import EmailDevice

from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from datetime import datetime, date

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

from django.core.mail import send_mail
from django.conf import settings 

from django.core.management import call_command
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser

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

                active_borrows = Borrow.objects.filter(borrowing=book, returned=False).count()
                if active_borrows >= book.quantity:
                    results.append(f"⛔ {book.title}: All copies are currently borrowed")
                    continue
                
                borrow_instance=Borrow(borrower=student, borrowing=book)
                try:
                    borrow_instance.full_clean()
                    borrow_instance.save()
                    if student.email: 
                        subject = f"Library Receipt: {book.title}"
                        message = f"""
                        Hi {student.first},
                        
                        You have successfully borrowed: {book.title}
                        Date: {timezone.now().date()}
                        Please return it on time!
                        """
                        try:
                            send_mail(
                                subject,
                                message,
                                settings.EMAIL.HOST_USER,
                                [student.email],
                                fail_silently=True,
                            )
                        except Exception as e:
                            print(f"Email failed to send: {e}")
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
        otp_token = request.data.get('otp_token')
        
        user = authenticate(username=username, password=password)
        
        if user is not None:
            device = EmailDevice.objects.filter(user=user, confirmed=True).first()
            if device:
                if not otp_token:
                    device.generate_challenge()
                    return Response({
                        "status": "otp_required",
                        "message": "Please enter the OTP sent to your email."
                    }, status=status.HTTP_200_OK)
                
                is_valid = device.verify_token(otp_token)
                if not is_valid:
                    return Response({
                        "status": "error", 
                        "message": "Invalid OTP Code. Please try again.",
                    }, status=status.HTTP_400_BAD_REQUEST)
            return Response({
                "status": "success",
                "username": user.username,
                "is_staff": user.is_staff,
            }, status=status.HTTP_200_OK)
        else: 
            return Response({"status": "error", "message": "Invalid Credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        
class AdminDashboardView(APIView):
    def get(self, request):
        now = timezone.now()
        
        # 1. Get the lists from the database
        active_borrows = Borrow.objects.filter(returned=False, due_date__gte=now).order_by('due_date')
        overdue_borrows = Borrow.objects.filter(returned=False, due_date__lt=now).order_by('due_date')
        
        def format_borrows(queryset, is_overdue=False):
            data = []
            for b in queryset:
                try:
                    # --- 1. DATE FIX (Handle mismatch types) ---
                    due = b.due_date
                    if type(due) is date:
                        due = timezone.make_aware(datetime.combine(due, datetime.min.time()))
                    
                    # --- 2. NAME FIX (The cause of your empty list) ---
                    # We try 'first'/'last' (your model), fallback to 'first_name' if changed
                    f_name = getattr(b.borrower, 'first', getattr(b.borrower, 'first_name', 'Unknown'))
                    l_name = getattr(b.borrower, 'last', getattr(b.borrower, 'last_name', 'Student'))
                    full_name = f"{f_name} {l_name}"

                    # --- 3. CALCULATE STATUS ---
                    time_diff = due - now
                    if is_overdue:
                        days = abs(time_diff.days)
                        status_msg = f"Overdue by {days} days" if days > 0 else "Overdue (Today)"
                    else:
                        hours = time_diff.total_seconds() / 3600
                        status_msg = f"{hours:.1f} hours left"

                    data.append({
                        "id": b.id,
                        "student_name": full_name,
                        "student_id": b.borrower.tup_id,
                        "book_title": b.borrowing.title,
                        "due_date": b.due_date.strftime("%Y-%m-%d"),
                        "status": status_msg
                    })
                except Exception as e:
                    print(f"Error formatting borrow ID {b.id}: {e}")
                    # We continue to the next item instead of crashing
                    continue
                    
            return data

        return Response({
            "active": format_borrows(active_borrows, is_overdue=False),
            "overdue": format_borrows(overdue_borrows, is_overdue=True)
        })

@api_view(['POST'])
def trigger_overdue_emails(request):
    try:
        # Run the management command manually
        call_command('send_overdue_notices')
        return Response({'status': 'success', 'message': 'Overdue emails have been sent successfully!'}, status=200)
    except Exception as e:
        return Response({'status': 'error', 'message': str(e)}, status=500)