from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from core.models import ProductStore, Pedido

def is_staff(user):
    return user.is_staff

@login_required
@user_passes_test(is_staff)
def dashboard_home(request):
    productos = ProductStore.objects.all()
    pedidos = Pedido.objects.all()
    return render(request, 'dashboard/dashboard_home.html', {
        'productos': productos,
        'pedidos': pedidos,
    })