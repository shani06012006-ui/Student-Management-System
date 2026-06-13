from django import forms
from django.contrib.auth.models import User
from django.db import models
from .models import Teacher, Subject, Student, ClassGrade

class TeacherForm(forms.ModelForm):
    # User fields
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True
    )
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True
    )
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        required=True
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False,
        help_text='Leave blank to keep current password (for updates)'
    )
    
    # Teacher fields
    subjects = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mathematics, Science, English, etc.'
        }),
        help_text='Enter subjects separated by commas'
    )
    
    class Meta:
        model = Teacher
        fields = ['employee_id', 'phone_number', 'qualification', 
                 'joining_date', 'is_class_teacher', 'experience_years']
        widgets = {
            'joining_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_class_teacher': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If editing an existing teacher, populate user fields
        if self.instance and self.instance.pk and self.instance.user:
            self.fields['username'].initial = self.instance.user.username
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email
            self.fields['password'].required = False
            self.fields['password'].help_text = 'Leave blank to keep current password'
            
            # Populate subjects as comma-separated string
            subjects_list = [subject.name for subject in self.instance.subjects.all()]
            if subjects_list:
                self.fields['subjects'].initial = ', '.join(subjects_list)
        else:
            # New teacher - password is required
            self.fields['password'].required = True
            self.fields['password'].help_text = 'Minimum 8 characters'
    
    def clean_password(self):
        password = self.cleaned_data.get('password')
        if password and len(password) < 8:
            raise forms.ValidationError("Password must be at least 8 characters long")
        return password
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            # Check if username exists and it's not the current user
            if self.instance and self.instance.pk and self.instance.user:
                if User.objects.filter(username=username).exclude(pk=self.instance.user.pk).exists():
                    raise forms.ValidationError("Username already exists")
            elif User.objects.filter(username=username).exists():
                raise forms.ValidationError("Username already exists")
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Check if email exists and it's not the current user
            if self.instance and self.instance.pk and self.instance.user:
                if User.objects.filter(email=email).exclude(pk=self.instance.user.pk).exists():
                    raise forms.ValidationError("Email already exists")
            elif User.objects.filter(email=email).exists():
                raise forms.ValidationError("Email already exists")
        return email
    
    def save(self, commit=True):
        # Get or create user
        if self.instance and self.instance.pk and self.instance.user:
            # Update existing user
            user = self.instance.user
            user.username = self.cleaned_data['username']
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            
            # Update password if provided
            password = self.cleaned_data.get('password')
            if password:
                user.set_password(password)
            
            if commit:
                user.save()
        else:
            # Create new user
            user = User.objects.create_user(
                username=self.cleaned_data['username'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                email=self.cleaned_data['email'],
                password=self.cleaned_data['password']
            )
        
        # Create/Update teacher
        teacher = super().save(commit=False)
        teacher.user = user
        
        if commit:
            teacher.save()
            self.save_m2m()
            
            # Process subjects
            subjects_text = self.cleaned_data.get('subjects', '')
            if subjects_text:
                subject_list = [s.strip() for s in subjects_text.split(',') if s.strip()]
                teacher.subjects.clear()
                for subject_name in subject_list:
                    subject, created = Subject.objects.get_or_create(name=subject_name)
                    teacher.subjects.add(subject)
        
        return teacher

class StudentRegistrationForm(forms.ModelForm):
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
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'current_class': forms.Select(attrs={'class': 'form-select'}),
            'roll_number': forms.NumberInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control'}),
            'aadhar_number': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control'}),
            'father_name': forms.TextInput(attrs={'class': 'form-control'}),
            'father_occupation': forms.TextInput(attrs={'class': 'form-control'}), 
            'father_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'mother_name': forms.TextInput(attrs={'class': 'form-control'}),
            'mother_occupation': forms.TextInput(attrs={'class': 'form-control'}), 
            'mother_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_name': forms.TextInput(attrs={'class': 'form-control'}),
            'guardian_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'allergies': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'medical_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'religion': forms.TextInput(attrs={'class': 'form-control'}),
            'community': forms.TextInput(attrs={'class': 'form-control'}),
            'caste': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Order classes in a specific sequence
        order = ['PKG', 'LKG', 'UKG', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
        
        from django.db.models import Case, When, IntegerField
        self.fields['current_class'].queryset = ClassGrade.objects.filter(
            name__in=order
        ).order_by(
            Case(
                *[When(name=name, then=pos) for pos, name in enumerate(order)],
                output_field=IntegerField()
            )
        )

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

class AttendanceForm(forms.Form):
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    class_grade = forms.ModelChoiceField(
        queryset=ClassGrade.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label="Select Class"
    )