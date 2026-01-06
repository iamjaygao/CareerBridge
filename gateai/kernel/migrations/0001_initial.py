from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="KernelAuditLog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "event_id",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("event_type", models.CharField(max_length=128)),
                ("decision_id", models.CharField(max_length=128)),
                ("idempotency_key", models.CharField(db_index=True, max_length=128)),
                ("context_hash", models.CharField(max_length=128)),
                ("schema_version", models.CharField(default="1.0", max_length=10)),
                ("payload", models.JSONField(default=dict)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("EMITTED", "Emitted"),
                            ("HANDLED", "Handled"),
                            ("FAILED", "Failed"),
                            ("REJECTED", "Rejected"),
                        ],
                        db_index=True,
                        default="EMITTED",
                        max_length=16,
                    ),
                ),
                ("failure_reason", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="kernelauditlog",
            index=models.Index(
                fields=["event_type", "created_at"],
                name="kernel_kern_event_t_535ea0_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="kernelauditlog",
            index=models.Index(
                fields=["decision_id", "created_at"],
                name="kernel_kern_decisio_03dd8e_idx",
            ),
        ),
    ]

