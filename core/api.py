from django_filters import rest_framework as filters
from rest_framework import generics
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .models import AppUser
from .serializers import AppUserSerializer


class AppUserFilter(filters.FilterSet):
    # Date filters
    created_from = filters.DateFilter(
        field_name="created", lookup_expr="date__gte")
    created_to = filters.DateFilter(
        field_name="created", lookup_expr="date__lte")
    birthday_from = filters.DateFilter(
        field_name="birthday", lookup_expr="gte")
    birthday_to = filters.DateFilter(field_name="birthday", lookup_expr="lte")

    # Numeric ranges
    points_min = filters.NumberFilter(
        field_name="relationship__points", lookup_expr="gte")
    points_max = filters.NumberFilter(
        field_name="relationship__points", lookup_expr="lte")

    # DateTime ranges
    last_activity_from = filters.IsoDateTimeFilter(
        field_name="relationship__last_activity", lookup_expr="gte")
    last_activity_to = filters.IsoDateTimeFilter(
        field_name="relationship__last_activity", lookup_expr="lte")

    class Meta:
        model = AppUser
        fields = {
            "id": ["exact"],
            "first_name": ["icontains"],
            "last_name": ["icontains"],
            "gender": ["exact"],
            "customer_id": ["exact"],
            "phone_number": ["icontains"],
            "address__city": ["icontains"],
            "address__city_code": ["exact"],
            "address__country": ["icontains"],
        }


@extend_schema(
    parameters=[
        OpenApiParameter(name="ordering", description="Sort by any allowed field. Prefix with '-' for desc.",
                         required=False, type=str),
    ]
)
class AppUserListView(generics.ListAPIView):
    """List users with joined address & relationship, filter/sort/paginate."""
    permission_classes = [AllowAny]
    serializer_class = AppUserSerializer
    filterset_class = AppUserFilter
    ordering_fields = (
        "id", "first_name", "last_name", "gender", "customer_id", "phone_number",
        "created", "last_updated", "birthday",
        "address__city", "address__city_code", "address__country",
        "relationship__points", "relationship__last_activity",
    )
    ordering = ("id",)

    def get_queryset(self):
        return (
            AppUser.objects
            .select_related("address", "relationship")
            .only(
                "id", "first_name", "last_name", "gender", "customer_id", "phone_number",
                "birthday", "created", "last_updated",
                "address__city", "address__city_code", "address__country",
                "relationship__points", "relationship__last_activity",
            )
        )
