# Generated migration - Add created_at and updated_at to Usuario

from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_atividadeusuario_review'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='usuario',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='usuario',
            name='email',
            field=models.EmailField(max_length=512, unique=True),
        ),
    ]
