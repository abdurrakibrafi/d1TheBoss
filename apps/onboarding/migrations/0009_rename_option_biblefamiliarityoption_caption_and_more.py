
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("onboarding", "0008_bibleversionoption_api_bible_id"),
    ]

    operations = [
        migrations.RenameField(
            model_name="biblefamiliarityoption",
            old_name="option",
            new_name="caption",
        ),
        migrations.RenameField(
            model_name="tonepreferenceoption",
            old_name="option_subtitle",
            new_name="description",
        ),
        migrations.RenameField(
            model_name="tonepreferenceoption",
            old_name="option_title",
            new_name="name",
        ),
        migrations.AddField(
            model_name="biblefamiliarityoption",
            name="is_selected",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="biblefamiliarityoption",
            name="label",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="biblefamiliarityoption",
            name="name",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name="biblefamiliarityoption",
            name="text1",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name="biblefamiliarityoption",
            name="text2",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name="biblefamiliarityoption",
            name="title",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name="bibleversionoption",
            name="is_selected",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="denominationoption",
            name="is_selected",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="faithgoaloption",
            name="is_selected",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="faithgoalquestion",
            name="is_selected",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="journeyreasonoption",
            name="is_selected",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="tonepreferenceoption",
            name="icon",
            field=models.ImageField(
                blank=True, null=True, upload_to="onboarding/tone_preference_icons/"
            ),
        ),
        migrations.AddField(
            model_name="tonepreferenceoption",
            name="is_selected",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="tonepreferenceoption",
            name="quote",
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name="tonepreferenceoption",
            name="title",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
