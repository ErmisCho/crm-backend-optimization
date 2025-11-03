from django.db import models


class AppUser(models.Model):
    gender_choices = (("m", "Male"), ("f", "Female"), ("o", "Other"))

    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    gender = models.CharField(
        max_length=1, choices=gender_choices)
    customer_id = models.CharField(max_length=64)
    phone_number = models.CharField(max_length=32)
    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    birthday = models.DateField(null=True, blank=True)
    address = models.ForeignKey(
        "Address", on_delete=models.PROTECT, related_name="users"
    )

    class Meta:
        indexes = [
            models.Index(fields=["last_name", "first_name"],
                         name="idx_name_combo"),
            models.Index(fields=["customer_id", "created"],
                         name="idx_customer_created"),
        ]
        verbose_name = "App User"
        verbose_name_plural = "App Users"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Address(models.Model):
    street = models.CharField(max_length=128)
    street_number = models.CharField(max_length=16)
    city_code = models.CharField(max_length=16)
    city = models.CharField(max_length=64)
    country = models.CharField(max_length=64)

    class Meta:
        indexes = [
            # City + code often used together in filtering
            models.Index(fields=["city", "city_code"],
                         name="idx_city_citycode")
        ]

    def __str__(self):
        return f"{self.street} {self.street_number}, {self.city}"


class CustomerRelationship(models.Model):
    appuser = models.OneToOneField(
        AppUser, on_delete=models.CASCADE, related_name="relationship"
    )
    points = models.IntegerField(db_index=True)
    created = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(db_index=True)

    class Meta:
        indexes = [
            # Composite: often filter/sort by user + points
            models.Index(fields=["appuser", "points"], name="idx_user_points"),
        ]
        verbose_name = "Customer Relationship"
        verbose_name_plural = "Customer Relationships"

    def __str__(self):
        return f"{self.appuser} - {self.points} pts"
