import uuid
from django.core.management.base import BaseCommand
from cards.models import EmployeeCard


class Command(BaseCommand):
    help = 'Явно добавить 5 вымышленных визиток. Существующие записи не меняются.'

    def handle(self, *args, **options):
        names = [('Александр Иванов', 'Менеджер по работе с клиентами'),
                 ('Мария Петрова', 'Руководитель отдела продаж'),
                 ('Дмитрий Соколов', 'Инженер'),
                 ('Анна Смирнова', 'Специалист по работе с партнёрами'),
                 ('Сергей Волков', 'Руководитель проектов')]
        for index, (name, title) in enumerate(names, start=1):
            card, created = EmployeeCard.objects.get_or_create(
                pk=uuid.uuid5(uuid.NAMESPACE_URL, f'https://example.com/kmz-demo/{index}'), defaults={
                    'full_name': name, 'job_title': title, 'email': f'employee{index}@example.com',
                    'description': 'Демонстрационная визитка. Данные сотрудника вымышленные.',
                    'is_active': True,
                })
            self.stdout.write(f'{"Создана" if created else "Уже существует"}: {card.get_absolute_url()}')
