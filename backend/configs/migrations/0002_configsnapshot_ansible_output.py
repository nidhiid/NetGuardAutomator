from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("configs", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="configsnapshot",
            name="ansible_stdout",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="configsnapshot",
            name="ansible_stderr",
            field=models.TextField(blank=True),
        ),
    ]
