from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='apps/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Student URLs
    path('students/', views.student_list, name='student_list'),
    path('students/add/', views.student_add, name='student_add'),
    path('students/<int:pk>/', views.student_detail, name='student_detail'),
    path('students/<int:pk>/edit/', views.student_edit, name='student_edit'),
    path('students/<int:pk>/delete/', views.student_delete, name='student_delete'),
    
    # Attendance URLs
    path('attendance/mark/', views.mark_attendance, name='mark_attendance'),
    path('attendance/report/', views.attendance_report, name='attendance_report'),
    
    # Teacher URLs
    path('teachers/', views.teacher_list, name='teacher_list'),
    path('teachers/add/', views.teacher_add, name='teacher_add'),
    path('teachers/<int:pk>/', views.teacher_detail, name='teacher_detail'),
    path('teachers/<int:pk>/edit/', views.teacher_edit, name='teacher_edit'),
    path('teachers/<int:pk>/delete/', views.teacher_delete, name='teacher_delete'),
    
    # Exam URLs
    path('exams/', views.exam_list, name='exam_list'),
    path('exams/add/', views.exam_add, name='exam_add'),
    path('exams/<int:exam_id>/marks/', views.enter_marks, name='enter_marks'),
    path('exams/<int:pk>/edit/', views.exam_edit, name='exam_edit'),
    path('exams/<int:pk>/delete/', views.exam_delete, name='exam_delete'),
    
    # Marksheet
    path('marksheet/<int:student_id>/', views.marksheet, name='marksheet'),
    
    # Fee Management
    path('fee-structures/', views.fee_structure_list, name='fee_structure_list'),
    path('fee-structures/add/', views.fee_structure_add, name='fee_structure_add'),
    path('fee-structures/<int:pk>/edit/', views.fee_structure_edit, name='fee_structure_edit'),
    path('fee-structures/<int:pk>/delete/', views.fee_structure_delete, name='fee_structure_delete'),
    
    # API URLs
    path('api/get-students/', views.get_students_by_class, name='get_students_by_class'),
    path('api/get-exam-details/', views.get_exam_details, name='get_exam_details'),
    path('api/get-fee-structure/', views.get_fee_structure, name='get_fee_structure'),
    path('api/get-subjects-by-class/', views.get_subjects_by_class, name='get_subjects_by_class'),
    path('api/dashboard-stats/', views.dashboard_stats_api, name='dashboard_stats_api'),
    path('teachers/<int:pk>/delete/', views.teacher_delete, name='teacher_delete'),
]