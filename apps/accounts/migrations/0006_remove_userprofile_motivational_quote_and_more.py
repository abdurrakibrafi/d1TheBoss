
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0005_alter_otp_purpose"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="userprofile",
            name="motivational_quote",
        ),
        migrations.RemoveField(
            model_name="userprofile",
            name="stripe_customer_id",
        ),
    ]
