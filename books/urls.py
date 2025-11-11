from django.urls import path
from . import views

app_name="library"

urlpatterns = [
    path("", views.index, name="index"),
    path("<int:book_id>/", views.book, name="book"),
    path("student/<str:tup_id>/", views.student, name="student"),

    path("library/", views.BookListsView.as_view(), name="books-lists"),
    path("details/<int:pk>/", views.BookDetailsView.as_view(), name="book-details"),
    path("history/<str:tup_id>/", views.StudentHistoryView.as_view(), name="student-history"),
]