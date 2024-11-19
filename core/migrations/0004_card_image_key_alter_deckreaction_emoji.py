# Generated by Django 5.0.1 on 2024-11-18 17:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_deckreaction_deckvote_delete_reaction_delete_vote'),
    ]

    operations = [
        migrations.AddField(
            model_name='card',
            name='image_key',
            field=models.CharField(default='test', max_length=200),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='deckreaction',
            name='emoji',
            field=models.CharField(choices=[('⚡', 'Lightning'), ('🔥', 'Fire'), ('🌿', 'Leaf'), ('💧', 'Water'), ('⭐', 'Star'), ('✨', 'Sparkles'), ('💪', 'Strong'), ('🎯', 'Target'), ('❤️', 'Heart'), ('💔', 'Broken Heart'), ('🎲', 'Dice'), ('✅', 'Check Mark'), ('❌', 'Cross Mark'), ('🗑️', 'Trash'), ('👁️', 'Eye'), ('💫', 'Dizzy'), ('🛡️', 'Shield'), ('⚠️', 'Warning')], max_length=5),
        ),
    ]