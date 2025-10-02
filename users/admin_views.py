import json
import jwt
import os
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Count
from .models import User
from images.models import Image
from classification.models import Classification


# JWT verification decorator
def jwt_required_admin(view_func):
    def wrapper(request, *args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return JsonResponse({'message': 'Token de autorização obrigatório'}, status=401)
        
        if not token.startswith('Bearer '):
            return JsonResponse({'message': 'Formato de token inválido'}, status=401)
        
        token = token[7:]  # Remove 'Bearer ' prefix
        
        try:
            payload = jwt.decode(
                token, 
                os.getenv('JWT_SECRET_KEY', 'default-secret-key'),
                algorithms=['HS256']
            )
            
            # Check if user exists and is admin
            user = User.objects.get(id=payload['user_id'])
            if not user.is_staff:  # Assuming admin privileges through is_staff
                return JsonResponse({'message': 'Acesso negado. Privilégios de administrador necessários'}, status=403)
                
            request.user = user
            return view_func(request, *args, **kwargs)
            
        except jwt.ExpiredSignatureError:
            return JsonResponse({'message': 'Token expirado'}, status=401)
        except jwt.InvalidTokenError:
            return JsonResponse({'message': 'Token inválido'}, status=401)
        except User.DoesNotExist:
            return JsonResponse({'message': 'Usuário não encontrado'}, status=401)
        except Exception as e:
            return JsonResponse({'message': 'Erro de autenticação'}, status=401)
    
    return wrapper


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required_admin
def get_metrics(request):
    """
    GET /admin/metrics/
    Returns system metrics for administrators
    """
    try:
        # Count total users
        total_users = User.objects.count()
        
        # Count total images
        total_images = Image.objects.count()
        
        # Count total classifications
        total_classifications = Classification.objects.count()
        
        # Count classifications by stage
        classifications_by_stage = Classification.objects.values('stage').annotate(
            count=Count('stage')
        ).order_by('stage')
        
        # Format stage counts
        stage_counts = {}
        for item in classifications_by_stage:
            stage_counts[item['stage']] = item['count']
        
        # Count users by specialty
        users_by_specialty = User.objects.exclude(
            specialty__isnull=True
        ).exclude(
            specialty__exact=''
        ).values('specialty').annotate(
            count=Count('specialty')
        ).order_by('specialty')
        
        specialty_counts = {}
        for item in users_by_specialty:
            specialty_counts[item['specialty']] = item['count']
        
        metrics = {
            'total_users': total_users,
            'total_images': total_images,
            'total_classifications': total_classifications,
            'classifications_by_stage': stage_counts,
            'users_by_specialty': specialty_counts,
            'generated_at': datetime.now().isoformat()
        }
        
        return JsonResponse(metrics, status=200)
        
    except Exception as e:
        return JsonResponse({
            'message': 'Erro interno do servidor',
            'errors': {'server': [str(e)]}
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
@jwt_required_admin
def list_admin_users(request):
    """
    GET /admin/users/
    Returns list of all users for administrators
    """
    try:
        users = User.objects.all().order_by('-date_joined')
        
        users_data = []
        for user in users:
            user_data = {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'coren': user.coren,
                'specialty': user.specialty,
                'institution': user.institution,
                'is_staff': user.is_staff,
                'is_active': user.is_active,
                'date_joined': user.date_joined.isoformat() if user.date_joined else None,
                'last_login': user.last_login.isoformat() if user.last_login else None
            }
            users_data.append(user_data)
        
        return JsonResponse({
            'users': users_data,
            'total_count': len(users_data)
        }, status=200)
        
    except Exception as e:
        return JsonResponse({
            'message': 'Erro interno do servidor',
            'errors': {'server': [str(e)]}
        }, status=500)