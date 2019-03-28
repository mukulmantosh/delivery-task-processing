from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

TASK_PRIORITY = (
    ('HIGH', 'HIGH'),
    ('MEDIUM', 'MEDIUM'),
    ('LOW', 'LOW')
)

DELIVERY_STATES = (
    ('ACCEPTED', 'ACCEPTED'),
    ('COMPLETED', 'COMPLETED'),
    ('DECLINED', 'DECLINED'),
    ('CANCELLED', 'CANCELLED')
)


class StoreManagerGroupRequired(object):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_anonymous is True:
            return redirect("/")
        else:
            if request.user.groups.first().name != "STORE MANAGER":
                if request.user.groups.first().name != "DELIVERY BOY":
                    raise PermissionDenied
                else:
                    return redirect("store:delivery-index")

        return super(StoreManagerGroupRequired, self).dispatch(request, *args, **kwargs)


class DeliveryBoyGroupRequired(object):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_anonymous is True:
            return redirect("/")
        else:
            if request.user.groups.first().name != "DELIVERY BOY":
                if request.user.groups.first().name != "STORE MANAGER":
                    raise PermissionDenied
                else:
                    return redirect("store:index")
        return super(DeliveryBoyGroupRequired, self).dispatch(request, *args, **kwargs)
