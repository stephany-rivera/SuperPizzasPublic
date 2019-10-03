# Generated by Django 2.2.5 on 2019-10-03 03:24

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('ingredientes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Producto',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=50)),
                ('valor', models.BigIntegerField()),
                ('ingrediente', models.ManyToManyField(to='ingredientes.Ingrediente')),
            ],
        ),
    ]
