from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from app.models import User


class Command(BaseCommand):
    help = "Seeds the database with initial users for testing"

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding data...")

        # --- ADMIN ACCOUNT ---

        # WARN: FLAW A02:2021 - Cryptographic Failures
        # We are writing raw plain-text strings directly into the password field.
        admin_user, created = User.objects.get_or_create(
            username="admin", defaults={"password_hash": "admin", "is_admin": True}
        )

        # FIX: Securely hash the password using the django API before saving
        # admin_user, created = User.objects.get_or_create(
        #     username="admin",
        #     defaults={"password_hash": make_password("admin"), "is_admin": True}
        # )

        if created:
            self.stdout.write(self.style.SUCCESS("Created admin account (admin:admin)"))
        else:
            self.stdout.write("Admin account already exists.")

        # --- WORKER ACCOUNT ---

        # WARN: FLAW A02:2021 - Cryptographic Failures
        # We are writing raw plain-text strings directly into the password field.
        worker_user, created = User.objects.get_or_create(
            username="worker", defaults={"password_hash": "worker", "is_admin": False}
        )

        # FIX: Securely hash the password using the django API before saving
        # worker_user, created = User.objects.get_or_create(
        #     username="worker",
        #     defaults={"password_hash": make_password("worker"), "is_admin": False}
        # )

        if created:
            self.style.SUCCESS("Created worker account (worker:worker)")
        else:
            self.stdout.write("Worker account already exists.")

        self.stdout.write(self.style.SUCCESS("Seeding complete!"))
