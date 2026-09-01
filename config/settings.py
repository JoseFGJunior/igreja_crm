from pathlib import Path

from decouple import Config
from decouple import Csv
from decouple import RepositoryEnv
from decouple import config as bootstrap_config
from django.core.exceptions import ImproperlyConfigured


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

ENVIRONMENT = bootstrap_config('ENVIRONMENT', default='development').lower()

if ENVIRONMENT not in {'development', 'production'}:
    raise ImproperlyConfigured(
        'ENVIRONMENT deve ser "development" ou "production".'
    )

environment_file = BASE_DIR / f'.env.{ENVIRONMENT}'

if not environment_file.exists():
    raise ImproperlyConfigured(
        f'Arquivo de configuração não encontrado: {environment_file.name}'
    )

config = Config(RepositoryEnv(str(environment_file)))
ENVIRONMENT_DISPLAY = {
    'development': 'DESENVOLVIMENTO',
    'production': 'PRODUÇÃO',
}[ENVIRONMENT]


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config(
    'SECRET_KEY',
    default='django-insecure-^)rh+q!jn8ew2reu)lf51ygs+^t6rx$$g!sg*v_*+*ms1+lg4f'
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config(
    'DEBUG',
    default=True,
    cast=bool
)

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='',
    cast=Csv()
)


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'apps.core',
    'apps.igrejas',
    'apps.membros',
    'apps.accounts',
    'apps.financeiro',
    'apps.eventos',
    
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.igreja_atual',
                'apps.core.context_processors.environment',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DB_ENGINE = config('DB_ENGINE')

if DB_ENGINE != 'postgresql':
    raise ImproperlyConfigured(
        'DB_ENGINE deve ser postgresql em todos os ambientes.'
    )

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('POSTGRES_DB'),
        'USER': config('POSTGRES_USER'),
        'PASSWORD': config('POSTGRES_PASSWORD'),
        'HOST': config('POSTGRES_HOST'),
        'PORT': config('POSTGRES_PORT', default='5432'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Sao_Paulo'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static'
]

STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'

MEDIA_ROOT = BASE_DIR / 'media'

AUTH_USER_MODEL = 'accounts.Usuario'

LOGIN_URL = 'login'
