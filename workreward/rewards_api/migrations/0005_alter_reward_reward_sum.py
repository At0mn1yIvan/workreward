# Generated by Django 5.1.2 on 2024-12-18 16:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("rewards_api", "0004_alter_reward_reward_sum"),
    ]

    operations = [
        migrations.AlterField(
            model_name="reward",
            name="reward_sum",
            field=models.DecimalField(decimal_places=2, max_digits=7),
        ),
    ]
