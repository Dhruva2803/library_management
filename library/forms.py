from django import forms
from .models import Book, Member, Transaction

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = '__all__'

class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = '__all__'

class IssueForm(forms.Form):
    book = forms.ModelChoiceField(queryset=Book.objects.all())
    member = forms.ModelChoiceField(queryset=Member.objects.all())

class ReturnForm(forms.Form):
    transaction_id = forms.IntegerField(label="Transaction ID")
