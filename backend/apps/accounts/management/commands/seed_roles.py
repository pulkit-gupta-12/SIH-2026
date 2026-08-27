"""
Management command: seed_roles
Creates the 7 predefined roles and one test superuser per role.
"""
from django.core.management.base import BaseCommand
from apps.accounts.models import User, Role, RoleAssignment


ROLES = [
    "citizen",
    "field_officer",
    "state_controller",
    "national_admin",
    "business",
    "ecommerce_partner",
    "rule_admin",
]

# Test user details per role
TEST_USERS = {
    "citizen": {
        "username": "citizen_demo",
        "email": "citizen@legalmetro.test",
        "first_name": "Priya",
        "last_name": "Sharma",
    },
    "field_officer": {
        "username": "officer_demo",
        "email": "officer@legalmetro.test",
        "first_name": "Rajesh",
        "last_name": "Kumar",
        "state": "Maharashtra",
    },
    "state_controller": {
        "username": "controller_demo",
        "email": "controller@legalmetro.test",
        "first_name": "Anita",
        "last_name": "Desai",
        "state": "Maharashtra",
    },
    "national_admin": {
        "username": "admin_demo",
        "email": "admin@legalmetro.test",
        "first_name": "Vikram",
        "last_name": "Singh",
    },
    "business": {
        "username": "business_demo",
        "email": "business@legalmetro.test",
        "first_name": "Arun",
        "last_name": "Patel",
        "organization": "Patel Foods Pvt. Ltd.",
    },
    "ecommerce_partner": {
        "username": "ecommerce_demo",
        "email": "ecommerce@legalmetro.test",
        "first_name": "Meera",
        "last_name": "Joshi",
        "organization": "ShopEasy India",
    },
    "rule_admin": {
        "username": "ruleadmin_demo",
        "email": "ruleadmin@legalmetro.test",
        "first_name": "Sunil",
        "last_name": "Verma",
    },
}

DEFAULT_PASSWORD = "demo1234"


class Command(BaseCommand):
    help = "Seed the 7 predefined roles and create one demo superuser per role."

    def handle(self, *args, **options):
        # Create roles
        for role_name in ROLES:
            role, created = Role.objects.get_or_create(name=role_name)
            status = "Created" if created else "Already exists"
            self.stdout.write(f"  Role '{role_name}': {status}")

        # Create test users
        for role_name, user_info in TEST_USERS.items():
            state = user_info.pop("state", None)
            organization = user_info.pop("organization", None)
            username = user_info["username"]

            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": user_info["email"],
                    "first_name": user_info["first_name"],
                    "last_name": user_info["last_name"],
                    "is_staff": True,
                    "is_superuser": True,
                },
            )

            if created:
                user.set_password(DEFAULT_PASSWORD)
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f"  Created user '{username}' (password: {DEFAULT_PASSWORD})")
                )
            else:
                self.stdout.write(f"  User '{username}' already exists")

            # Assign role
            role = Role.objects.get(name=role_name)
            assignment, created = RoleAssignment.objects.get_or_create(
                user=user,
                role=role,
                defaults={"state": state, "organization": organization},
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"    Assigned role '{role_name}' to '{username}'")
                )

        self.stdout.write(self.style.SUCCESS("\nRole seeding complete!"))
