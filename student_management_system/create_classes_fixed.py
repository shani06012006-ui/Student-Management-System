import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.models import ClassGrade

# Create classes for grades 1-10 with sections A, B, C
created_count = 0
for grade in range(1, 11):
    for section in ['A', 'B', 'C']:
        obj, created = ClassGrade.objects.get_or_create(
            grade=grade,
            section=section,
            academic_year='2024-2025',
            defaults={
                'grade': grade,
                'section': section,
                'academic_year': '2024-2025'
            }
        )
        if created:
            created_count += 1
            print(f'Created: Grade {grade} - Section {section}')

print(f'\n✅ Successfully created {created_count} new classes')
print(f'📊 Total classes in database: {ClassGrade.objects.count()}')
