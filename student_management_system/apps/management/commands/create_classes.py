from django.core.management.base import BaseCommand
from apps.models import ClassGrade

class Command(BaseCommand):
    help = 'Create initial classes for the school'

    def handle(self, *args, **options):
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
                    self.stdout.write(
                        self.style.SUCCESS(f'Created: Grade {grade} - Section {section}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Successfully created {created_count} classes')
        )
        self.stdout.write(
            self.style.SUCCESS(f'📊 Total classes: {ClassGrade.objects.count()}')
        )
