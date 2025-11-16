from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
import uuid
import secrets

from .models import (
    ContableUser, Plan, Company, UserProfile, CompanyMembership,
    AuditLog
)


# ==========================================
# VISTAS DE AUTENTICACIÓN
# ==========================================

def register_view(request):
    """Vista de registro con selección de plan"""
    if request.method == 'POST':
        # Obtener datos del formulario
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        phone = request.POST.get('phone', '').strip()
        plan_name = request.POST.get('plan', 'free')
        
        # Datos de la empresa
        company_name = request.POST.get('company_name', '').strip()
        company_legal_name = request.POST.get('company_legal_name', '').strip()
        company_tax_id = request.POST.get('company_tax_id', '').strip()
        
        # Validaciones
        errors = []
        
        if not all([first_name, last_name, email, password, company_name, company_tax_id]):
            errors.append('Todos los campos obligatorios deben ser completados')
        
        if password != password_confirm:
            errors.append('Las contraseñas no coinciden')
        
        if len(password) < 8:
            errors.append('La contraseña debe tener al menos 8 caracteres')
        
        if ContableUser.objects.filter(email=email).exists():
            errors.append('Ya existe una cuenta con este email')
        
        if Company.objects.filter(tax_id=company_tax_id).exists():
            errors.append('Ya existe una empresa registrada con este NIT/RUT')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'contable/register.html', {
                'plans': Plan.objects.filter(is_active=True),
                'selected_plan': plan_name
            })
        
        try:
            # Obtener el plan
            plan = Plan.objects.get(name=plan_name, is_active=True)
            
            # Crear usuario ContableUser
            email_token = secrets.token_urlsafe(32)
            user = ContableUser.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                email_verified=False,
                email_token=email_token
            )
            
            # Crear perfil de usuario
            user_profile = UserProfile.objects.create(
                user=user,
                role='admin',  # El primer usuario es administrador
            )
            
            # Crear empresa
            company = Company.objects.create(
                name=company_name,
                legal_name=company_legal_name or company_name,
                tax_id=company_tax_id,
                email=email,
                plan=plan,
                is_active=True
            )
            
            # Crear membresía
            CompanyMembership.objects.create(
                user_profile=user_profile,
                company=company,
                role_in_company='admin',
                is_default=True,
                permissions={
                    'all_modules': True,
                    'can_create': True,
                    'can_edit': True,
                    'can_delete': True,
                    'can_approve': True
                }
            )
            
            # Enviar email de verificación
            send_verification_email(user, email_token, request)
            
            # Registrar auditoría
            AuditLog.objects.create(
                user=user,
                company=company,
                action='create',
                module='auth',
                description=f'Nuevo registro: {user.get_full_name()} - {company.name}',
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, 'Cuenta creada exitosamente. Por favor verifica tu email para activar tu cuenta.')
            return redirect('contable:login')
            
        except Plan.DoesNotExist:
            messages.error(request, 'Plan seleccionado no válido')
        except Exception as e:
            messages.error(request, f'Error al crear la cuenta: {str(e)}')
            if 'user' in locals():
                user.delete()
    
    # GET request
    selected_plan = request.GET.get('plan', 'free')
    plans = Plan.objects.filter(is_active=True)
    
    return render(request, 'contable/register.html', {
        'plans': plans,
        'selected_plan': selected_plan
    })


