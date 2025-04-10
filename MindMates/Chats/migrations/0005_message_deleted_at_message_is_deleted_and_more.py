# Generated by Django 4.2.16 on 2025-04-10 08:29

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("Chats", "0004_alter_message_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="message",
            name="deleted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="message",
            name="is_deleted",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="message",
            name="is_edited",
            field=models.BooleanField(default=False),
        ),
    ]
