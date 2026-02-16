from django import forms
from django.contrib.auth.models import User
from .models import *

class StudentRegistrationForm(forms.ModelForm):
    # Make sure these fields are properly defined
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=True
    )
    admission_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=True
    )
    
    class Meta:
        model = Student
        fields = '__all__'
        exclude = ['created_by', 'student_id', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter first name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter last name'}),
            'current_class': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'roll_number': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter roll number'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control', 'value': 'Indian'}),
            'religion': forms.TextInput(attrs={'class': 'form-control'}),
            'caste': forms.TextInput(attrs={'class': 'form-control'}),
            'aadhar_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter 12 digit Aadhar'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter city'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter state'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter 6 digit pincode'}),
            'father_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Enter father's name"}),
            'father_occupation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Enter father's occupation"}),
            'father_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Enter father's phone"}),
            'mother_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Enter mother's name"}),
            'mother_occupation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Enter mother's occupation"}),
            'mother_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Enter mother's phone"}),
            'guardian_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter guardian name'}),
            'guardian_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter guardian phone'}),
            'allergies': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Any allergies'}),
            'medical_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Any medical conditions'}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter emergency contact'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make sure current_class shows all available classes
        self.fields['current_class'].queryset = ClassGrade.objects.all()
        self.fields['current_class'].empty_label = "Select Class"
        self.fields['current_class'].label = "Current Class"
        self.fields['current_class'].required = True
        
        # Make other fields required as needed
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['date_of_birth'].required = True
        self.fields['gender'].required = True
        self.fields['phone_number'].required = True
        self.fields['email'].required = True
        self.fields['address'].required = True
        self.fields['city'].required = True
        self.fields['state'].required = True
        self.fields['pincode'].required = True
        self.fields['father_name'].required = True
        self.fields['father_phone'].required = True
        self.fields['mother_name'].required = True
        self.fields['mother_phone'].required = True
        self.fields['emergency_contact'].required = True
    
    def clean_aadhar_number(self):
        aadhar = self.cleaned_data.get('aadhar_number')
        if aadhar and len(aadhar) != 12:
            raise forms.ValidationError("Aadhar number must be 12 digits")
        return aadhar
    
    def clean_pincode(self):
        pincode = self.cleaned_data.get('pincode')
        if pincode and len(pincode) != 6:
            raise forms.ValidationError("Pincode must be 6 digits")
        return pincode
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if phone and len(phone) < 10:
            raise forms.ValidationError("Phone number must be at least 10 digits")
        return phone

class TeacherRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = Teacher
        fields = ['employee_id', 'qualification', 'experience_years', 'subjects', 
                 'phone_number', 'address', 'joining_date', 'is_class_teacher']
        widgets = {
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'subjects': forms.SelectMultiple(attrs={'class': 'form-select'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'joining_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_class_teacher': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['employee_id'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password']
        )
        teacher = super().save(commit=False)
        teacher.user = user
        if commit:
            teacher.save()
            self.save_m2m()
        return teacher

class AttendanceForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}))
    class_grade = forms.ModelChoiceField(
        queryset=ClassGrade.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Select Class"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student_attendance'] = forms.MultipleChoiceField(
            choices=[],
            widget=forms.CheckboxSelectMultiple,
            required=False
        )

class MarksEntryForm(forms.ModelForm):
    class Meta:
        model = Marks
        fields = ['student', 'exam', 'marks_obtained', 'remarks']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'exam': forms.Select(attrs={'class': 'form-select'}),
            'marks_obtained': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'remarks': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'exam' in self.data:
            try:
                exam_id = int(self.data.get('exam'))
                self.fields['student'].queryset = Student.objects.filter(
                    current_class=Exam.objects.get(id=exam_id).class_grade
                )
            except (ValueError, TypeError):
                pass
