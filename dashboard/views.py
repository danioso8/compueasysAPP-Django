from django.contrib.auth.decorators import login_required, permission_required
from core.models import ProductStore, Pedido, SimpleUser
from dashboard.models import register_superuser
from django.shortcuts import get_object_or_404, redirect, render



from django.views.decorators.csrf import csrf_exempt

@login_required
@csrf_exempt  # Solo si tienes problemas con el token CSRF en el modal
def dashboard_home(request):
    productos = ProductStore.objects.all()
    usuarios_simple = SimpleUser.objects.all()
    usuarios_super = register_superuser.objects.all()
    pedidos = Pedido.objects.all()
    # Validación de admin aquí...

    # Procesar edición de usuario desde el modal
    if request.method == 'POST' and request.POST.get('user_id'):
        user_id = request.POST.get('user_id')
        username = request.POST.get('username')
        email = request.POST.get('email')
        usuario = User.objects.get(id=user_id)
        usuario.username = username
        usuario.email = email
        usuario.save()
        return redirect('dashboard_home')  # Recarga el dashboard

    return render(request, 'dashboard/dashboard_home.html', {
        'productos': productos,
        'usuarios': usuarios_simple,
        'usuarios_super': usuarios_super,
        'pedidos': pedidos,
    })


def dar_permiso_staff(request, user_id):
    usuario = get_object_or_404(User, id=user_id)
    usuario.is_staff = True
    usuario.save()
    return redirect('dashboard_home')

def eliminar_usuario(request, user_id):
    usuario = get_object_or_404(User, id=user_id)
    usuario.delete()
    return redirect('dashboard_home')

def editar_usuario(request, user_id):
    usuario = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        usuario.username = request.POST.get('username')
        usuario.email = request.POST.get('email')
        usuario.save()
        return redirect('dashboard_home')
    return render(request, 'dashboard/editar_usuario.html', {'usuario': usuario})    