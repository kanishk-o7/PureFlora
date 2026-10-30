from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.SlugField(max_length=80, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=160)),
                ("category", models.CharField(db_index=True, max_length=80)),
                ("price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("unit", models.CharField(max_length=80)),
                ("stock", models.PositiveIntegerField(default=0)),
                ("grower", models.CharField(max_length=160)),
                ("tag", models.CharField(blank=True, max_length=80)),
                ("color", models.CharField(blank=True, max_length=40)),
                ("image", models.URLField(blank=True, max_length=1000)),
                ("description", models.TextField(blank=True)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ("name",)},
        ),
    ]
