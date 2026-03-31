from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count, Avg, Sum
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta, date
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from .models import Student, Teacher, Attendance, Exam, Marks, FeeStructure, FeePayment
from .models import *
from .forms import *

# ============================================
# HELPER FUNCTIONS
# ============================================

def is_admin(user):
    """Check if user is admin"""
    return user.is_staff or user.is_superuser

def is_teacher(user):
    """Check if user is teacher"""
    return hasattr(user, 'teacher_profile')

# ============================================
# DASHBOARD VIEW
# ============================================

@login_required
def dashboard(request):
    """Main dashboard showing overview"""
    total_students = Student.objects.filter(is_active=True).count()
    total_teachers = Teacher.objects.count()
    total_classes = ClassGrade.objects.count()
    
    # Recent attendance
    today = date.today()
    present_today = Attendance.objects.filter(date=today, status='P').count()
    absent_today = Attendance.objects.filter(date=today, status='A').count()
    
    # Upcoming exams
    upcoming_exams = Exam.objects.filter(exam_date__gte=today).order_by('exam_date')[:5]
    
    # Recent fee payments
    recent_payments = FeePayment.objects.order_by('-payment_date')[:5]
    
    context = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_classes': total_classes,
        'present_today': present_today,
        'absent_today': absent_today,
        'upcoming_exams': upcoming_exams,
        'recent_payments': recent_payments,
    }
    
    return render(request, 'apps/dashboard.html', context)


def dashboard_stats_api(request):
    """API endpoint for dashboard charts"""
    today = date.today()
    
    # Attendance for last 7 days
    last_week = today - timedelta(days=7)
    attendance_stats = Attendance.objects.filter(date__gte=last_week).values('date').annotate(
        present=Count('id', filter=Q(status='P')),
        absent=Count('id', filter=Q(status='A')),
        late=Count('id', filter=Q(status='L'))
    ).order_by('date')
    
    # Class distribution
    class_distribution = Student.objects.filter(is_active=True).values('current_class__grade').annotate(
        count=Count('id')
    ).order_by('current_class__grade')
    
    data = {
        'attendance': list(attendance_stats),
        'class_distribution': list(class_distribution),
    }
    return JsonResponse(data)


# ============================================
# STUDENT VIEWS
# ============================================

@login_required
def student_list(request):
    """List all students with filters and pagination"""
    students = Student.objects.filter(is_active=True)
    
    # Filter by class
    class_id = request.GET.get('class')
    if class_id:
        students = students.filter(current_class_id=class_id)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        students = students.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(student_id__icontains=search_query) |
            Q(father_name__icontains=search_query) |
            Q(mother_name__icontains=search_query)
        )
    
    # Exclude students without valid primary keys
    students = students.exclude(pk__isnull=True)
    
    # Pagination
    paginator = Paginator(students, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'students': page_obj,
        'classes': ClassGrade.objects.all(),
        'search_query': search_query,
        'selected_class': class_id,
    }
    return render(request, 'apps/student_list.html', context)


@login_required
def student_detail(request, pk):
    """View student details"""
    student = get_object_or_404(Student, pk=pk)
    attendance = Attendance.objects.filter(student=student)[:30]
    marks = Marks.objects.filter(student=student).select_related('exam')
    fee_payments = FeePayment.objects.filter(student=student)
    
    context = {
        'student': student,
        'attendance': attendance,
        'marks': marks,
        'fee_payments': fee_payments,
    }
    return render(request, 'apps/student_detail.html', context)


@user_passes_test(is_admin)
def student_add(request):
    """Add new student"""
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save(commit=False)
            
            # Generate student ID
            class_grade = student.current_class
            last_student = Student.objects.filter(current_class=class_grade).order_by('-roll_number').first()
            roll_number = last_student.roll_number + 1 if last_student else 1
            
            student.roll_number = roll_number
            student.student_id = f"SCH{datetime.now().year}{class_grade.grade}{class_grade.section}{roll_number:03d}"
            student.created_by = request.user
            student.save()
            
            messages.success(request, f'Student {student.full_name} added successfully!')
            return redirect('student_detail', pk=student.pk)
    else:
        form = StudentRegistrationForm()
    
    return render(request, 'apps/student_form.html', {'form': form, 'title': 'Add Student'})


