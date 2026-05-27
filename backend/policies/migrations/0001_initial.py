from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="FirewallRule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("source_ip", models.CharField(max_length=64)),
                ("destination_ip", models.CharField(max_length=64)),
                ("protocol", models.CharField(max_length=16)),
                ("port", models.IntegerField(blank=True, null=True)),
                ("action", models.CharField(choices=[("ALLOW", "Allow"), ("DENY", "Deny")], max_length=16)),
                ("enabled", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["id"]},
        ),
    ]
