
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_remove_user_user_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="otp",
            name="otp",
            field=models.CharField(max_length=4),
        ),
    ]
