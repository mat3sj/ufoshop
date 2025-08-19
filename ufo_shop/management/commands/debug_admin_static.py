import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.staticfiles import finders, storage
from django.templatetags.static import static


class Command(BaseCommand):
    help = "Diagnose missing admin static files in production.\n\n" \
           "This checks Django staticfiles configuration, attempts to resolve\n" \
           "'admin/css/base.css' through finders and storage, and prints\n" \
           "actionable next steps."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("== Staticfiles Diagnostics =="))
        self.stdout.write(f"DEBUG: {settings.DEBUG}")
        self.stdout.write(f"STATIC_URL: {settings.STATIC_URL}")
        self.stdout.write(f"STATIC_ROOT: {getattr(settings, 'STATIC_ROOT', None)}")
        staticfiles_dirs = getattr(settings, 'STATICFILES_DIRS', [])
        self.stdout.write(f"STATICFILES_DIRS: {list(staticfiles_dirs)}")
        self.stdout.write(f"STATICFILES_STORAGE: {getattr(settings, 'STATICFILES_STORAGE', 'django.contrib.staticfiles.storage.StaticFilesStorage')}")

        target = 'admin/css/base.css'
        self.stdout.write(self.style.NOTICE(f"\n-- Looking for '{target}' using finders --"))
        try:
            path = finders.find(target)
        except Exception as e:
            path = None
            self.stdout.write(self.style.ERROR(f"Error calling finders.find: {e}"))
        self.stdout.write(f"finders.find('{target}') => {path}")
        if path and os.path.exists(path):
            try:
                size = os.path.getsize(path)
            except Exception:
                size = 'unknown'
            self.stdout.write(f"Found on filesystem: {path} (size={size})")
        else:
            self.stdout.write(self.style.WARNING("Not found by finders. Ensure 'django.contrib.staticfiles' is in INSTALLED_APPS."))

        self.stdout.write(self.style.NOTICE("\n-- Checking STATIC_ROOT contents --"))
        if getattr(settings, 'STATIC_ROOT', None):
            in_root = os.path.join(settings.STATIC_ROOT, target)
            exists_in_root = os.path.exists(in_root)
            self.stdout.write(f"Expected path: {in_root}\nExists: {exists_in_root}")
        else:
            self.stdout.write(self.style.WARNING("STATIC_ROOT is not set. In production you must set STATIC_ROOT and run collectstatic."))

        self.stdout.write(self.style.NOTICE("\n-- Resolving URL and hashed name (if Manifest storage) --"))
        try:
            url = static(target)
            self.stdout.write(f"static('{target}') => {url}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error resolving static() URL: {e}"))

        st = storage.staticfiles_storage
        # Try to display hashed name/location if using Manifest storage
        hashed_path = None
        if hasattr(st, 'hashed_name'):
            try:
                hashed_path = st.hashed_name(target)
                self.stdout.write(f"hashed_name => {hashed_path}")
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"hashed_name not available yet (likely need collectstatic): {e}"))
        if getattr(settings, 'STATIC_ROOT', None) and hashed_path:
            hashed_fs = os.path.join(settings.STATIC_ROOT, hashed_path)
            self.stdout.write(f"Hashed file exists in STATIC_ROOT: {os.path.exists(hashed_fs)} ({hashed_fs})")

        self.stdout.write(self.style.MIGRATE_HEADING("\n== Next steps if styles are missing in /admin/ =="))
        self.stdout.write("1) On the server, run: source venv/bin/activate && python manage.py collectstatic --noinput --settings=ufo_shop.settings.production")
        self.stdout.write("2) Verify Nginx serves /static/ from STATIC_ROOT using alias, not root. For these settings:")
        self.stdout.write("   location /static/ { alias %s; access_log off; expires 7d; }" % getattr(settings, 'STATIC_ROOT', '<<STATIC_ROOT>>'))
        self.stdout.write("3) Test via Nginx directly: curl -I https://<your-domain>/static/admin/css/base.css")
        self.stdout.write("4) Check permissions: ensure the Nginx user (www-data) can read STATIC_ROOT.")
        self.stdout.write("5) Check logs: sudo tail -f /var/log/nginx/error.log and journalctl -u gunicorn")
        self.stdout.write("6) You can also run: python manage.py findstatic admin/css/base.css -v 2 for detailed finder output.")
        self.stdout.write(self.style.SUCCESS("Diagnostics complete."))
