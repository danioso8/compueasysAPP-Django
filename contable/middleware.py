from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.urls import reverse
from .models import ContableUser


class ContableAuthMiddleware(MiddlewareMixin):
    """
    Middleware para manejar autenticación de usuarios de contable
    usando sesión personalizada (sin django.contrib.auth)
    """
    
    def process_request(self, request):
        # Agregar atributo contable_user al request
        user_id = request.session.get('contable_user_id')
        
        if user_id:
            try:
                request.contable_user = ContableUser.objects.get(id=user_id, is_active=True)
            except ContableUser.DoesNotExist:
                request.contable_user = None
                # Limpiar sesión inválida
                request.session.pop('contable_user_id', None)
                request.session.pop('contable_user_email', None)
                request.session.pop('contable_user_name', None)
        else:
            request.contable_user = None
        
        return None


def contable_login_required(view_func):
    """
    Decorador personalizado para requerir autenticación en vistas de contable
    """
    def wrapped_view(request, *args, **kwargs):
        if not hasattr(request, 'contable_user') or request.contable_user is None:
            from django.contrib import messages
            messages.warning(request, 'Debes iniciar sesión para acceder a esta página')
            return redirect('contable:login')
        return view_func(request, *args, **kwargs)
    
    wrapped_view.__name__ = view_func.__name__
    wrapped_view.__doc__ = view_func.__doc__
    return wrapped_view
