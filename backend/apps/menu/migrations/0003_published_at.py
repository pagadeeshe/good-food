from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0002_meal_types'),
    ]

    operations = [
        migrations.AddField(
            model_name='dailymenu',
            name='published_at',
            field=models.DateTimeField(blank=True, db_index=True, null=True),
        ),
    ]
