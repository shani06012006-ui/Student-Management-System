from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.http import JsonResponse
from datetime import datetime, timedelta, date
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from .models import Student, Teacher
from .models import *
from .forms import *
from .forms import TeacherForm


def is_admin(user):
    return user.is_staff or user.is_superuser

def is_teacher(user):
    return hasattr(user, 'teacher_profile')

@login_required
def dashboard(request):
    total_students = Student.objects.filter(is_active=True).count()
    total_teachers = Teacher.objects.count()
    total_classes = ClassGrade.objects.count()
    
 
    
    return render(request, 'apps/dashboard.html')


def dashboard_stats_api(request):
    
   
    class_distribution = Student.objects.filter(is_active=True).values('current_class__grade').annotate(
        count=Count('id')
    ).order_by('current_class__grade')
    
    data = {
        'class_distribution': list(class_distribution),
    }
    return JsonResponse(data)


@login_required
def student_list(request):
    students = Student.objects.filter(is_active=True)
    class_id = request.GET.get('class')
    if class_id:
        students = students.filter(current_class_id=class_id)
        
    search_query = request.GET.get('search')
    if search_query:
        students = students.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(student_id__icontains=search_query) |
            Q(father_name__icontains=search_query) |
            Q(mother_name__icontains=search_query)
        )
    
    
    students = students.exclude(pk__isnull=True)
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
    student = get_object_or_404(Student, pk=pk)
    fee_payments = FeePayment.objects.filter(student=student)
    
    context = {
        'student': student,
        'fee_payments': fee_payments,
    }
    return render(request, 'apps/student_detail.html', context)


@user_passes_test(is_admin)
def student_add(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)  
        
        if form.is_valid():
            student = form.save(commit=False)

            selected_class = student.current_class 

            last_student = Student.objects.filter(
                current_class=selected_class
            ).order_by('-roll_number').first()

            roll_number = (
                (last_student.roll_number + 1)
                if last_student and last_student.roll_number
                else 1
            )

            student.roll_number = roll_number

            year_str = datetime.now().year

            student.student_id = f"SCH{year_str}{selected_class.level}{roll_number:03d}"

            student.created_by = request.user
            student.save()

            messages.success(request, f'Student {student.first_name} added successfully!')
            return redirect('student_detail', pk=student.pk)

        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = StudentRegistrationForm()

    return render(request, 'apps/student_form.html', {
        'form': form,
        'title': 'Add Student'
    })

@user_passes_test(is_admin)
def student_edit(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student details updated successfully!')
            return redirect('student_detail', pk=student.pk)
    else:
        form = StudentRegistrationForm(instance=student)
    
    return render(request, 'apps/student_form.html', {'form': form, 'title': 'Edit Student'})

@login_required
def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    
    context = {
        'student': student,
    }
    return render(request, 'apps/student_detail.html', context)

# ============================================
# STUDENT DELETE VIEW
# ============================================
@login_required
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    try:
        student_name = student.full_name
        student.delete()
        messages.success(request, f'Student "{student_name}" deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting student: {str(e)}')
    return redirect('student_list')

# ============================================
# TEACHER VIEWS
# ============================================
@login_required
def teacher_list(request):
    teachers = Teacher.objects.all().select_related('user')
    
    search_query = request.GET.get('search')
    if search_query:
        teachers = teachers.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(employee_id__icontains=search_query) |
            Q(qualification__icontains=search_query)
        )
    
    class_teachers_count = teachers.filter(is_class_teacher=True).count()
    avg_experience = teachers.aggregate(Avg('experience_years'))['experience_years__avg'] or 0
    
    context = {
        'teachers': teachers,
        'class_teachers_count': class_teachers_count,
        'avg_experience': round(avg_experience, 1),
    }
    return render(request, 'apps/teacher_list.html', context)


