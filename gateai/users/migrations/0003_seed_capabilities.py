from django.db import migrations

def seed_capabilities(apps, schema_editor):
    AdminCapability = apps.get_model('users', 'AdminCapability')
    capabilities = [
        ('mock.manage', 'Manage mock interviews and related data'),
        ('mock.review', 'Review mock interview results'),
        ('user.support', 'Provide user support and manage tickets'),
        ('analytics.read', 'Read system analytics and reports'),
        ('kernel.readonly', 'Read-only access to kernel state'),
    ]
    for code, description in capabilities:
        AdminCapability.objects.get_or_create(code=code, defaults={'description': description})

class Migration(migrations.Migration):
    dependencies = [
        ('users', '0002_admincapability_user_capabilities'),
    ]

    operations = [
        migrations.RunPython(seed_capabilities),
    ]
