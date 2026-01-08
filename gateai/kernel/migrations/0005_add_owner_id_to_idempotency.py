# Generated migration to add owner_id to KernelIdempotencyRecord
# Required for semantic collision detection (event_type, context_hash, owner_id)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kernel', '0004_add_arbitration_record'),
    ]

    operations = [
        migrations.AddField(
            model_name='kernelidempotencyrecord',
            name='owner_id',
            field=models.CharField(blank=True, help_text='Owner ID for semantic collision detection', max_length=128),
        ),
    ]

