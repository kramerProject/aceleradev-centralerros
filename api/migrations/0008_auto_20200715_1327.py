# Generated by Django 2.2.4 on 2020-07-15 13:27

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_event_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='password',
            field=models.CharField(max_length=500, validators=[django.core.validators.MinLengthValidator(8, 'the password must have at least 8 characters')]),
        ),
    ]
