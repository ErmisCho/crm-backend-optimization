from rest_framework import serializers
from .models import AppUser, Address, CustomerRelationship


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ("city", "city_code", "country")


class RelationshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerRelationship
        fields = ("points", "last_activity")


class AppUserSerializer(serializers.ModelSerializer):
    address = AddressSerializer(read_only=True)
    relationship = RelationshipSerializer(read_only=True)

    class Meta:
        model = AppUser
        fields = (
            "id", "first_name", "last_name", "gender", "customer_id",
            "phone_number", "birthday", "created", "last_updated",
            "address", "relationship",
        )
