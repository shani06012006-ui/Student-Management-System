from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from datetime import date

class ClassGrade(models.Model):
    """School classes/grades (e.g., 1st Grade, 2nd Grade, etc.)"""
    GRADE_CHOICES = [
        (1, '1st Grade'),
        (2, '2nd Grade'),
        (3, '3rd Grade'),
        (4, '4th Grade'),
        (5, '5th Grade'),
        (6, '6th Grade'),
        (7, '7th Grade'),
        (8, '8th Grade'),
        (9, '9th Grade'),
        (10, '10th Grade'),
    ]
    
    SECTION_CHOICES = [
        ('A', 'Section A'),
        ('B', 'Section B'),
        ('C', 'Section C'),
    ]
    
    grade = models.IntegerField(choices=GRADE_CHOICES, verbose_name="Grade")
    section = models.CharField(max_length=1, choices=SECTION_CHOICES, verbose_name="Section")
    class_teacher = models.ForeignKey('Teacher', on_delete=models.SET_NULL, null=True, blank=True, related_name='class_teacher')
    academic_year = models.CharField(max_length=9, help_text="e.g., 2024-2025")
    
    class Meta:
        unique_together = ['grade', 'section', 'academic_year']
        verbose_name = "Class"
        verbose_name_plural = "Classes"
        ordering = ['grade', 'section']
    
    def __str__(self):
        return f"{self.get_grade_display()} - {self.get_section_display()} ({self.academic_year})"

class Subject(models.Model):
    """School subjects"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    grade = models.ManyToManyField(ClassGrade, related_name='subjects')
    is_optional = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class Student(models.Model):
    """School student model"""
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('O+', 'O+'), ('O-', 'O-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
    ]
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    # Personal Information
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    student_id = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True)
    nationality = models.CharField(max_length=50, default='Indian')
    religion = models.CharField(max_length=50, blank=True)
    caste = models.CharField(max_length=50, blank=True)
    aadhar_number = models.CharField(max_length=12, unique=True, null=True, blank=True)
    
    # Academic Information
    current_class = models.ForeignKey(ClassGrade, on_delete=models.SET_NULL, null=True, related_name='students')
    roll_number = models.IntegerField(null=True, blank=True)
    admission_date = models.DateField(default=date.today)
    is_active = models.BooleanField(default=True)
    
    # Contact Information
    phone_number = models.CharField(max_length=15, validators=[RegexValidator(r'^\+?1?\d{9,15}$')])
    email = models.EmailField(unique=True)
    address = models.TextField()
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    pincode = models.CharField(max_length=6)
    
    # Parent/Guardian Information
    father_name = models.CharField(max_length=100)
    father_occupation = models.CharField(max_length=100, blank=True)
    father_phone = models.CharField(max_length=15)
    mother_name = models.CharField(max_length=100)
    mother_occupation = models.CharField(max_length=100, blank=True)
    mother_phone = models.CharField(max_length=15)
    guardian_name = models.CharField(max_length=100, blank=True)
    guardian_phone = models.CharField(max_length=15, blank=True)
    
    # Medical Information
    allergies = models.TextField(blank=True, help_text="Any known allergies")
    medical_conditions = models.TextField(blank=True, help_text="Any medical conditions")
    emergency_contact = models.CharField(max_length=15)
    
    # Profile Picture
    profile_picture = models.ImageField(upload_to='students/profile/', null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['current_class', 'roll_number', 'first_name']
        unique_together = ['current_class', 'roll_number']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.student_id})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))

class Teacher(models.Model):
    """School teacher model"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    employee_id = models.CharField(max_length=20, unique=True)
    qualification = models.CharField(max_length=200)
    experience_years = models.IntegerField(default=0)
    subjects = models.ManyToManyField(Subject, related_name='teachers')
    phone_number = models.CharField(max_length=15)
    address = models.TextField()
    joining_date = models.DateField()
    is_class_teacher = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"

class Attendance(models.Model):
    """Daily attendance for school students"""
    STATUS_CHOICES = [
        ('P', 'Present'),
        ('A', 'Absent'),
        ('L', 'Late'),
        ('H', 'Holiday'),
        ('S', 'Sick Leave'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance')
    class_grade = models.ForeignKey(ClassGrade, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    remarks = models.TextField(blank=True)
    marked_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)
    marked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.student} - {self.date} - {self.get_status_display()}"

class Exam(models.Model):
    """School examinations"""
    EXAM_TYPES = [
        ('UT1', 'Unit Test 1'),
        ('UT2', 'Unit Test 2'),
        ('QUARTERLY', 'Quarterly'),
        ('HALF_YEARLY', 'Half Yearly'),
        ('ANNUAL', 'Annual'),
    ]
    
    name = models.CharField(max_length=100)
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES)
    class_grade = models.ForeignKey(ClassGrade, on_delete=models.CASCADE, related_name='exams')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    exam_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    total_marks = models.IntegerField(default=100)
    passing_marks = models.IntegerField(default=35)
    
    class Meta:
        ordering = ['-exam_date']
    
    def __str__(self):
        return f"{self.name} - {self.class_grade} - {self.subject}"

class Marks(models.Model):
    """Student marks in examinations"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='marks')
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='marks')
    marks_obtained = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    grade = models.CharField(max_length=2, blank=True)
    remarks = models.TextField(blank=True)
    entered_by = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)
    entered_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['student', 'exam']
        verbose_name_plural = 'Marks'
    
    def save(self, *args, **kwargs):
        # Calculate grade based on marks
        percentage = (self.marks_obtained / self.exam.total_marks) * 100
        if percentage >= 90:
            self.grade = 'A+'
        elif percentage >= 80:
            self.grade = 'A'
        elif percentage >= 70:
            self.grade = 'B+'
        elif percentage >= 60:
            self.grade = 'B'
        elif percentage >= 50:
            self.grade = 'C'
        elif percentage >= 40:
            self.grade = 'D'
        else:
            self.grade = 'F'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.student} - {self.exam} - {self.marks_obtained}"

class FeeStructure(models.Model):
    """School fee structure"""
    class_grade = models.ForeignKey(ClassGrade, on_delete=models.CASCADE, related_name='fee_structure')
    term = models.CharField(max_length=50, choices=[('Term 1', 'Term 1'), ('Term 2', 'Term 2'), ('Annual', 'Annual')])
    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2)
    library_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sports_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    laboratory_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    miscellaneous_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    due_date = models.DateField()
    
    @property
    def total_fee(self):
        return self.tuition_fee + self.library_fee + self.sports_fee + self.laboratory_fee + self.transport_fee + self.miscellaneous_fee
    
    def __str__(self):
        return f"Fee Structure - {self.class_grade} - {self.term}"

class FeePayment(models.Model):
    """Student fee payments"""
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='fee_payments')
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(auto_now_add=True)
    payment_method = models.CharField(max_length=50, choices=[('Cash', 'Cash'), ('Card', 'Card'), ('Online', 'Online')])
    receipt_number = models.CharField(max_length=50, unique=True)
    remarks = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"{self.student} - {self.fee_structure} - {self.amount_paid}"