def login_view(request):
    """Vista de inicio de sesión"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        
        if not email or not password:
            messages.error(request, 'Por favor ingresa email y contraseña')
            return render(request, 'contable/login.html')
        
        try:
            # Buscar usuario de contable por email
            user = ContableUser.objects.filter(email=email).first()
            
            if not user:
                messages.error(request, 'Email o contraseña incorrectos')
                return render(request, 'contable/login.html')
            
            # Autenticar con el backend personalizado de ContableUser
            if user.check_password(password):
                # Verificar si el email está verificado
                if not user.email_verified:
                    messages.warning(request, 'Por favor verifica tu email antes de iniciar sesión')
                    return render(request, 'contable/login.html')
                
                    messages.warning(request, 'Por favor verifica tu email antes de iniciar sesión')
                    return render(request, 'contable/login.html')
                
                # Crear sesión manualmente (no usamos django.contrib.auth.login)
                request.session['contable_user_id'] = str(user.id)
                request.session['contable_user_email'] = user.email
                request.session['contable_user_name'] = user.get_full_name()
                
                # Actualizar last_login
                user.last_login = timezone.now()
                user.save(update_fields=['last_login'])
                
                # Obtener empresa por defecto
                default_membership = CompanyMembership.objects.filter(
                    user_profile=user.profile,
                    is_default=True
                ).first()
                
                if default_membership:
                    request.session['current_company_id'] = str(default_membership.company.id)
                    request.session['current_company_name'] = default_membership.company.name
                    request.session['user_role'] = default_membership.role_in_company
                    
                    # Registrar auditoría
                    AuditLog.objects.create(
                        user=user,
                        company=default_membership.company,
                        action='login',
                        module='auth',
                        description=f'Inicio de sesión exitoso',
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                
                messages.success(request, f'¡Bienvenido {user.get_full_name()}!')
                
                # Redirigir
                next_url = request.GET.get('next', 'contable:dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'Email o contraseña incorrectos')
        except Exception as e:
            messages.error(request, 'Error al iniciar sesión')
            print(f"Error en login: {e}")
    
    return render(request, 'contable/login.html')


def logout_view(request):
    """Cerrar sesión"""
    user_id = request.session.get('contable_user_id')
    company_id = request.session.get('current_company_id')
    
    if user_id and company_id:
        try:
            user = ContableUser.objects.get(id=user_id)
            company = Company.objects.get(id=company_id)
            AuditLog.objects.create(
                user=user,
                company=company,
                action='logout',
                module='auth',
                description='Cierre de sesión',
                ip_address=get_client_ip(request)
            )
        except (ContableUser.DoesNotExist, Company.DoesNotExist):
            pass
    
    # Limpiar sesión de contable
    request.session.pop('contable_user_id', None)
    request.session.pop('contable_user_email', None)
    request.session.pop('contable_user_name', None)
    request.session.pop('current_company_id', None)
    request.session.pop('current_company_name', None)
    request.session.pop('user_role', None)
    
    messages.success(request, 'Sesión cerrada exitosamente')
    return redirect('contable:login')


def verify_email(request, token):
    """Verificar email del usuario"""
    try:
        user = ContableUser.objects.get(email_token=token, email_verified=False)
        user.email_verified = True
        user.email_token = ''
        user.save()
        
        messages.success(request, '¡Email verificado exitosamente! Ya puedes iniciar sesión.')
        return redirect('contable:login')
    except ContableUser.DoesNotExist:
        messages.error(request, 'Token de verificación inválido o expirado')
        return redirect('contable:register')


def forgot_password(request):
    """Solicitar restablecimiento de contraseña"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        
        try:
            user = ContableUser.objects.get(email=email)
            
            # Generar token de restablecimiento
            reset_token = secrets.token_urlsafe(32)
            user.profile.reset_token = reset_token
            user.profile.reset_token_expires = timezone.now() + timedelta(hours=24)
            user.profile.save()
            
            # Enviar email
            send_password_reset_email(user, reset_token, request)
            
            messages.success(request, 'Se ha enviado un enlace de restablecimiento a tu email')
            return redirect('contable:login')
        except User.DoesNotExist:
            messages.error(request, 'No existe una cuenta con este email')
    
    return render(request, 'contable/forgot_password.html')


