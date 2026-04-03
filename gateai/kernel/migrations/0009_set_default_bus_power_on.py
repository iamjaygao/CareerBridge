from django.db import migrations

BUS_NAMES = [
    "KERNEL_CORE_BUS",
    "PUBLIC_WEB_BUS",
    "ADMIN_BUS",
    "AI_BUS",
    "PEER_MOCK_BUS",
    "MENTOR_BUS",
    "PAYMENT_BUS",
    "SEARCH_BUS",
]


def set_all_buses_on(apps, schema_editor):
    BusPowerState = apps.get_model("kernel", "BusPowerState")
    for bus_name in BUS_NAMES:
        BusPowerState.objects.update_or_create(
            bus_name=bus_name,
            defaults={"state": "ON"},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("kernel", "0008_add_buspower_state"),
    ]

    operations = [
        migrations.RunPython(set_all_buses_on, migrations.RunPython.noop),
    ]
