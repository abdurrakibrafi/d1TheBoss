
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("checkin", "0002_alter_usergoal_unique_together_and_more"),
    ]

    operations = [
        migrations.DeleteModel(
            name="UserGoal",
        ),
    ]
