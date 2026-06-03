
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "onboarding",
            "0004_rename_bible_familiarity_biblefamiliarity_bible_familiarity_option",
        ),
    ]

    operations = [
        migrations.RenameField(
            model_name="bibleversion",
            old_name="bible_version",
            new_name="bible_version_option",
        ),
    ]
