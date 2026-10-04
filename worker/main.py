from redis import Redis
from rq import Worker

from app.core.config import get_settings


def main() -> None:
    settings = get_settings()
    connection = Redis.from_url(settings.redis_url)
    # L'exécution RQ forkée s'effectue dans le conteneur Linux, pas sous Windows.
    worker = Worker(["analysis"], connection=connection, worker_ttl=90)
    worker.work(with_scheduler=False)


if __name__ == "__main__":
    main()
