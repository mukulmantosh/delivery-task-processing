from django import forms
from . import models
from urban_piper import utils


class StoreTaskForm(forms.ModelForm):
    title = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), required=True)
    priority = forms.ChoiceField(choices=utils.TASK_PRIORITY, widget=forms.Select(attrs={'class': 'form-control'}),
                                 required=True)

    class Meta:
        model = models.DeliveryTask
        fields = ["user_store", "title", "priority"]

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(StoreTaskForm, self).__init__(*args, **kwargs)
        self.fields['user_store'] = forms.ModelChoiceField(queryset=models.UserStore.objects.filter(user=self.user),
                                                           widget=forms.Select(attrs={'class': 'form-control'}))
