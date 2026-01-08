# Generated migration for KernelArbitrationRecord
# Adds atomic arbitration gate for deterministic winner selection

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kernel', '0003_add_in_progress_and_succeeded_statuses'),
    ]

    operations = [
        migrations.CreateModel(
            name='KernelArbitrationRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('resource_id', models.CharField(db_index=True, help_text='Resource ID from sys_claim', max_length=255)),
                ('bucket_start', models.DateTimeField(db_index=True, help_text='Start of 2-second arbitration bucket')),
                ('winner_hash', models.CharField(blank=True, default='', help_text='SHA256 hash of winner', max_length=64)),
                ('winner_owner_id', models.CharField(blank=True, default='', help_text='Owner ID of winner', max_length=128)),
                ('winner_context_hash', models.CharField(blank=True, default='', help_text='Context hash of winner', max_length=128)),
                ('decided_at', models.DateTimeField(blank=True, help_text='When winner was decided', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='kernelarbitrationrecord',
            constraint=models.UniqueConstraint(fields=('resource_id', 'bucket_start'), name='uniq_arb_resource_bucket'),
        ),
        migrations.AddIndex(
            model_name='kernelarbitrationrecord',
            index=models.Index(fields=['resource_id', 'bucket_start'], name='kernel_kern_resourc_idx'),
        ),
        migrations.AddIndex(
            model_name='kernelarbitrationrecord',
            index=models.Index(fields=['decided_at'], name='kernel_kern_decided_idx'),
        ),
    ]

