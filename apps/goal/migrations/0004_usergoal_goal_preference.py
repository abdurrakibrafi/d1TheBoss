
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("goal", "0003_alter_usergoal_goal_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="usergoal",
            name="goal_preference",
            field=models.CharField(
                blank=True,
                choices=[
                    ("scripture", "Scripture Knowledge"),
                    ("share_faith", "Inspiration Goal"),
                    ("conversation", "Confidence Goal"),
                ],
                default="scripture",
                max_length=20,
                null=True,
            ),
        ),
    ]
