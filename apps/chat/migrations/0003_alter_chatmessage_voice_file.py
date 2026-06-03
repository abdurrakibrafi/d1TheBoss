
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0002_chatmessage_has_voice_chatmessage_voice_file_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="chatmessage",
            name="voice_file",
            field=models.FileField(
                blank=True, null=True, upload_to="chat/voice_messages/"
            ),
        ),
    ]