def reset_password(request, token):
    """Restablecer contraseña con token"""
    try:
        user_profile = UserProfile.objects.get(
            reset_token=token,
            reset_token_expires__gt=timezone.now()
        )
        
        if request.method == 'POST':
            password = request.POST.get('password', '')
            password_confirm = request.POST.get('password_confirm', '')
            
            if password != password_confirm:
                messages.error(request, 'Las contraseñas no coinciden')
            elif len(password) < 8:
                messages.error(request, 'La contraseña debe tener al menos 8 caracteres')
            else:
                user_profile.user.set_password(password)
                user_profile.user.save()
                user_profile.reset_token = ''
                user_profile.reset_token_expires = None
                user_profile.save()
                
                messages.success(request, 'Contraseña restablecida exitosamente')
                return redirect('contable:login')
        
        return render(request, 'contable/reset_password.html', {'token': token})
    except UserProfile.DoesNotExist:
        messages.error(request, 'Token de restablecimiento inválido o expirado')
        return redirect('contable:forgot_password')


# ==========================================
# DASHBOARD PRINCIPAL
# ==========================================

from .middleware import contable_login_required


@contable_login_required
def dashboard_view(request):
    """Dashboard principal del sistema contable"""
    user = request.contable_user
    user_profile = user.profile
    
    # Obtener empresa actual
    company_id = request.session.get('current_company_id')
    if not company_id:
        # Si no hay empresa en sesión, obtener la default
        default_membership = CompanyMembership.objects.filter(
            user_profile=user_profile,
            is_default=True
        ).first()
        
        if not default_membership:
            messages.error(request, 'No tienes acceso a ninguna empresa')
            return redirect('contable:logout')
        
        company = default_membership.company
        request.session['current_company_id'] = str(company.id)
        request.session['current_company_name'] = company.name
    else:
        try:
            company = Company.objects.get(id=company_id)
        except Company.DoesNotExist:
            messages.error(request, 'Empresa no encontrada')
            return redirect('contable:logout')
    
    # Obtener membresía y permisos
    membership = CompanyMembership.objects.get(
        user_profile=user_profile,
        company=company
    )
    
    # Obtener todas las empresas del usuario para el selector
    user_companies = CompanyMembership.objects.filter(
        user_profile=user_profile
    ).select_related('company')
    
    context = {
        'company': company,
        'membership': membership,
        'user_companies': user_companies,
        'plan': company.plan,
        'user_role': membership.role_in_company,
        'permissions': membership.permissions
    }
    
    return render(request, 'contable/dashboard.html', context)


# ==========================================
# UTILIDADES
# ==========================================

def get_client_ip(request):
    """Obtener IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def send_verification_email(user, token, request):
    """Enviar email de verificación"""
    verify_url = request.build_absolute_uri(f'/contable/verify/{token}/')
    
    subject = 'Verifica tu cuenta - CompuEasys Contable'
    message = f'''
    Hola {user.first_name},
    
    Gracias por registrarte en CompuEasys Contable.
    
    Para completar tu registro, por favor verifica tu email haciendo clic en el siguiente enlace:
    
    {verify_url}
    
    Este enlace expirará en 24 horas.
    
    Si no creaste esta cuenta, puedes ignorar este email.
    
    Saludos,
    Equipo de CompuEasys
    '''
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Error sending verification email: {e}")


def send_password_reset_email(user, token, request):
    """Enviar email de restablecimiento de contraseña"""
    reset_url = request.build_absolute_uri(f'/contable/reset-password/{token}/')
    
    subject = 'Restablecer contraseña - CompuEasys Contable'
    message = f'''
    Hola {user.first_name},
    
    Recibimos una solicitud para restablecer tu contraseña.
    
    Para crear una nueva contraseña, haz clic en el siguiente enlace:
    
    {reset_url}
    
    Este enlace expirará en 24 horas.
    
    Si no solicitaste restablecer tu contraseña, puedes ignorar este email.
    
    Saludos,
    Equipo de CompuEasys
    '''
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    except Exception as e:
        print(f"Error sending password reset email: {e}")
