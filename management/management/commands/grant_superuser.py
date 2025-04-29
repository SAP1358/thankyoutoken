# yourapp/management/commands/grant_superuser.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Grants superuser status to an existing user'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username of the existing user')

    def handle(self, *args, **options):
        username = options['username']
        User = get_user_model()
        try:
            user = User.objects.get(username=username)
            user.is_superuser = True
            user.is_staff = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f"Successfully granted superuser status to {username}"))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User with username {username} does not exist"))
