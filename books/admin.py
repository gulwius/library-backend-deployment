from django.contrib import admin
from django.utils.html import format_html
from .models import Book, Student, Borrow, Author, Subject

# Register your models here.

admin.site.register(Book)
admin.site.register(Student)
admin.site.register(Author)
admin.site.register(Subject)

class BorrowAdmin(admin.ModelAdmin):
    list_display = ('borrowing', 'borrower', 'borrowed_date', 'due_date', 'duration_hours', 'returned')
    readonly_fields = ('borrowed_date', 'due_date', 'daily_limit_info')
    fields = ('borrowing', 'borrower', 'duration_hours', 'returned', 'borrowed_date', 'due_date', 'daily_limit_info')
    
    def get_readonly_fields(self, request, obj=None):
        return self.readonly_fields
    
    def daily_limit_info(self, obj):
        """Display current daily borrow statistics"""
        today_count = Borrow.get_today_borrow_count()
        remaining = Borrow.get_daily_limit_remaining()
        limit = Borrow.DAILY_LIMIT
        
        # Color code based on remaining slots
        if remaining > 50:
            color = 'green'
            status = '✅ Good'
        elif remaining > 20:
            color = 'orange'
            status = '⚠️ Caution'
        else:
            color = 'red'
            status = '🔴 Critical'
        
        html = f"""
        <div style="padding: 10px; border: 2px solid {color}; border-radius: 5px; background-color: {color}20;">
            <strong>{status}</strong><br>
            Today's Borrows: <strong>{today_count}/{limit}</strong> students<br>
            Remaining Slots: <strong>{remaining}</strong>
        </div>
        """
        return format_html(html)
    
    daily_limit_info.short_description = "📊 Daily Borrow Limit Status"
    
    def get_readonly_fields(self, request, obj=None):
        """Make sure daily_limit_info is always shown"""
        return self.readonly_fields

admin.site.register(Borrow, BorrowAdmin)
