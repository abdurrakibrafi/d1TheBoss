
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("goal", "0004_usergoal_goal_preference"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="usergoal",
            name="goal_preference",
        ),
    ]
