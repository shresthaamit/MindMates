# Generated by Django 4.2.16 on 2025-04-17 14:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Community",
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
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "image",
                    models.ImageField(
                        blank=True, null=True, upload_to="community_image"
                    ),
                ),
                (
                    "creaters",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="create_communities",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "members",
                    models.ManyToManyField(
                        related_name="communities", to=settings.AUTH_USER_MODEL
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CommunityMessage",
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
                ("content", models.TextField()),
                (
                    "file",
                    models.FileField(
                        blank=True, null=True, upload_to="community_files/"
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("is_edited", models.BooleanField(default=False)),
                ("is_deleted", models.BooleanField(default=False)),
                (
                    "community",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="messages",
                        to="Communities.community",
                    ),
                ),
                (
                    "sender",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