@user_passes_test(is_admin)
def student_edit(request, pk):
    """Edit student details"""
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Student details updated successfully!')
                return redirect('student_detail', pk=student.pk)
            except Exception as e:
                messages.error(request, f'Error updating student: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StudentRegistrationForm(instance=student)
    
    return render(request, 'apps/student_form.html', {'form': form, 'title': 'Edit Student'})


# ============================================
# STUDENT DELETE VIEW
# ============================================
@login_required
def student_delete(request, pk):
    """Delete student"""
    student = get_object_or_404(Student, pk=pk)
    try:
        student_name = student.full_name
        student.delete()
        messages.success(request, f'Student "{student_name}" deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting student: {str(e)}')
    return redirect('student_list')


# ============================================
# ATTENDANCE VIEWS
# ============================================

@login_required
def mark_attendance(request):
    """Mark daily attendance"""
    if request.method == 'POST':
        class_id = request.POST.get('class_grade')
        attendance_date = request.POST.get('date')
        class_grade = get_object_or_404(ClassGrade, pk=class_id)
        students = Student.objects.filter(current_class=class_grade, is_active=True)
        
        for student in students:
            status = request.POST.get(f'status_{student.id}', 'A')
            Attendance.objects.update_or_create(
                student=student,
                date=attendance_date,
                defaults={
                    'status': status,
                    'class_grade': class_grade,
                    'marked_by': request.user.teacher_profile if hasattr(request.user, 'teacher_profile') else None
                }
            )
        
        messages.success(request, f'Attendance marked for {class_grade} on {attendance_date}')
        return redirect('attendance_report')
    
    # Handle GET request with filters
    class_id = request.GET.get('class_grade')
    attendance_date = request.GET.get('date')
    
    students = None
    selected_class = None
    
    if class_id and attendance_date:
        try:
            selected_class = ClassGrade.objects.get(pk=class_id)
            students = Student.objects.filter(
                current_class=selected_class, 
                is_active=True
            ).order_by('roll_number')
        except ClassGrade.DoesNotExist:
            messages.error(request, 'Selected class does not exist')
    
    context = {
        'classes': ClassGrade.objects.all(),
        'today': date.today(),
        'students': students,
        'selected_class': selected_class,
    }
    return render(request, 'apps/mark_attendance.html', context)


@login_required
def attendance_report(request):
    """View attendance reports"""
    class_id = request.GET.get('class')
    start_date = request.GET.get('start_date', date.today() - timedelta(days=30))
    end_date = request.GET.get('end_date', date.today())
    
    # Convert string dates to date objects if they are strings
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    attendance = Attendance.objects.filter(date__range=[start_date, end_date])
    
    if class_id:
        attendance = attendance.filter(class_grade_id=class_id)
    
    # Group by student
    report_data = []
    students = Student.objects.filter(is_active=True)
    if class_id:
        students = students.filter(current_class_id=class_id)
        
    for student in students:
        student_attendance = attendance.filter(student=student)
        total_days = student_attendance.count()
        present_days = student_attendance.filter(status='P').count()
        absent_days = student_attendance.filter(status='A').count()
        late_days = student_attendance.filter(status='L').count()
        sick_days = student_attendance.filter(status='S').count()
        
        if total_days > 0:
            attendance_percentage = ((present_days + late_days) / total_days) * 100
        else:
            attendance_percentage = 0
        
        report_data.append({
            'student': student,
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'late_days': late_days,
            'sick_days': sick_days,
            'attendance_percentage': round(attendance_percentage, 2)
        })
    
    context = {
        'report_data': report_data,
        'classes': ClassGrade.objects.all(),
        'selected_class': class_id,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'apps/attendance_report.html', context)


# ============================================
# TEACHER VIEWS
# ============================================

@login_required
def teacher_list(request):
    """List all teachers with search functionality"""
    teachers = Teacher.objects.all().select_related('user').prefetch_related('subjects')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        teachers = teachers.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(employee_id__icontains=search_query) |
            Q(qualification__icontains=search_query)
        )
    
    # Calculate statistics
    class_teachers_count = teachers.filter(is_class_teacher=True).count()
    total_subjects = Subject.objects.count()
    avg_experience = teachers.aggregate(Avg('experience_years'))['experience_years__avg'] or 0
    
    context = {
        'teachers': teachers,
        'class_teachers_count': class_teachers_count,
        'total_subjects': total_subjects,
        'avg_experience': round(avg_experience, 1),
    }
    return render(request, 'apps/teacher_list.html', context)


