from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'description', 'image', 'stock']
        # Adding some Tailwind classes to the form inputs for a clean look
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}),
            'price': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded'}),
            'description': forms.Textarea(attrs={'class': 'w-full p-2 border rounded', 'rows': 4}),
            'image': forms.FileInput(attrs={'class': 'w-full p-2 border rounded'}),
            'stock': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded'}),
        }