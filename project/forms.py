from django import forms
from .models import FundRequest, Project, SeedGrant, TDGGrant

from django import forms
from .models import FundRequest, Project, SeedGrant, TDGGrant, Receipt

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
        fields = ['pi_name', 'short_no', 'head', 'particulars', 'amount']
        widgets = {
            'pi_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'short_no': forms.TextInput(attrs={'class': 'form-control'}),
            'head': forms.TextInput(attrs={'class': 'form-control'}),
            'particulars': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'amount': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user and hasattr(user, 'faculty'):
            self.fields['pi_name'].initial = user.faculty.pi_name



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


class ReceiptForm(forms.ModelForm):

    short_no = forms.ChoiceField(label="Short No.")

    class Meta:
        model = Receipt
        fields = [
            "receipt_date",
            "financial_year",
            "category",
            "short_no",
            "reference_number",
            "invoice_no",
            "total_amount",
            "remarks",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        project_choices = [
            (f"P-{p.id}", f"{p.project_short_no} (Project)")
            for p in Project.objects.all()
        ]

        seed_choices = [
            (f"S-{s.id}", f"{s.short_no} (Seed)")
            for s in SeedGrant.objects.all()
        ]

        tdg_choices = [
            (f"T-{t.id}", f"{t.short_no} (TDG)")
            for t in TDGGrant.objects.all()
        ]

        self.fields["short_no"].choices = (
            project_choices + seed_choices + tdg_choices
        )

        if self.instance and self.instance.pk:
            if self.instance.project:
                self.initial["short_no"] = f"P-{self.instance.project.id}"
            elif self.instance.seed_grant:
                self.initial["short_no"] = f"S-{self.instance.seed_grant.id}"
            elif self.instance.tdg_grant:
                self.initial["short_no"] = f"T-{self.instance.tdg_grant.id}"

    
    def save(self, commit=True):
        instance = super().save(commit=False)

        value = self.cleaned_data.get("short_no")

        if value:
            prefix, obj_id = value.split("-")

            instance.project = None
            instance.seed_grant = None
            instance.tdg_grant = None

            if prefix == "P":
                instance.project = Project.objects.get(id=obj_id)

            elif prefix == "S":
                instance.seed_grant = SeedGrant.objects.get(id=obj_id)

            elif prefix == "T":
                instance.tdg_grant = TDGGrant.objects.get(id=obj_id)

        if commit:
            instance.save()

        return instance


    def clean(self):
        cleaned_data = super().clean()

        value = cleaned_data.get("short_no")

        if not value:
            raise forms.ValidationError("Please select a funding source")

        return cleaned_data