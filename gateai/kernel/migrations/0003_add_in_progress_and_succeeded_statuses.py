# Generated migration for KernelIdempotencyRecord status updates
# Adds STATUS_IN_PROGRESS and STATUS_SUCCEEDED to support proper idempotency semantics

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kernel', '0002_kernelidempotencyrecord_and_more'),
    ]

    operations = [
        # Update status field to include new choices and change default to IN_PROGRESS
        migrations.AlterField(
            model_name='kernelidempotencyrecord',
            name='status',
            field=models.CharField(
                choices=[
                    ('IN_PROGRESS', 'In Progress'),
                    ('SUCCEEDED', 'Succeeded'),
                    ('PROCESSED', 'Processed'),  # Legacy
                    ('REJECTED', 'Rejected'),
                    ('FAILED', 'Failed'),
                ],
                db_index=True,
                default='IN_PROGRESS',
                max_length=16,
            ),
        ),
        # Make event_type, decision_id, and context_hash blank=True
        # to support partial initialization during claim
        migrations.AlterField(
            model_name='kernelidempotencyrecord',
            name='event_type',
            field=models.CharField(blank=True, db_index=True, max_length=128),
        ),
        migrations.AlterField(
            model_name='kernelidempotencyrecord',
            name='decision_id',
            field=models.CharField(blank=True, db_index=True, max_length=128),
        ),
        migrations.AlterField(
            model_name='kernelidempotencyrecord',
            name='context_hash',
            field=models.CharField(blank=True, max_length=64),
        ),
    ]

