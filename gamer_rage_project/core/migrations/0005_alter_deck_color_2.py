# Generated by Django 5.0.1 on 2024-11-19 02:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_card_image_key_alter_deckreaction_emoji'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deck',
            name='color_2',
            field=models.CharField(choices=[('grass', 'Grass'), ('fire', 'Fire'), ('water', 'Water'), ('lightning', 'Lightning'), ('fighting', 'Fighting'), ('psychic', 'Psychic'), ('colorless', 'Colorless'), ('darkness', 'Darkness'), ('metal', 'Metal'), ('dragon', 'Dragon'), ('fairy', 'Fairy')], max_length=30, null=True),
        ),
    ]
