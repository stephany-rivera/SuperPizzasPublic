# Generated by Django 2.2.5 on 2019-11-30 05:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pizzas', '0006_auto_20191129_2256'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ingredientesa',
            name='detalle',
        ),
        migrations.AddField(
            model_name='ingredientesa',
            name='factura',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='pizzas.Factura'),
        ),
        migrations.AddField(
            model_name='ingredientesa',
            name='producto',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='pizzas.Pizza'),
        ),
    ]
