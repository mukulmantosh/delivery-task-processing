from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import TemplateView
from urban_piper.utils import StoreManagerGroupRequired, DeliveryBoyGroupRequired
from django.db import transaction, IntegrityError
from . import forms
from . import models
from . import queue


class IndexView(StoreManagerGroupRequired, LoginRequiredMixin, TemplateView):
    """
    This view returns the index page of the store manager after he is
    successfully logged in.
    """
    template_name = "store/index.html"


class TaskListView(StoreManagerGroupRequired, LoginRequiredMixin, TemplateView):
    """
    This view returns list of all tasks as well as real-time updates on the view.
    """
    template_name = "store/view_task.html"


class StoreView(StoreManagerGroupRequired, LoginRequiredMixin, View):
    """
    This view is used to create new task by a respective store manager.
    """
    template_name = "store/store.html"
    form_class = forms.StoreTaskForm

    def get(self, request):
        form = self.form_class(request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.user, request.POST)
        if form.is_valid():
            form.save()
            return redirect("store:task-list")
        else:
            return render(request, self.template_name, {'form': form})


class StoreTaskDetailView(StoreManagerGroupRequired, LoginRequiredMixin, View):
    """
    This view shows up details of a particular delivery task along-with that
    it shows the delivery status log on a particular order.
    """
    template_name = 'store/store-detail.html'

    def get(self, request, **kwargs):
        delivery_task_model = models.DeliveryTask.objects.filter(id=self.kwargs['pk']).first()
        delivery_status_model = models.DeliveryStatus.objects.filter(delivery_tasks=delivery_task_model)

        return render(request, self.template_name,
                      {'deliverytask': delivery_task_model, 'delivery_status': delivery_status_model})


class CancelStoreOrderView(StoreManagerGroupRequired, LoginRequiredMixin, View):
    """
    This view is used to cancel the delivery task. This is used by the store manager.
    """
    def post(self, request, pk):
        models.DeliveryTask.objects.filter(id=pk).update(last_known_state="CANCELLED")
        return redirect("store:store-detail", pk)


class DeliveryIndex(DeliveryBoyGroupRequired, LoginRequiredMixin, TemplateView):
    """
    This view returns the index page after the delivery boy gets logged in.
    """
    template_name = "store/delivery-index.html"


class DeliveryOrderListView(DeliveryBoyGroupRequired, LoginRequiredMixin, TemplateView):
    """
    This view show the list of new orders placed by the store manager.
    """
    template_name = "store/delivery-order-listing.html"


class DeliveryOrderProcessView(DeliveryBoyGroupRequired, LoginRequiredMixin, View):
    """
    This view is to process order by the delivery boys.
    """
    def post(self, request):
        order_status = request.POST.get('order_status', None)
        if order_status == "ACCEPT":
            # read data from queue.
            data = queue.read_data_from_queue()
            if data is False:
                # No data present in Queue.
                return redirect("store:delivery-order-list")
            else:
                try:
                    delivery_task_obj = models.DeliveryTask.objects.get(id=data["id"])
                    if delivery_task_obj.last_known_state == "CANCELLED":
                        queue.read_data_from_queue(acknowledge=True)
                        messages.error(request, 'This order has already been cancelled ! or deleted !')
                        return redirect("store:delivery-order-list")

                except:
                    queue.read_data_from_queue(acknowledge=True)
                    messages.error(request, 'This order has already been cancelled ! or deleted !')
                    return redirect("store:delivery-order-list")

            try:
                if models.DeliveryLogs.objects.filter(user=request.user, delivery_status="ACCEPTED").count() >= 3:
                    messages.error(request, 'Sorry ! You cannot have more than 3 Accepted Orders !')
                    return redirect("store:delivery-order-list")

                with transaction.atomic():

                    # create new delivery log or update if exists.
                    try:

                        delivery_log_obj = models.DeliveryLogs.objects.get(delivery_task_id=data["id"],
                                                                              user=request.user)
                        delivery_log_obj.delivery_status = "ACCEPTED"
                        delivery_log_obj.save()

                    except models.DeliveryLogs.DoesNotExist:
                        delivery_log_obj = models.DeliveryLogs.objects.create(delivery_task_id=data["id"],
                                                           user=request.user,
                                                           delivery_status="ACCEPTED")

                    models.DeliveryStatus.objects.create(delivery_log=delivery_log_obj, delivery_tasks_id=data["id"],
                                                         delivery_status="ACCEPTED")

                    # update delivery task.
                    delivery_task_obj.last_known_state = "ACCEPTED"
                    delivery_task_obj.save()

            except IntegrityError as err:
                transaction.rollback()

            finally:
                return redirect("store:delivery-order-list")


class DeliveryTaskAcceptedOrderView(DeliveryBoyGroupRequired, LoginRequiredMixin, View):
    """
    This view returns the list of orders which has been accepted by the delivery boy.
    Besides that this view allow delivery boy to process the order (COMPLETED or CANCELLED).
    """
    template_name = 'store/delivery-accepted-order-listing.html'

    def get(self, request):
        result = models.DeliveryLogs.objects.filter(user=request.user, delivery_status="ACCEPTED")
        print(result)
        return render(request, self.template_name, {'result': result})

    def post(self, request):
        order_id = int(request.POST.get('order_id'))
        order_status = request.POST.get('order_status')

        if models.DeliveryTask.objects.filter(id=order_id, last_known_state="CANCELLED").exists():
            queue.read_data_from_queue(acknowledge=True)
            messages.error(request, 'This order has already been cancelled ! or deleted !')
            return redirect("store:delivery-task-accepted-order")

        try:
            data = models.DeliveryLogs.objects.get(user=request.user, id=order_id, delivery_status="ACCEPTED")
        except models.DeliveryLogs.DoesNotExist:
            print("No DeliveryLogs Present !")
            return redirect("store:delivery-task-accepted-order")

        if order_status == "COMPLETED":
            try:
                with transaction.atomic():
                    result = models.DeliveryTask.objects.get(id=data.delivery_task.id)
                    result.last_known_state = "COMPLETED"
                    result.save()

                    delivery_log_obj = models.DeliveryLogs.objects.get(delivery_task=result, user=request.user)
                    delivery_log_obj.delivery_status = "COMPLETED"
                    delivery_log_obj.save()

                    models.DeliveryStatus.objects.create(delivery_log=delivery_log_obj, delivery_tasks=result,
                                                         delivery_status="COMPLETED")

                return redirect("store:delivery-task-accepted-order")
            except IntegrityError as err:
                transaction.rollback()
                raise Exception("Something went wrong.")

        elif order_status == "DECLINED":
            try:
                with transaction.atomic():
                    result = models.DeliveryTask.objects.get(id=data.delivery_task.id)
                    result.last_known_state = "NEW"
                    result.save()

                    delivery_log_obj = models.DeliveryLogs.objects.get(delivery_task=result, user=request.user)
                    delivery_log_obj.delivery_status = "DECLINED"
                    delivery_log_obj.save()

                    models.DeliveryStatus.objects.create(delivery_log=delivery_log_obj, delivery_tasks=result,
                                                         delivery_status="DECLINED")

                return redirect("store:delivery-task-accepted-order")
            except IntegrityError as err:
                transaction.rollback()
                raise Exception("Something went wrong.")

        else:
            return redirect("store:delivery-task-accepted-order")
