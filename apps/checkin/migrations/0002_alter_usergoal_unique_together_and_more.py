
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("checkin", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="usergoal",
            unique_together={("user", "goal_type")},
        ),
        migrations.AlterField(
            model_name="usergoal",
            name="goal_type",
            field=models.CharField(
                choices=[
                    ("scripture", "Scripture"),
                    ("share_faith", "Share Faith"),
                    ("conversation", "Conversation"),
                ],
                max_length=20,
            ),
        ),
        migrations.RemoveField(
            model_name="usergoal",
            name="date",
        ),
    ]
