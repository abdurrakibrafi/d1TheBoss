
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("onboarding", "0007_alter_biblefamiliarity_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="bibleversionoption",
            name="api_bible_id",
            field=models.CharField(blank=True, max_length=50, null=True, unique=True),
        ),
    ]
