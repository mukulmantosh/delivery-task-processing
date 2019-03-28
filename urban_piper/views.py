from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import generic, View


class IndexView(View):
    def get(self, request):
        return HttpResponse("<h1>Welcome</h1>")

class LoginView(generic.FormView):
    form_class = AuthenticationForm
    success_url = reverse_lazy("store:index")
    template_name = "base/login.html"

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:

            return redirect("store:index")
        else:
            return render(request, self.template_name, {'form': self.form_class})

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(self.request, **self.get_form_kwargs())

    def form_valid(self, form):
        login(self.request, form.get_user())
        return super().form_valid(form)



class LogoutView(generic.RedirectView):
    url = reverse_lazy("login")

    def get(self, request, *args, **kwargs):
        logout(request)
        return super().get(request, *args, **kwargs)