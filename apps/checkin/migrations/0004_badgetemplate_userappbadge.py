
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("checkin", "0003_delete_usergoal"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="BadgeTemplate",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "badge_type",
                    models.CharField(
                        choices=[
                            ("default", "Default"),
                            ("first_week_checked", "First Week Checked"),
                            ("first_week", "First Week"),
                            ("two_week", "Two Week"),
                            ("one_month", "One Month"),
                            ("three_months", "Three Months"),
                            ("six_months", "Six Months"),
                            ("one_year", "One Year"),
                        ],
                        max_length=100,
                        unique=True,
                    ),
                ),
                ("title", models.CharField(blank=True, max_length=200, null=True)),
                ("description", models.TextField(blank=True, null=True)),
                (
                    "image",
                    models.ImageField(
                        blank=True, null=True, upload_to="checkin/badges/"
                    ),
                ),
                ("order", models.IntegerField(default=0)),
                ("days_required", models.IntegerField(blank=True, null=True)),
            ],
            options={
                "ordering": ["order"],
            },
        ),
        migrations.CreateModel(
            name="UserAppBadge",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("earned_at", models.DateTimeField(auto_now_add=True)),
                (
                    "badge_template",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="checkin.badgetemplate",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="app_badges",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-earned_at"],
                "unique_together": {("user", "badge_template")},
            },
        ),
    ]
