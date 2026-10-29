import os
from pathlib import Path
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
application = get_wsgi_application()

try:
    from whitenoise import WhiteNoise
    BASE_DIR = Path(__file__).resolve().parent.parent
    static_root = BASE_DIR / 'staticfiles'
    if static_root.exists():
        application = WhiteNoise(application, root=str(static_root), prefix='/static/')
        application.add_files(str(static_root), prefix='/static/')
except Exception as e:
    pass

app = application

