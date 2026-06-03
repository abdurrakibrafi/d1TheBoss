
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("onboarding", "0011_usergoalpreference"),
    ]

    operations = [
        migrations.AddField(
            model_name="faithgoaloption",
            name="goal_type",
            field=models.CharField(
                choices=[
                    ("conversation", "Confidence Goal"),
                    ("scripture", "Scripture Knowledge"),
                    ("share_faith", "Inspiration Goal"),
                ],
                default="scripture",
                max_length=20,
            ),
        ),
    ]
