from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.models import Teacher, Subject

class Command(BaseCommand):
    help = 'Create sample teachers'

    def handle(self, *args, **options):
        # Create subjects if they don't exist
        subjects_data = [
            ('Mathematics', 'MATH01'),
            ('Science', 'SCI01'),
            ('English', 'ENG01'),
            ('Hindi', 'HIN01'),
            ('Social Studies', 'SOC01'),
        ]
        
        subjects = []
        for name, code in subjects_data:
            subject, created = Subject.objects.get_or_create(
                name=name,
                defaults={'code': code}
            )
            subjects.append(subject)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created subject: {name}'))

        # Create teachers
        teachers_data = [
            {
                'username': 'teacher1',
                'password': 'teacher123',
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john.doe@school.com',
                'employee_id': 'TCH001',
                'qualification': 'M.Sc, B.Ed',
                'experience': 5,
                'phone': '9876543210',
                'address': '123 Main Street',
                'subjects': [0, 1]  # Mathematics, Science
            },
            {
                'username': 'teacher2',
                'password': 'teacher123',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'email': 'jane.smith@school.com',
                'employee_id': 'TCH002',
                'qualification': 'M.A, B.Ed',
                'experience': 3,
                'phone': '9876543211',
                'address': '456 Oak Avenue',
                'subjects': [1, 2]  # Science, English
            },
            {
                'username': 'teacher3',
                'password': 'teacher123',
                'first_name': 'Robert',
                'last_name': 'Johnson',
                'email': 'robert.j@school.com',
                'employee_id': 'TCH003',
                'qualification': 'M.Com, B.Ed',
                'experience': 4,
                'phone': '9876543212',
                'address': '789 Pine Road',
                'subjects': [3, 4]  # Hindi, Social Studies
            },
        ]

        created_count = 0
        for data in teachers_data:
            # Check if teacher already exists
            if Teacher.objects.filter(employee_id=data['employee_id']).exists():
                self.stdout.write(f"Teacher {data['employee_id']} already exists")
                continue
                
            # Create user
            user = User.objects.create_user(
                username=data['username'],
                password=data['password'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                email=data['email']
            )
            
            # Create teacher
            teacher = Teacher.objects.create(
                user=user,
                employee_id=data['employee_id'],
                qualification=data['qualification'],
                experience_years=data['experience'],
                phone_number=data['phone'],
                address=data['address'],
                joining_date='2024-01-01'
            )
            
            # Assign subjects
            subject_list = [subjects[i] for i in data['subjects']]
            teacher.subjects.set(subject_list)
            
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'Created teacher: {data["first_name"]} {data["last_name"]} ({data["employee_id"]})')
            )

        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Successfully created {created_count} teachers')
        )
        self.stdout.write(
            self.style.SUCCESS(f'📊 Total teachers: {Teacher.objects.count()}')
        )
