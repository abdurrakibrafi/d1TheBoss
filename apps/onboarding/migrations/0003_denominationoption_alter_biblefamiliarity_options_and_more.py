
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("onboarding", "0002_alter_biblefamiliarityoption_options_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DenominationOption",
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
                ("name", models.CharField(blank=True, max_length=200, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name_plural": "03. Denomination Options",
            },
        ),
        migrations.AlterModelOptions(
            name="biblefamiliarity",
            options={"verbose_name_plural": "11. Bible Familiarity"},
        ),
        migrations.AlterModelOptions(
            name="biblefamiliarityoption",
            options={"verbose_name_plural": "10. Bible Familiarity Options"},
        ),
        migrations.AlterModelOptions(
            name="bibleversion",
            options={"verbose_name_plural": "13. Bible Versions"},
        ),
        migrations.AlterModelOptions(
            name="bibleversionoption",
            options={"verbose_name_plural": "12. Bible Version Options"},
        ),
        migrations.AlterModelOptions(
            name="denomination",
            options={"verbose_name_plural": "04. Denominations"},
        ),
        migrations.AlterModelOptions(
            name="faithgoal",
            options={"verbose_name_plural": "07. Faith Goals"},
        ),
        migrations.AlterModelOptions(
            name="faithgoaloption",
            options={"verbose_name_plural": "06. Faith Goal Options"},
        ),
        migrations.AlterModelOptions(
            name="faithgoalquestion",
            options={"verbose_name_plural": "05. Faith Goal Questions"},
        ),
        migrations.AlterModelOptions(
            name="tonepreference",
            options={"verbose_name_plural": "09. Tone Preferences"},
        ),
        migrations.AlterModelOptions(
            name="tonepreferenceoption",
            options={"verbose_name_plural": "08. Tone Preference Options"},
        ),
        migrations.RemoveField(
            model_name="denomination",
            name="is_active",
        ),
        migrations.RemoveField(
            model_name="denomination",
            name="is_parent",
        ),
        migrations.RemoveField(
            model_name="denomination",
            name="parent",
        ),
        migrations.AddField(
            model_name="biblefamiliarity",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="bibleversion",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="denomination",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="faithgoal",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="journeyreason",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="tonepreference",
            name="user",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="denomination",
            name="denomination_option",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="onboarding.denominationoption",
            ),
        ),
    ]
