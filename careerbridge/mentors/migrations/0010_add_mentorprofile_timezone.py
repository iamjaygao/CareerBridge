from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('mentors', '0009_add_primary_service_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='mentorprofile',
            name='timezone',
            field=models.CharField(
                default=settings.TIME_ZONE,
                help_text='IANA timezone for availability (e.g., America/New_York)',
                max_length=64
            ),
        ),
    ]
