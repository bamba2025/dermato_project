from datetime import timedelta

from redis import Redis
from rq import Worker

from app.core.config import get_settings
from app.models.identity import utcnow

connection = Redis.from_url(get_settings().redis_url)
workers = Worker.all(connection=connection)
fresh = any(
    w.last_heartbeat and utcnow() - w.last_heartbeat < timedelta(minutes=2)
    for w in workers
)
raise SystemExit(0 if fresh else 1)
