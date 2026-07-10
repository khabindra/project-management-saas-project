from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from common.models import TimeStampedModel


class CustomUserManager(BaseUserManager):
    """
    Custom user manager where email is the unique identifier
    instead of username.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        
        # Notice we do NOT pass username here
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(TimeStampedModel, AbstractUser):
    """
    Custom User model with email as the unique identifier.
    """
    # I removed `id = models.UUIDField(...)` here because you already 
    # inherit it from TimeStampedModel! No need to define it twice.
    
    username = None  # Remove username field entirely
    email = models.EmailField(unique=True) 
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)

    # 1. Tell Django to use email for login
    USERNAME_FIELD = 'email'
    
    # 2. Tell Django that NO other fields are required when typing createsuperuser
    REQUIRED_FIELDS = []

    # 3. ATTACH THE CUSTOM MANAGER HERE!
    objects = CustomUserManager()

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return self.get_full_name()