@login_required
def teacher_add(request):
    """Add new teacher"""
    if request.method == 'POST':
        try:
            # Get form data
            username = request.POST.get('username')
            password = request.POST.get('password')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            employee_id = request.POST.get('employee_id')
            qualification = request.POST.get('qualification')
            experience_years = request.POST.get('experience_years', 0)
            phone_number = request.POST.get('phone_number')
            address = request.POST.get('address')
            joining_date = request.POST.get('joining_date')
            is_class_teacher = request.POST.get('is_class_teacher') == 'on'
            subject_ids = request.POST.getlist('subjects')
            
            # Check if username already exists
            if User.objects.filter(username=username).exists():
                messages.error(request, f'Username "{username}" already exists!')
                return redirect('teacher_add')
            
            # Check if employee_id already exists
            if Teacher.objects.filter(employee_id=employee_id).exists():
                messages.error(request, f'Employee ID "{employee_id}" already exists!')
                return redirect('teacher_add')
            
            # Create user
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                email=email
            )
            
            # Create teacher
            teacher = Teacher.objects.create(
                user=user,
                employee_id=employee_id,
                qualification=qualification,
                experience_years=experience_years,
                phone_number=phone_number,
                address=address,
                joining_date=joining_date,
                is_class_teacher=is_class_teacher
            )
            
            # Add subjects
            if subject_ids:
                teacher.subjects.set(subject_ids)
            
            messages.success(request, f'Teacher {first_name} {last_name} added successfully!')
            return redirect('teacher_list')
            
        except Exception as e:
            messages.error(request, f'Error adding teacher: {str(e)}')
            return redirect('teacher_add')
    
    context = {
        'title': 'Add New Teacher',
        'subjects': Subject.objects.all(),
        'today': date.today(),
    }
    return render(request, 'apps/teacher_form.html', context)


@login_required
def teacher_edit(request, pk):
    """Edit teacher details"""
    teacher = get_object_or_404(Teacher, pk=pk)
    
    if request.method == 'POST':
        try:
            # Update user information
            teacher.user.first_name = request.POST.get('first_name')
            teacher.user.last_name = request.POST.get('last_name')
            teacher.user.email = request.POST.get('email')
            teacher.user.save()
            
            # Update teacher information
            teacher.qualification = request.POST.get('qualification')
            teacher.experience_years = request.POST.get('experience_years', 0)
            teacher.phone_number = request.POST.get('phone_number')
            teacher.address = request.POST.get('address')
            teacher.joining_date = request.POST.get('joining_date')
            teacher.is_class_teacher = request.POST.get('is_class_teacher') == 'on'
            
            # Update subjects
            subject_ids = request.POST.getlist('subjects')
            teacher.subjects.set(subject_ids)
            
            teacher.save()
            
            messages.success(request, f'Teacher {teacher.user.get_full_name()} updated successfully!')
            return redirect('teacher_list')
            
        except Exception as e:
            messages.error(request, f'Error updating teacher: {str(e)}')
    
    context = {
        'title': 'Edit Teacher',
        'teacher': teacher,
        'subjects': Subject.objects.all(),
        'today': date.today(),
    }
    return render(request, 'apps/teacher_form.html', context)


@login_required
def teacher_detail(request, pk):
    """View teacher details"""
    teacher = get_object_or_404(Teacher, pk=pk)
    context = {
        'teacher': teacher,
    }
    return render(request, 'apps/teacher_detail.html', context)


# ============================================
# TEACHER DELETE VIEW
# ============================================
@login_required
def teacher_delete(request, pk):
    """Delete teacher"""
    teacher = get_object_or_404(Teacher, pk=pk)
    try:
        teacher_name = teacher.user.get_full_name()
        # Delete user (will cascade delete teacher)
        teacher.user.delete()
        messages.success(request, f'Teacher "{teacher_name}" deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting teacher: {str(e)}')
    return redirect('teacher_list')


