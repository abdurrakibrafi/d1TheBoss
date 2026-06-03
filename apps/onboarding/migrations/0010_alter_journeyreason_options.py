
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("onboarding", "0009_rename_option_biblefamiliarityoption_caption_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="journeyreason",
            options={},
        ),
    ]
