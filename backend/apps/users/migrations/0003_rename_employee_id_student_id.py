from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_alter_user_managers'),
    ]

    operations = [
        migrations.RenameField(
            model_name='user',
            old_name='employee_id',
            new_name='student_id',
        ),
    ]
