
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("goal", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="chapterread",
            options={"ordering": ["-read_at"]},
        ),
        migrations.AlterModelOptions(
            name="conversationinteraction",
            options={"ordering": ["-created_at"]},
        ),
        migrations.AlterModelOptions(
            name="shareactivity",
            options={"ordering": ["-shared_at"]},
        ),
        migrations.AlterModelOptions(
            name="usergoal",
            options={"ordering": ["-week_start", "goal_type"]},
        ),
        migrations.AlterField(
            model_name="chapterread",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="chapters_read",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="conversationinteraction",
            name="interaction_type",
            field=models.CharField(
                choices=[("thumbs_up", "Thumbs Up"), ("thumbs_down", "Thumbs Down")],
                default="thumbs_up",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="conversationinteraction",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="conversation_interactions",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="shareactivity",
            name="share_platform",
            field=models.CharField(
                blank=True,
                choices=[
                    ("whatsapp", "WhatsApp"),
                    ("facebook", "Facebook"),
                    ("twitter", "Twitter"),
                    ("instagram", "Instagram"),
                    ("email", "Email"),
                    ("copy_link", "Copy Link"),
                    ("other", "Other"),
                ],
                max_length=50,
            ),
        ),
        migrations.AlterField(
            model_name="shareactivity",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="share_activities",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="usergoal",
            name="week_start",
            field=models.DateField(),
        ),
    ]
