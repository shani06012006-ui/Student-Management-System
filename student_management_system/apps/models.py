from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from datetime import date

# ✅ CLASS MODEL (Fixed with 'level' field)
class ClassGrade(models.Model):
    CLASS_CHOICES = [
        ('PKG', 'Pre-K.G'), ('LKG', 'L.K.G'), ('UKG', 'U.K.G'),
        ('1', '1st'), ('2', '2nd'), ('3', '3rd'), ('4', '4th'), ('5', '5th'),
        ('6', '6th'), ('7', '7th'), ('8', '8th'), ('9', '9th'), ('10', '10th'),
        ('11', '11th'), ('12', '12th'),
    ]

    name = models.CharField(max_length=10, choices=CLASS_CHOICES, unique=True)
    level = models.IntegerField(default=0) # 👈 Indha line thaan miss aachu!

    class Meta:
        ordering = ['level']

    def __str__(self):
        return self.get_name_display()


# ✅ SUBJECT
class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    grades = models.ManyToManyField(ClassGrade, related_name='subjects')
    is_optional = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


# ✅ STUDENT
class Student(models.Model):
    BLOOD_GROUP_CHOICES = [('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), ('O+', 'O+'), ('O-', 'O-'), ('AB+', 'AB+'), ('AB-', 'AB-')]
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
    address = models.TextField()
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)
    pincode = models.CharField(max_length=6)
    father_name = models.CharField(max_length=100)
    father_phone = models.CharField(max_length=15)
    mother_name = models.CharField(max_length=100)
    mother_phone = models.CharField(max_length=15)
    emergency_contact = models.CharField(max_length=15)
    profile_picture = models.ImageField(upload_to='students/profile/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['current_class', 'roll_number', 'first_name']
        unique_together = ['current_class', 'roll_number']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        today = date.today()
        return today.year - self.date_of_birth.year


# ✅ TEACHER
class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=20, unique=True)
    subjects = models.ManyToManyField(Subject)
    phone_number = models.CharField(max_length=15)
    joining_date = models.DateField()

    def __str__(self):
        return self.user.username


# ✅ ATTENDANCE
class Attendance(models.Model):
    STATUS_CHOICES = [('P', 'Present'), ('A', 'Absent')]
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    class_grade = models.ForeignKey(ClassGrade, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=1, choices=STATUS_CHOICES)

    class Meta:
        unique_together = ['student', 'date']


# ✅ EXAM
class Exam(models.Model):
    name = models.CharField(max_length=100)
    class_grade = models.ForeignKey(ClassGrade, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    exam_date = models.DateField()
    total_marks = models.IntegerField(default=100)

    def __str__(self):
        return self.name


# ✅ MARKS (Removed Duplicate and Added Remarks)
class Marks(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    marks_obtained = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    remarks = models.TextField(null=True, blank=True) 

    class Meta:
        unique_together = ['student', 'exam']


# ✅ FEE STRUCTURE
class FeeStructure(models.Model):
    class_grade = models.ForeignKey(ClassGrade, on_delete=models.CASCADE)
    academic_year = models.CharField(max_length=10)
    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2)
    transport_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    other_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Fee for {self.class_grade.name} ({self.academic_year})"


# ✅ FEE PAYMENT
class FeePayment(models.Model):
    PAYMENT_MODE = [('Cash', 'Cash'), ('Online', 'Online'), ('Cheque', 'Cheque')]
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(auto_now_add=True)
    payment_mode = models.CharField(max_length=10, choices=PAYMENT_MODE)
    receipt_number = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"{self.student.first_name} - {self.amount_paid}"