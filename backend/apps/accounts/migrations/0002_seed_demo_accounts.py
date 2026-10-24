from django.db import migrations
from django.contrib.auth.hashers import make_password


DEMO_USERS = [
    {
        "username": "citizen_demo",
        "email": "citizen@legalmetro.test",
        "first_name": "Priya",
        "last_name": "Sharma",
        "role": "citizen",
    },
    {
        "username": "officer_demo",
        "email": "officer@legalmetro.test",
        "first_name": "Rajesh",
        "last_name": "Kumar",
        "role": "field_officer",
        "state": "Maharashtra",
    },
    {
        "username": "ruleadmin_demo",
        "email": "ruleadmin@legalmetro.test",
        "first_name": "Sunil",
        "last_name": "Verma",
        "role": "rule_admin",
    },
]


def create_demo_accounts(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    Role = apps.get_model("accounts", "Role")
    RoleAssignment = apps.get_model("accounts", "RoleAssignment")

    for details in DEMO_USERS:
        role_name = details["role"]
        role, _ = Role.objects.get_or_create(name=role_name)
        user, created = User.objects.get_or_create(
            username=details["username"],
            defaults={
                "email": details["email"],
                "first_name": details["first_name"],
                "last_name": details["last_name"],
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            user.password = make_password("demo1234")
            user.save(update_fields=["password"])

        RoleAssignment.objects.get_or_create(
            user=user,
            role=role,
            defaults={
                "state": details.get("state"),
                "organization": None,
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_demo_accounts, migrations.RunPython.noop),
    ]
