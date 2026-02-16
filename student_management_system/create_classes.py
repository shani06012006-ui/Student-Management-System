from apps.models import ClassGrade

# Create classes for grades 1-10 with sections A, B, C
for grade in range(1, 11):
    for section in ['A', 'B', 'C']:
        ClassGrade.objects.get_or_create(
            grade=grade,
            section=section,
            academic_year='2024-2025',
            defaults={
                'grade': grade,
                'section': section,
                'academic_year': '2024-2025'
            }
        )

print('Classes created successfully!')
print('Total classes:', ClassGrade.objects.count())