@login_required
def teacher_add(request):
    if request.method == 'POST':
        form = TeacherForm(request.POST)
        if form.is_valid():
            teacher = form.save()
            messages.success(request, f'Teacher {teacher.user.get_full_name()} added successfully!')
            return redirect('teacher_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TeacherForm()
    
    return render(request, 'apps/teacher_form.html', {
        'form': form,
        'title': 'Add New Teacher',
        'teacher': None
    })


@login_required
def teacher_edit(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    
    if request.method == 'POST':
        try:
            teacher.user.first_name = request.POST.get('first_name')
            teacher.user.last_name = request.POST.get('last_name')
            teacher.user.email = request.POST.get('email')
            teacher.user.save()
            
            teacher.qualification = request.POST.get('qualification')
            teacher.experience_years = request.POST.get('experience_years', 0)
            teacher.phone_number = request.POST.get('phone_number')
            teacher.address = request.POST.get('address')
            teacher.joining_date = request.POST.get('joining_date')
            teacher.is_class_teacher = request.POST.get('is_class_teacher') == 'on'
        
            teacher.save()
            
            messages.success(request, f'Teacher {teacher.user.get_full_name()} updated successfully!')
            return redirect('teacher_list')
            
        except Exception as e:
            messages.error(request, f'Error updating teacher: {str(e)}')
    
    context = {
        'title': 'Edit Teacher',
        'teacher': teacher,
        'today': date.today(),
    }
    return render(request, 'apps/teacher_form.html', context)


@login_required
def teacher_detail(request, pk):
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
        teacher.user.delete()
        messages.success(request, f'Teacher "{teacher_name}" deleted successfully!')
    except Exception as e:
        messages.error(request, f'Error deleting teacher: {str(e)}')
    return redirect('teacher_list')


# ============================================
# FEE MANAGEMENT VIEWS
# ============================================
@login_required
def fee_structure_list(request):
    fee_structures = FeeStructure.objects.all().select_related('class_grade')
    
    class_id = request.GET.get('class')
    if class_id:
        fee_structures = fee_structures.filter(class_grade_id=class_id)
    
    term = request.GET.get('term')
    if term:
        fee_structures = fee_structures.filter(term=term)
    
    total_classes = ClassGrade.objects.count()
    avg_fee = fee_structures.aggregate(Avg('tuition_fee'))['tuition_fee__avg'] or 0
    
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
    if request.method == 'POST':
        try:
            class_grade_id = request.POST.get('class_grade')
            term = request.POST.get('term')
            tuition_fee = request.POST.get('tuition_fee', 0)
            library_fee = request.POST.get('library_fee', 0)
            sports_fee = request.POST.get('sports_fee', 0)
            laboratory_fee = request.POST.get('laboratory_fee', 0)
            transport_fee = request.POST.get('transport_fee', 0)
            miscellaneous_fee = request.POST.get('miscellaneous_fee', 0)
            due_date = request.POST.get('due_date')
            
            if FeeStructure.objects.filter(class_grade_id=class_grade_id, term=term).exists():
                messages.error(request, f'Fee structure already exists for this class and term!')
                return redirect('fee_structure_add')
            
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
    fee_structure = get_object_or_404(FeeStructure, pk=pk)
    
    if request.method == 'POST':
        try:
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
    class_id = request.GET.get('class_id')
    if not class_id:
        return JsonResponse({'error': 'No class ID provided'}, status=400)
    
    try:
        students = Student.objects.filter(
            current_class_id=class_id, 
            is_active=True
        ).values('id', 'first_name', 'last_name', 'roll_number').order_by('roll_number')
        
        student_list = list(students)
        return JsonResponse(student_list, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def get_fee_structure(request):
    fee_id = request.GET.get('fee_id')
    fee = get_object_or_404(FeeStructure, pk=fee_id)
    data = {
        'id': fee.id,
        'total_fee': float(fee.total_fee),
        'term': fee.term,
        'due_date': fee.due_date.strftime('%Y-%m-%d'),
    }
    return JsonResponse(data)



def generate_student_id():
    last_student = Student.objects.order_by('-id').first()

    if last_student and last_student.student_id:
        last_id = last_student.student_id
        number = int(last_id[-4:]) + 1
    else:
        number = 1

    return f"SCH2026{number:04d}"

