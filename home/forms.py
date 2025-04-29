from django import forms
from myprofile.models import ManageTokens, UserLike, ManageDept, ManagePosi, ManageTokensGroup, AccessLog, ManageThankyouWeeks, BefInsUcmsg

class UploadFileForm(forms.Form):
    file = forms.FileField()

class BefInsUcmsgForm(forms.ModelForm):
    class Meta:
        model = BefInsUcmsg
        fields = '__all__'