# ============================================
# EXAM VIEWS
# ============================================

@login_required
def exam_list(request):
    """List all exams"""
    exams = Exam.objects.all().select_related('class_grade', 'subject')
    
    # Filter by class
    class_id = request.GET.get('class')
    if class_id:
        exams = exams.filter(class_grade_id=class_id)
    
    # Filter by upcoming/past
    filter_type = request.GET.get('filter', 'all')
    today = date.today()
    
    if filter_type == 'upcoming':
        exams = exams.filter(exam_date__gte=today)
    elif filter_type == 'past':
        exams = exams.filter(exam_date__lt=today)
    
    context = {
        'exams': exams.order_by('exam_date'),
        'classes': ClassGrade.objects.all(),
        'subjects': Subject.objects.all(),
    }
    return render(request, 'apps/exam_list.html', context)


@login_required
def exam_add(request):
    """Add new exam"""
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name')
        exam_type = request.POST.get('exam_type')
        class_grade_id = request.POST.get('class_grade')
        subject_id = request.POST.get('subject')
        exam_date = request.POST.get('exam_date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        total_marks = request.POST.get('total_marks')
        passing_marks = request.POST.get('passing_marks')
        
        # Validate required fields
        if not all([name, exam_type, class_grade_id, subject_id, exam_date, start_time, end_time, total_marks, passing_marks]):
            messages.error(request, 'All fields are required!')
        else:
            # Create exam
            Exam.objects.create(
                name=name,
                exam_type=exam_type,
                class_grade_id=class_grade_id,
                subject_id=subject_id,
                exam_date=exam_date,
                start_time=start_time,
                end_time=end_time,
                total_marks=total_marks,
                passing_marks=passing_marks
            )
            messages.success(request, 'Exam added successfully!')
            return redirect('exam_list')
    
    context = {
        'classes': ClassGrade.objects.all(),
        'subjects': Subject.objects.all(),
    }
    return render(request, 'apps/exam_add.html', context)


@login_required
def exam_edit(request, pk):
    """Edit exam"""
    exam = get_object_or_404(Exam, pk=pk)
    
    if request.method == 'POST':
        exam.name = request.POST.get('name')
        exam.exam_type = request.POST.get('exam_type')
        exam.class_grade_id = request.POST.get('class_grade')
        exam.subject_id = request.POST.get('subject')
        exam.exam_date = request.POST.get('exam_date')
        exam.start_time = request.POST.get('start_time')
        exam.end_time = request.POST.get('end_time')
        exam.total_marks = request.POST.get('total_marks')
        exam.passing_marks = request.POST.get('passing_marks')
        exam.save()
        
        messages.success(request, f'Exam "{exam.name}" updated successfully!')
        return redirect('exam_list')
    
    context = {
        'exam': exam,
        'classes': ClassGrade.objects.all(),
        'subjects': Subject.objects.all(),
    }
    return render(request, 'apps/exam_edit.html', context)
    
    
# ============================================
# EXAM DELETE VIEW
# ============================================
@login_required
def exam_delete(request, pk):
    """Delete exam"""
    exam = get_object_or_404(Exam, pk=pk)
    try:
        exam_name = exam.name
        exam.delete()
        messages.success(request, f'Exam "{exam_name}" deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting exam: {str(e)}')
    return redirect('exam_list')


@login_required
def enter_marks(request, exam_id):
    """Enter marks for an exam"""
    exam = get_object_or_404(Exam, pk=exam_id)
    students = Student.objects.filter(current_class=exam.class_grade, is_active=True).order_by('roll_number')
    
    if request.method == 'POST':
        for student in students:
            marks_obtained = request.POST.get(f'marks_{student.id}')
            if marks_obtained and marks_obtained.strip():
                try:
                    marks_float = float(marks_obtained)
                    Marks.objects.update_or_create(
                        student=student,
                        exam=exam,
                        defaults={
                            'marks_obtained': marks_float,
                            'entered_by': request.user.teacher_profile if hasattr(request.user, 'teacher_profile') else None,
                            'remarks': request.POST.get(f'remarks_{student.id}', '')
                        }
                    )
                except ValueError:
                    continue
        
        messages.success(request, f'Marks entered successfully for {exam.name}')
        return redirect('exam_list')
    
    # Get existing marks
    existing_marks = Marks.objects.filter(exam=exam).select_related('student')
    marks_dict = {mark.student_id: mark for mark in existing_marks}
    
    context = {
        'exam': exam,
        'students': students,
        'existing_marks': marks_dict,
    }
    return render(request, 'apps/enter_marks.html', context)


@login_required
def marksheet(request, student_id):
    """Generate marksheet for a student"""
    student = get_object_or_404(Student, pk=student_id)
    exams = Exam.objects.filter(class_grade=student.current_class).select_related('subject')
    
    marks_data = {}
    for exam in exams:
        try:
            marks = Marks.objects.get(student=student, exam=exam)
            marks_data[exam] = marks
        except Marks.DoesNotExist:
            marks_data[exam] = None
    
    # Calculate overall performance
    total_marks = 0
    max_marks = 0
    for exam, marks in marks_data.items():
        if marks:
            total_marks += marks.marks_obtained
            max_marks += exam.total_marks
    
    percentage = (total_marks / max_marks * 100) if max_marks > 0 else 0
    
    # Determine grade
    if percentage >= 90:
        grade = 'A+'
    elif percentage >= 80:
        grade = 'A'
    elif percentage >= 70:
        grade = 'B+'
    elif percentage >= 60:
        grade = 'B'
    elif percentage >= 50:
        grade = 'C'
    elif percentage >= 40:
        grade = 'D'
    else:
        grade = 'F'
    
    context = {
        'student': student,
        'marks_data': marks_data,
        'total_marks': total_marks,
        'max_marks': max_marks,
        'percentage': round(percentage, 2),
        'grade': grade,
    }
    return render(request, 'apps/marksheet.html', context)


# ============================================
# FEE MANAGEMENT VIEWS
# ============================================

@login_required
def fee_structure_list(request):
    """List all fee structures with filters"""
    fee_structures = FeeStructure.objects.all().select_related('class_grade')
    
    # Apply filters
    class_id = request.GET.get('class')
    if class_id:
        fee_structures = fee_structures.filter(class_grade_id=class_id)
    
    term = request.GET.get('term')
    if term:
        fee_structures = fee_structures.filter(term=term)
    
    # Calculate statistics
    total_classes = ClassGrade.objects.count()
    avg_fee = fee_structures.aggregate(Avg('tuition_fee'))['tuition_fee__avg'] or 0
    
    # Count fees due this month
    today = date.today()
    next_month = today + timedelta(days=30)
    due_this_month = fee_structures.filter(due_date__range=[today, next_month]).count()
    
    context = {
        'fee_structures': fee_structures,
        'classes': ClassGrade.objects.all(),
        'total_classes': total_classes,
        'avg_fee': avg_fee,
        'due_this_month': due_this_month,
        'today': today,
    }
    return render(request, 'apps/fee_structure_list.html', context)


@login_required
def fee_structure_add(request):
    """Add new fee structure"""
    if request.method == 'POST':
        try:
            # Get form data
            class_grade_id = request.POST.get('class_grade')
            term = request.POST.get('term')
            tuition_fee = request.POST.get('tuition_fee', 0)
            library_fee = request.POST.get('library_fee', 0)
            sports_fee = request.POST.get('sports_fee', 0)
            laboratory_fee = request.POST.get('laboratory_fee', 0)
            transport_fee = request.POST.get('transport_fee', 0)
            miscellaneous_fee = request.POST.get('miscellaneous_fee', 0)
            due_date = request.POST.get('due_date')
            
            # Check if fee structure already exists for this class and term
            if FeeStructure.objects.filter(class_grade_id=class_grade_id, term=term).exists():
                messages.error(request, f'Fee structure already exists for this class and term!')
                return redirect('fee_structure_add')
            
            # Create fee structure
            FeeStructure.objects.create(
                class_grade_id=class_grade_id,
                term=term,
                tuition_fee=tuition_fee,
                library_fee=library_fee,
                sports_fee=sports_fee,
                laboratory_fee=laboratory_fee,
                transport_fee=transport_fee,
                miscellaneous_fee=miscellaneous_fee,
                due_date=due_date
            )
            
            messages.success(request, 'Fee structure added successfully!')
            return redirect('fee_structure_list')
            
        except Exception as e:
            messages.error(request, f'Error adding fee structure: {str(e)}')
    
    context = {
        'title': 'Add Fee Structure',
        'classes': ClassGrade.objects.all(),
        'today': date.today(),
    }
    return render(request, 'apps/fee_structure_form.html', context)


@login_required
def fee_structure_edit(request, pk):
    """Edit fee structure"""
    fee_structure = get_object_or_404(FeeStructure, pk=pk)
    
    if request.method == 'POST':
        try:
            # Update fee structure
            fee_structure.class_grade_id = request.POST.get('class_grade')
            fee_structure.term = request.POST.get('term')
            fee_structure.tuition_fee = request.POST.get('tuition_fee', 0)
            fee_structure.library_fee = request.POST.get('library_fee', 0)
            fee_structure.sports_fee = request.POST.get('sports_fee', 0)
            fee_structure.laboratory_fee = request.POST.get('laboratory_fee', 0)
            fee_structure.transport_fee = request.POST.get('transport_fee', 0)
            fee_structure.miscellaneous_fee = request.POST.get('miscellaneous_fee', 0)
            fee_structure.due_date = request.POST.get('due_date')
            fee_structure.save()
            
            messages.success(request, 'Fee structure updated successfully!')
            return redirect('fee_structure_list')
            
        except Exception as e:
            messages.error(request, f'Error updating fee structure: {str(e)}')
    
    context = {
        'title': 'Edit Fee Structure',
        'fee_structure': fee_structure,
        'classes': ClassGrade.objects.all(),
        'today': date.today(),
    }
    return render(request, 'apps/fee_structure_form.html', context)


# ============================================
# FEE STRUCTURE DELETE VIEW
# ============================================
@login_required
def fee_structure_delete(request, pk):
    """Delete fee structure"""
    fee_structure = get_object_or_404(FeeStructure, pk=pk)
    try:
        class_info = f"{fee_structure.class_grade} - {fee_structure.term}"
        fee_structure.delete()
        messages.success(request, f'Fee structure for {class_info} deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting fee structure: {str(e)}')
    return redirect('fee_structure_list')


# ============================================
# API VIEWS (AJAX)
# ============================================

def get_students_by_class(request):
    """API endpoint to get students for a class"""
    class_id = request.GET.get('class_id')
    if not class_id:
        return JsonResponse({'error': 'No class ID provided'}, status=400)
    
    try:
        students = Student.objects.filter(
            current_class_id=class_id, 
            is_active=True
        ).values('id', 'first_name', 'last_name', 'roll_number').order_by('roll_number')
        
        # Convert to list for JSON response
        student_list = list(students)
        return JsonResponse(student_list, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_exam_details(request):
    """API endpoint to get exam details"""
    exam_id = request.GET.get('exam_id')
    exam = get_object_or_404(Exam, pk=exam_id)
    data = {
        'id': exam.id,
        'name': exam.name,
        'total_marks': exam.total_marks,
        'passing_marks': exam.passing_marks,
        'date': exam.exam_date.strftime('%Y-%m-%d'),
        'class': str(exam.class_grade),
        'subject': str(exam.subject),
    }
    return JsonResponse(data)


def get_fee_structure(request):
    """API endpoint to get fee structure details"""
    fee_id = request.GET.get('fee_id')
    fee = get_object_or_404(FeeStructure, pk=fee_id)
    data = {
        'id': fee.id,
        'total_fee': float(fee.total_fee),
        'term': fee.term,
        'due_date': fee.due_date.strftime('%Y-%m-%d'),
    }
    return JsonResponse(data)


def get_subjects_by_class(request):
    """API endpoint to get subjects for a class"""
    class_id = request.GET.get('class_id')
    if not class_id:
        return JsonResponse({'error': 'No class ID provided'}, status=400)
    
    try:
        class_grade = get_object_or_404(ClassGrade, pk=class_id)
        subjects = class_grade.subjects.all().values('id', 'name', 'code')
        return JsonResponse(list(subjects), safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)