from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('adminpanel', '0005_merge_20251228_2300'),
    ]

    operations = [
        migrations.AddField(
            model_name='contentitem',
            name='summary',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='contentitem',
            name='body',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='contentitem',
            name='cover_image_url',
            field=models.URLField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='supportticket',
            name='staff_notes',
            field=models.TextField(blank=True),
        ),
    ]
