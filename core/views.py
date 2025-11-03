from django.core.paginator import Paginator, EmptyPage
from django.db.models import Q
from django.http import JsonResponse
from django.views import View
from .models import AppUser

ALLOWED_ORDER_FIELDS = {
    "id", "first_name", "last_name", "gender", "customer_id", "phone_number",
    "created", "last_updated", "birthday",
    "address__city", "address__city_code", "address__country",
    "relationship__points", "relationship__last_activity",
}
FILTER_MAP = {
    "id": "id",
    "first_name": "first_name__icontains",
    "last_name": "last_name__icontains",
    "gender": "gender",
    "customer_id": "customer_id",
    "phone_number": "phone_number__icontains",
    "created_from": "created__date__gte",
    "created_to": "created__date__lte",
    "birthday_from": "birthday__gte",
    "birthday_to": "birthday__lte",
    "city": "address__city__icontains",
    "city_code": "address__city_code",
    "country": "address__country__icontains",
    "points_min": "relationship__points__gte",
    "points_max": "relationship__points__lte",
    "last_activity_from": "relationship__last_activity__gte",
    "last_activity_to": "relationship__last_activity__lte",
}


class UserListView(View):
    def get(self, request):
        qs = AppUser.objects.select("address", "relationship")
        q = Q()
        for param, path in FILTER_MAP.items():
            v = request.GET.get(param)
            if v:
                q &= Q(**{path: v})
        if q:
            qs = qs.filter(q)

        order_by = request.GET.get("order_by", "id")
        if order_by.lstrip("-") not in ALLOWED_ORDER_FIELDS:
            order_by = "id"
        qs = qs.order_by(order_by)

        page_size = min(int(request.GET.get("page_size", 50)), 500)
        page = int(request.GET.get("page", 1))

        qs = qs.only(
            "id", "first_name", "last_name", "gender", "customer_id", "phone_number", "birthday", "created", "last_updated",
            "address__city", "address__city_code", "address__country",
            "relationship__points", "relationship__last_activity",
        )
        paginator = Paginator(qs, page_size)
        try:
            page_obj = paginator.page(page)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        results = []
        for u in page_obj.object_list:
            results.append({
                "id": u.id,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "gender": u.gender,
                "customer_id": u.customer_id,
                "phone_number": u.phone_number,
                "birthday": u.birthday.isoformat() if u.birthday else None,
                "created": u.created.isoformat() if u.created else None,
                "last_updated": u.last_updated.isoformat() if u.last_updated else None,
                "address": {
                    "city": u.address.city,
                    "city_code": u.address.city_code,
                    "country": u.address.country,
                },
                "relationship": {
                    "points": u.relationship.points,
                    "last_activity": u.relationship.last_activity.isoformat() if u.relationship.last_activity else None,
                }
            })

        return JsonResponse({
            "count": paginator.count,
            "num_pages": paginator.num_pages,
            "page": page_obj.number,
            "page_size": page_size,
            "order_by": order_by,
            "results": results,
        })
