from django.conf import settings
from django.core.management.base import BaseCommand

from apps.users.models import User, UserProfile


class Command(BaseCommand):
    help = 'Ensure the single standard admin account exists and demote other admin users.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--password',
            default='admin123',
            help='Password for the standard admin account (default: admin123)',
        )

    def handle(self, *args, **options):
        admin_email = settings.ADMIN_EMAIL
        password = options['password']

        demoted = User.objects.filter(role='admin').exclude(
            email__iexact=admin_email
        ).update(role='user', is_staff=False, is_superuser=False)

        if demoted:
            self.stdout.write(self.style.WARNING(
                f'Demoted {demoted} non-standard admin account(s) to user role.'
            ))

        admin_user, created = User.objects.get_or_create(
            email=admin_email,
            defaults={
                'employee_id': 'ADMIN001',
                'first_name': 'Admin',
                'last_name': 'User',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
            },
        )

        if created:
            admin_user.set_password(password)
            admin_user.save()
            UserProfile.objects.create(user=admin_user)
            self.stdout.write(self.style.SUCCESS(
                f'Created standard admin: {admin_email}'
            ))
        else:
            admin_user.role = 'admin'
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.is_active = True
            admin_user.save(update_fields=[
                'role', 'is_staff', 'is_superuser', 'is_active', 'updated_at',
            ])
            UserProfile.objects.get_or_create(user=admin_user)
            self.stdout.write(self.style.SUCCESS(
                f'Standard admin verified: {admin_email}'
            ))

        self.stdout.write(f'Admin portal login: {admin_email} / {password}')
