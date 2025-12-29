from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('adminpanel', '0002_support_tickets'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ContentItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('content_type', models.CharField(choices=[('blog', 'Blog'), ('resource', 'Resource'), ('guide', 'Guide')], max_length=20)),
                ('status', models.CharField(choices=[('published', 'Published'), ('draft', 'Draft'), ('archived', 'Archived')], default='draft', max_length=20)),
                ('views', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='content_items', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='contentitem',
            index=models.Index(fields=['content_type', 'status'], name='adminpanel_content_type_status_idx'),
        ),
        migrations.AddIndex(
            model_name='contentitem',
            index=models.Index(fields=['status', 'created_at'], name='adminpanel_status_created_idx'),
        ),
    ]
