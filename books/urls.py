from django.urls import path
from . import views

app_name = "library"

urlpatterns = [
    path("", views.index, name="index"),
    path("<int:book_id>/", views.book, name="book"),
    path("student/<str:tup_id>/", views.student, name="student"),
    
    path("library/", views.BookListsView.as_view(), name="books-lists"),
    path("details/<int:pk>/", views.BookDetailsView.as_view(), name="book-details"),
    path("history/<str:tup_id>/", views.StudentHistoryView.as_view(), name="student-history"),

    path("api/books/", views.BookListsView.as_view(), name="api_book_list"),
    path("api/books/<int:pk>/", views.BookDetailsView.as_view(), name="api_book_detail"),
    path("api/history/<str:tup_id>/", views.StudentHistoryView.as_view(), name="api_student_history"),

    path("api/circulation/", views.CirculationView.as_view(), name="api_circulation"),

    path("api/students/", views.StudentListView.as_view(), name="api_student_list"),

    path("api/login/", views.loginView.as_view(), name="api_login"),

    path('api/admin-dashboard/', views.AdminDashboardView.as_view(), name='admin-dashboard'),
    path('api/trigger-emails/', views.trigger_overdue_emails, name='trigger-emails'),
]