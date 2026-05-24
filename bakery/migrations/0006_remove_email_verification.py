from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("bakery", "0005_alter_activitylog_action_emailverification"),
    ]

    operations = [
        migrations.DeleteModel(
            name="EmailVerification",
        ),
        migrations.AlterField(
            model_name="activitylog",
            name="action",
            field=models.CharField(
                choices=[
                    ("login", "Login"),
                    ("logout", "Logout"),
                    ("create", "Create"),
                    ("update", "Update"),
                    ("delete", "Delete"),
                    ("archive", "Archive"),
                    ("stock", "Stock"),
                    ("sale", "Sale"),
                    ("void", "Void"),
                    ("backup", "Backup"),
                    ("restore", "Restore"),
                    ("password", "Password"),
                ],
                max_length=20,
            ),
        ),
    ]
