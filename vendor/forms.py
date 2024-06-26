from django import forms

from accounts.validators import allow_only_image_validators
from vendor.models import Vendor, OpeningHour


class VendorForm(forms.ModelForm):
    vendor_license = forms.FileField(widget=forms.FileInput(attrs={'class': 'btn btn-info'}), validators=[allow_only_image_validators])   # in here widget
    # make css runable to forms in browser

    class Meta:
        model = Vendor
        fields = [
            'vendor_name', 'vendor_license',
        ]


class OpeningHourForm(forms.ModelForm):
    class Meta:
        model = OpeningHour
        fields = ['day', 'from_hour', 'to_hour', 'is_closed']
