# Generated by Django 4.2 on 2024-04-07 22:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vendor', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='vendor',
            old_name='vendor_licence',
            new_name='vendor_license',
        ),
    ]
