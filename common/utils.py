import uuid


def generate_unique_slug(instance, slug_field, queryset=None):
    """
    Generate a unique slug for a model instance.
    """
    if queryset is None:
        queryset = instance.__class__.objects.all()
    
    slug = getattr(instance, slug_field)
    original_slug = slug
    
    counter = 1
    while queryset.filter(**{slug_field: slug}).exists():
        slug = f"{original_slug}-{counter}"
        counter += 1
    
    return slug


def get_client_ip(request):
    """
    Get client IP address from request.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip