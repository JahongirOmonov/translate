import os
from celery import Celery

# Django settings modulini o'rnatish
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.settings")

# Celery ilovasini yaratish
app = Celery("src")

# Django sozlamalaridan Celery konfiguratsiyasini yuklash
app.config_from_object("django.conf:settings", namespace="CELERY")

# Broker ulanishni qayta urinib ko'rishni faollashtirish (Celery 6.0 uchun zarur)
app.conf.broker_connection_retry_on_startup = True

# Django loyihasidagi tasks (vazifalar)ni avtomatik aniqlash
app.autodiscover_tasks()

# Custom vazifalarni tekshirish uchun misol
@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
