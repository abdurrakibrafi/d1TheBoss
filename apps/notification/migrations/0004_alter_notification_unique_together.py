
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("notification", "0003_rename_is_sent_notification_sent_at"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="notification",
            unique_together=set(),
        ),
    ]
