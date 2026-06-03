
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("checkin", "0005_alter_userweeklycheckin_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="userstreak",
            name="current_weekly_streak",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="userstreak",
            name="has_red_flame",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="userstreak",
            name="longest_weekly_streak",
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="badgetemplate",
            name="badge_type",
            field=models.CharField(
                choices=[
                    ("default", "Default"),
                    ("week_1", "Week 1 — Seed Planted"),
                    ("week_2", "Week 2 — Rooted in Grace"),
                    ("week_3", "Week 3 — New Life Rising"),
                    ("week_4", "Week 4 — Standing in the Light"),
                    ("week_12", "Week 12 — Branches of Influence"),
                    ("week_24", "Week 24 — Flourishing in Faith"),
                    ("week_52", "Week 52 — Fruit of a Faithful Life"),
                ],
                max_length=100,
                unique=True,
            ),
        ),
    ]
