
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("checkin", "0004_badgetemplate_userappbadge"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="userweeklycheckin",
            options={"ordering": ["week_number"]},
        ),
        migrations.RenameField(
            model_name="badgetemplate",
            old_name="days_required",
            new_name="weeks_required",
        ),
        migrations.AddField(
            model_name="userweeklycheckin",
            name="status",
            field=models.CharField(
                choices=[
                    ("available", "Available"),
                    ("completed", "Completed"),
                    ("missed", "Missed"),
                ],
                default="available",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="userweeklycheckin",
            name="week_end",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="userweeklycheckin",
            name="week_start",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="userbadge",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="badges",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="userweeklycheckin",
            name="is_available",
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name="userweeklycheckin",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="weekly_checkins",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterUniqueTogether(
            name="userweeklycheckin",
            unique_together={("user", "week_number")},
        ),
    ]
