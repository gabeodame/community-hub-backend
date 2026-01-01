from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("posts", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="post",
            name="is_deleted",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="post",
            name="deleted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="comment",
            name="is_deleted",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="comment",
            name="deleted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="Report",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                (
                    "content_type",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="contenttypes.contenttype"),
                ),
                ("object_id", models.PositiveIntegerField()),
                ("reason", models.CharField(choices=[("spam", "Spam"), ("harassment", "Harassment"), ("misinfo", "Misinformation"), ("illegal", "Illegal"), ("other", "Other")], max_length=20)),
                ("details", models.TextField(blank=True, max_length=1000)),
                ("status", models.CharField(choices=[("open", "Open"), ("reviewed", "Reviewed"), ("actioned", "Actioned"), ("dismissed", "Dismissed")], default="open", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "reporter",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reports", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                "indexes": [
                    models.Index(fields=["content_type", "object_id"], name="posts_report_target_idx"),
                    models.Index(fields=["status"], name="posts_report_status_idx"),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="report",
            constraint=models.UniqueConstraint(fields=["reporter", "content_type", "object_id"], name="uniq_reporter_target"),
        ),
    ]
