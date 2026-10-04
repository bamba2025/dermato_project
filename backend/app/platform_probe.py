"""Test d'intégration technique à exécuter dans le conteneur backend."""

import time
import uuid
from urllib.error import HTTPError
from urllib.request import urlopen

import boto3
from redis import Redis
from rq import Queue
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import session_factory


def main() -> None:
    settings = get_settings()
    with session_factory()() as db:
        assert db.scalar(text("SELECT extname FROM pg_extension WHERE extname = 'vector'"))
        assert db.scalar(text("SELECT '[1,2,3]'::vector <-> '[1,2,3]'::vector")) == 0
    s3 = boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
    )
    key = f"integration/{uuid.uuid4()}/probe.txt"
    s3.put_object(Bucket=settings.s3_bucket, Key=key, Body=b"technical-probe")
    try:
        unsigned = f"{settings.s3_endpoint}/{settings.s3_bucket}/{key}"
        try:
            with urlopen(unsigned, timeout=10):
                raise AssertionError("Le bucket autorise un accès anonyme")
        except HTTPError as error:
            assert error.code == 403
        signed = s3.generate_presigned_url(
            "get_object", Params={"Bucket": settings.s3_bucket, "Key": key}, ExpiresIn=30
        )
        with urlopen(signed, timeout=10) as response:
            assert response.read() == b"technical-probe"
    finally:
        s3.delete_object(Bucket=settings.s3_bucket, Key=key)
    with Redis.from_url(settings.redis_url) as connection:
        job = Queue("analysis", connection=connection).enqueue("worker.tasks.ping", result_ttl=60)
        deadline = time.monotonic() + 45
        while time.monotonic() < deadline:
            job.refresh()
            if job.is_finished:
                assert job.return_value() == "ok"
                job.delete()
                print("Probe OK : pgvector, objet privé, URL signée et worker Redis.")
                return
            if job.is_failed:
                raise AssertionError("Le worker a échoué sur la tâche technique")
            time.sleep(0.25)
    raise AssertionError("Le worker n'a pas traité la tâche technique")


if __name__ == "__main__":
    main()
