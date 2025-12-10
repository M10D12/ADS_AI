# Generated migration - Fix Filme fields (simplified)

from django.db import migrations, models
import django.core.validators
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_usuario_timestamps'),
    ]

    operations = [
        # Add fields to Filme that don't exist
        migrations.AddField(
            model_name='filme',
            name='ano_lancamento',
            field=models.IntegerField(
                blank=True,
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(1800),
                    django.core.validators.MaxValueValidator(2100),
                ],
                help_text='Ano de lançamento do filme'
            ),
        ),
        migrations.AddField(
            model_name='filme',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True,
                default=timezone.now,
                help_text='Data e hora de adição ao catálogo'
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='filme',
            name='updated_at',
            field=models.DateTimeField(
                auto_now=True,
                help_text='Data e hora da última atualização'
            ),
        ),
        # Add fields to AtividadeUsuario
        migrations.AddField(
            model_name='atividadeusuario',
            name='data_visualizacao',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='Data e hora em que o filme foi marcado como visto'
            ),
        ),
        migrations.AddField(
            model_name='atividadeusuario',
            name='data_adicao_favoritos',
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text='Data e hora em que foi adicionado aos favoritos'
            ),
        ),
        migrations.AddField(
            model_name='atividadeusuario',
            name='created_at',
            field=models.DateTimeField(
                auto_now_add=True,
                default=timezone.now,
                help_text='Data e hora de criação do registo de atividade'
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='atividadeusuario',
            name='updated_at',
            field=models.DateTimeField(
                auto_now=True,
                help_text='Data e hora da última atualização'
            ),
        ),
    ]
