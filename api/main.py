from app.core.sentry_init import init_sentry

init_sentry()

from app.main import create_app

app = create_app()
