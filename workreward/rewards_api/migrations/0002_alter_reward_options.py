# Generated by Django 5.1.2 on 2024-12-24 19:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("rewards_api", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="reward",
            options={"ordering": ["-time_create"]},
        ),
    ]
