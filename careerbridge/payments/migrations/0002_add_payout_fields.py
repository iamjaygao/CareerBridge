from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymentsettings',
            name='payout_hold_days',
            field=models.PositiveSmallIntegerField(default=2, help_text='Hold period (days) after completion before payout is eligible'),
        ),
        migrations.AddField(
            model_name='paymentsettings',
            name='payout_requires_admin_approval',
            field=models.BooleanField(default=False, help_text='Require admin approval before releasing payouts'),
        ),
        migrations.AddField(
            model_name='payment',
            name='payout_available_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='payout_failure_reason',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='payout_paid_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='payout_status',
            field=models.CharField(choices=[('not_eligible', 'Not Eligible'), ('pending', 'Pending Hold/Approval'), ('ready', 'Ready to Pay Out'), ('paid', 'Paid Out'), ('failed', 'Payout Failed'), ('on_hold', 'On Hold')], default='not_eligible', max_length=20),
        ),
        migrations.AddField(
            model_name='payment',
            name='payout_transfer_id',
            field=models.CharField(blank=True, max_length=120),
        ),
    ]
