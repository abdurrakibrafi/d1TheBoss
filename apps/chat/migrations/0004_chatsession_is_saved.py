
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0003_alter_chatmessage_voice_file"),
    ]

    operations = [
        migrations.AddField(
            model_name="chatsession",
            name="is_saved",
            field=models.BooleanField(default=False),
        ),
    ]
