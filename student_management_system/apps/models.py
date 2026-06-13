from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from datetime import date


class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']
        

class ClassGrade(models.Model):
    CLASS_CHOICES = [
        ('PKG', 'Pre-K.G'), ('LKG', 'L.K.G'), ('UKG', 'U.K.G'),
        ('1', '1st'), ('2', '2nd'), ('3', '3rd'), ('4', '4th'), ('5', '5th'),
        ('6', '6th'), ('7', '7th'), ('8', '8th'), ('9', '9th'), ('10', '10th'),
        ('11', '11th'), ('12', '12th'),
    ]

    name = models.CharField(max_length=10, choices=CLASS_CHOICES, unique=True)
    level = models.IntegerField(default=0) 

    class Meta:
        ordering = ['level']

    def __str__(self):
        return self.get_name_display()


class Student(models.Model):
    BLOOD_GROUP_CHOICES = [('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), 
                          ('O+', 'O+'), ('O-', 'O-'), ('AB+', 'AB+'), ('AB-', 'AB-')]
    GENDER_CHOICES = [('M', 'Male'), ('F', 'Female'), ('O', 'Other')]

    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    student_id = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True)
    nationality = models.CharField(max_length=50, default='Indian')
    aadhar_number = models.CharField(max_length=12, unique=True, null=True, blank=True)
    current_class = models.ForeignKey(ClassGrade, on_delete=models.SET_NULL, null=True, related_name='students')
    roll_number = models.IntegerField(null=True, blank=True)
    admission_date = models.DateField(default=date.today)
    is_active = models.BooleanField(default=True)
    phone_number = models.CharField(max_length=15, validators=[RegexValidator(r'^\+?1?\d{9,15}$')])
    email = models.EmailField(unique=True)
    address = models.CharField(max_length=200)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    pincode = models.CharField(max_length=6)
    father_name = models.CharField(max_length=100)
    father_phone = models.CharField(max_length=15)
    father_occupation = models.CharField(max_length=100, null=True, blank=True)
    mother_name = models.CharField(max_length=100)
    mother_phone = models.CharField(max_length=15)
    mother_occupation = models.CharField(max_length=100, null=True, blank=True) 
    guardian_name = models.CharField(max_length=100, null=True, blank=True)
    guardian_phone = models.CharField(max_length=15, null=True, blank=True)
    allergies = models.TextField(null=True, blank=True)
    emergency_contact = models.CharField(max_length=15)
    medical_conditions = models.TextField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='students/profile/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='students_created')
    religion = models.CharField(max_length=51, null=True, blank=True)
    community = models.CharField(max_length=51, null=True, blank=True)
    caste = models.CharField(max_length=50, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True) 

    class Meta:
        ordering = ['current_class', 'roll_number', 'first_name']
        unique_together = ['current_class', 'roll_number']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.student_id})"

    @property
    def age(self):
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_address(self):
        return f"{self.address}, {self.city}, {self.state} - {self.pincode}"


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    employee_id = models.CharField(max_length=20, unique=True)
    phone_number = models.CharField(max_length=15)
    qualification = models.CharField(max_length=200, blank=True, null=True)
    joining_date = models.DateField()
    is_class_teacher = models.BooleanField(default=False)
    experience_years = models.PositiveIntegerField(default=0)
    subjects = models.ManyToManyField(Subject, blank=True, related_name='teachers')
    
    def __str__(self):
        return self.user.get_full_name() or self.user.username
    
    @property
    def name(self):
        return self.user.get_full_name() or self.user.username
    
    @property
    def email(self):
        return self.user.email
    
    @property
    def experience_display(self):
        return f"{self.experience_years} year{'s' if self.experience_years != 1 else ''}"


class FeeStructure(models.Model):
    class_grade = models.ForeignKey(ClassGrade, on_delete=models.CASCADE, related_name='fee_structures')
    academic_year = models.CharField(max_length=10)
    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2)
    transport_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    other_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    due_date = models.DateField(null=True, blank=True)
    
    class Meta:
        unique_together = ['class_grade', 'academic_year']
        ordering = ['class_grade', '-academic_year']
    
    def __str__(self):
        return f"Fee for {self.class_grade} ({self.academic_year})"
    
    @property
    def total_fees(self):
        return self.tuition_fee + self.transport_fee + self.other_fees


class FeePayment(models.Model):
    PAYMENT_MODE = [('Cash', 'Cash'), ('Online', 'Online'), ('Cheque', 'Cheque')]
    PAYMENT_STATUS = [('Pending', 'Pending'), ('Paid', 'Paid'), ('Partial', 'Partial')]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_payments')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(auto_now_add=True)
    payment_mode = models.CharField(max_length=10, choices=PAYMENT_MODE)
    receipt_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='Paid')
    remarks = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"Receipt #{self.receipt_number} - {self.student.full_name} - ₹{self.amount_paid}"
    
    def save(self, *args, **kwargs):
        if not self.receipt_number:
            # Generate receipt number: RCPT/YYYY/MM/XXXX
            from datetime import datetime
            year = datetime.now().strftime('%Y')
            month = datetime.now().strftime('%m')
            last_receipt = FeePayment.objects.filter(
                receipt_number__startswith=f'RCPT/{year}/{month}/'
            ).order_by('-receipt_number').first()
            
            if last_receipt:
                last_num = int(last_receipt.receipt_number.split('/')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.receipt_number = f'RCPT/{year}/{month}/{new_num:04d}'
        
        super().save(*args, **kwargs)