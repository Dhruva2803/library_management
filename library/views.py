from django.shortcuts import render, redirect, get_object_or_404
from .models import Book, Member, Transaction
from .forms import BookForm, MemberForm, IssueForm, ReturnForm
import requests
import datetime

# DASHBOARD
def dashboard(request):
    total_books = Book.objects.count()
    total_members = Member.objects.count()
    total_issued = Transaction.objects.filter(return_date__isnull=True).count()

    context = {
        'total_books': total_books,
        'total_members': total_members,
        'total_issued': total_issued,
    }

    return render(request, 'dashboard.html', context)

# BOOKS
def book_list(request):
    q = request.GET.get("q", "")
    books = Book.objects.filter(title__icontains=q) | Book.objects.filter(author__icontains=q)
    return render(request, 'book_list.html', {'books': books})

def book_add(request):
    form = BookForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('book_list')
    return render(request, 'book_form.html', {'form': form})

# MEMBERS
def member_list(request):
    members = Member.objects.all()
    return render(request, 'member_list.html', {'members': members})

def member_add(request):
    form = MemberForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('member_list')
    return render(request, 'member_form.html', {'form': form})

# ISSUE BOOK
def issue_book(request):
    form = IssueForm(request.POST or None)
    msg = ""
    if form.is_valid():
        book = form.cleaned_data['book']
        member = form.cleaned_data['member']
        if book.stock > 0 and member.debt <= 500:
            Transaction.objects.create(book=book, member=member)
            book.stock -= 1
            book.save()
            msg = "Book issued successfully."
        else:
            msg = "Cannot issue: Stock or Debt Limit problem"
    return render(request, 'issue_book.html', {'form': form, 'msg': msg})

# RETURN BOOK
def return_book(request):
    form = ReturnForm(request.POST or None)
    msg = ""
    if form.is_valid():
        try:
            tx = Transaction.objects.get(id=form.cleaned_data['transaction_id'], return_date=None)
            tx.return_date = datetime.date.today()
            days = (tx.return_date - tx.issue_date).days
            fee = max(0, (days - 7) * 5)
            tx.fee = fee
            tx.save()

            tx.book.stock += 1
            tx.book.save()

            tx.member.debt += fee
            tx.member.save()

            msg = f"Book returned. Fee: ₹{fee}"
        except Transaction.DoesNotExist:
            msg = "Invalid or already returned transaction"
    return render(request, 'return_book.html', {'form': form, 'msg': msg})

# IMPORT BOOKS
def book_import(request):
    if request.method == 'POST':
        count = int(request.POST.get('count'))
        title = request.POST.get('title', '')
        imported = 0
        page = 1 

        while imported < count:
            
            url = 'https://frappe.io/api/method/frappe-library'
            params = {'title': title, 'page': page}
            response = requests.get(url, params=params)

            if response.status_code != 200:
                break  

            data = response.json()
            books = data.get('message', [])

            if not books:
                break  

            for b in books:
                if imported >= count:
                    break

                
                Book.objects.get_or_create(
                    title=b.get('title', 'Untitled'),
                    author=b.get('authors', 'Unknown'),
                    isbn=b.get('isbn', ''),
                    publisher=b.get('publisher', ''),
                    pages=b.get('num_pages') or 0,
                    defaults={'stock': 1}
                )
                imported += 1

            page += 1  
        return redirect('book_list')

    return render(request, 'book_import.html')

def issued_book(request):
    issue_transactions = Transaction.objects.filter(return_date__isnull=True).select_related('book', 'member')

    context = {
        'issued_transactions': issue_transactions
    }
    return render(request, 'issued_book.html', context)
    
