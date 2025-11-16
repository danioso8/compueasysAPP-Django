from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count
from django.utils import timezone
from .models import ContableUser, UserProfile, Company, CompanyMembership, AuditLog
from .middleware import contable_login_required


def superuser_required(view_func):
    """Decorador para requerir permisos de superusuario"""
    def wrapped_view(request, *args, **kwargs):
        if not hasattr(request, 'contable_user') or request.contable_user is None:
            messages.warning(request, 'Debes iniciar sesión')
            return redirect('contable:login')
        
        if not request.contable_user.is_superuser:
            messages.error(request, 'No tienes permisos para acceder a esta página')
            return redirect('contable:dashboard')
        
        return view_func(request, *args, **kwargs)
    
    wrapped_view.__name__ = view_func.__name__
    return wrapped_view


@superuser_required
def admin_users_view(request):
    """Vista de administración de usuarios - Solo superusuarios"""
    user = request.contable_user
    
    # Filtros
    search = request.GET.get('search', '').strip()
    status = request.GET.get('status', 'all')  # all, active, inactive, pending
    role = request.GET.get('role', 'all')
    
    # Query base
    users = ContableUser.objects.all().select_related('profile').prefetch_related(
        'profile__companies'
    ).order_by('-date_joined')
    
    # Aplicar filtros
    if search:
        users = users.filter(
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    if status == 'active':
        users = users.filter(is_active=True, email_verified=True)
    elif status == 'inactive':
        users = users.filter(is_active=False)
    elif status == 'pending':
        users = users.filter(email_verified=False)
    
    if role != 'all':
        users = users.filter(profile__role=role)
    
    # Estadísticas
    stats = {
        'total': ContableUser.objects.count(),
        'active': ContableUser.objects.filter(is_active=True, email_verified=True).count(),
        'inactive': ContableUser.objects.filter(is_active=False).count(),
        'pending': ContableUser.objects.filter(email_verified=False).count(),
        'superusers': ContableUser.objects.filter(is_superuser=True).count(),
    }
    
    context = {
        'users': users,
        'stats': stats,
        'search': search,
        'current_status': status,
        'current_role': role,
    }
    
    return render(request, 'contable/admin_users.html', context)


@superuser_required
@require_http_methods(["POST"])
def toggle_user_status(request, user_id):
    """Activar/Desactivar usuario"""
    try:
        target_user = get_object_or_404(ContableUser, id=user_id)
        
        # No permitir desactivar el propio usuario
        if target_user.id == request.contable_user.id:
            return JsonResponse({
                'success': False,
                'message': 'No puedes desactivar tu propia cuenta'
            })
        
        # Cambiar estado
        target_user.is_active = not target_user.is_active
        target_user.save()
        
        # Registrar auditoría
        AuditLog.objects.create(
            user=request.contable_user,
            action='update',
            module='admin',
            description=f'{"Activó" if target_user.is_active else "Desactivó"} la cuenta de {target_user.email}',
            ip_address=get_client_ip(request)
        )
        
        return JsonResponse({
            'success': True,
            'is_active': target_user.is_active,
            'message': f'Usuario {"activado" if target_user.is_active else "desactivado"} exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


@superuser_required
@require_http_methods(["POST"])
def verify_user_email(request, user_id):
    """Verificar email de usuario manualmente"""
    try:
        target_user = get_object_or_404(ContableUser, id=user_id)
        
        target_user.email_verified = True
        target_user.email_token = ''
        target_user.save()
        
        # Registrar auditoría
        AuditLog.objects.create(
            user=request.contable_user,
            action='update',
            module='admin',
            description=f'Verificó manualmente el email de {target_user.email}',
            ip_address=get_client_ip(request)
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Email verificado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


@superuser_required
@require_http_methods(["POST"])
def delete_user(request, user_id):
    """Eliminar usuario permanentemente"""
    try:
        target_user = get_object_or_404(ContableUser, id=user_id)
        
        # No permitir eliminar el propio usuario
        if target_user.id == request.contable_user.id:
            return JsonResponse({
                'success': False,
                'message': 'No puedes eliminar tu propia cuenta'
            })
        
        # No permitir eliminar otros superusuarios
        if target_user.is_superuser:
            return JsonResponse({
                'success': False,
                'message': 'No puedes eliminar a otro superusuario'
            })
        
        user_email = target_user.email
        
        # Registrar auditoría antes de eliminar
        AuditLog.objects.create(
            user=request.contable_user,
            action='delete',
            module='admin',
            description=f'Eliminó la cuenta de {user_email}',
            ip_address=get_client_ip(request)
        )
        
        # Eliminar usuario (CASCADE eliminará perfil y membresías)
        target_user.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Usuario eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)


@superuser_required
def edit_user_view(request, user_id):
    """Vista para editar usuario"""
    target_user = get_object_or_404(ContableUser, id=user_id)
    
    if request.method == 'POST':
        try:
            # Actualizar datos básicos
            target_user.first_name = request.POST.get('first_name', '').strip()
            target_user.last_name = request.POST.get('last_name', '').strip()
            target_user.phone = request.POST.get('phone', '').strip()
            
            # Actualizar email solo si cambió
            new_email = request.POST.get('email', '').strip().lower()
            if new_email != target_user.email:
                if ContableUser.objects.filter(email=new_email).exclude(id=target_user.id).exists():
                    messages.error(request, 'Ya existe un usuario con ese email')
                    return redirect('contable:edit_user', user_id=user_id)
                target_user.email = new_email
            
            # Actualizar rol del perfil
            new_role = request.POST.get('role', 'user')
            if hasattr(target_user, 'profile'):
                target_user.profile.role = new_role
                target_user.profile.save()
            
            # Cambiar contraseña si se proporcionó
            new_password = request.POST.get('new_password', '').strip()
            if new_password:
                if len(new_password) >= 8:
                    target_user.set_password(new_password)
                else:
                    messages.error(request, 'La contraseña debe tener al menos 8 caracteres')
                    return redirect('contable:edit_user', user_id=user_id)
            
            target_user.save()
            
            # Registrar auditoría
            AuditLog.objects.create(
                user=request.contable_user,
                action='update',
                module='admin',
                description=f'Editó los datos de {target_user.email}',
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, 'Usuario actualizado exitosamente')
            return redirect('contable:admin_users')
            
        except Exception as e:
            messages.error(request, f'Error al actualizar usuario: {str(e)}')
    
    context = {
        'target_user': target_user,
        'companies': Company.objects.all(),
        'memberships': CompanyMembership.objects.filter(
            user_profile=target_user.profile
        ).select_related('company') if hasattr(target_user, 'profile') else []
    }
    
    return render(request, 'contable/edit_user.html', context)


def get_client_ip(request):
    """Obtener IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
