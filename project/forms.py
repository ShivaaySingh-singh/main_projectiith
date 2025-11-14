from django import forms
from .models import FundRequest, Project, SeedGrant, TDGGrant

from django import forms
from .models import FundRequest, Project, SeedGrant, TDGGrant

class FundRequestForm(forms.ModelForm):
    PROJECT_TYPE_CHOICES = [
        ('', 'Select Project Type'),
        ('project', 'Project'),
        ('seed', 'Seed Grant'),
        ('tdg', 'TDG Grant'),
    ]

    project_type = forms.ChoiceField(
        choices=PROJECT_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
        label="Project Type"
    )

    project_selection = forms.CharField(
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
        label="Select Project/Grant"
    )

    class Meta:
        model = FundRequest
        fields = ['faculty_name', 'short_no', 'head', 'particulars', 'amount']
        widgets = {
            'faculty_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'short_no': forms.TextInput(attrs={'class': 'form-control'}),
            'head': forms.TextInput(attrs={'class': 'form-control'}),
            'particulars': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user and hasattr(user, 'faculty'):
            self.fields['faculty_name'].initial = user.faculty.pi_name



class AdminRemarkForm(forms.ModelForm):
    class Meta:
        model = FundRequest
        fields = ['status', 'remarks_by_src']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'remarks_by_src': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 5,
                'placeholder': 'Add comments or reasons for approval/rejection...'
            }),
        }
        labels = {
            'remarks_by_src': 'Remarks by SRC',
        }