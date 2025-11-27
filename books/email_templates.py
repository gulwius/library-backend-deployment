from django.utils import timezone

BORROW_CONFIRMATION = """
TUP Student Library
---------------------
Book has been borrowed!

Hi {first_name},

You have successfully borrowed: {book_title}📖

⏱️
Due Date: {due_date}
Duration: {duration} hours

Please return the book on {due_date} to avoid overdue fees.

Thank you!
- TUP Student Library Group
"""

REMINDER = """
TUP Student Library
---------------------
Return Reminder.

Hi {first_name},

Your borrowed book ({book_title}) is due soon.

Due in {hours_left} hours -> {due_date}

Please return it in due time.

Thank you!
- TUP Student Library Group
"""

OVERDUE = """
TUP Student Library
---------------------
OVERDUE BOOK!!

Hi {first_name},

Your borrowed book ({book_title}) is now overdue.

You have failed to return the book on {due_date}.

Please return it immediately. 
Further action will be taken if book has not been properly returned.

Thank you!
- TUP Student Library Group
"""