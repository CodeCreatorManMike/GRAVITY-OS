"""
Storage service — MinIO object storage for user-uploaded files and generated documents.

Bucket layout:
  gravity-files/
    uploads/{user_id}/{file_id}/{filename}     ← user-uploaded PDFs, syllabuses, etc.
    generated/{user_id}/{file_id}/{filename}   ← AI-generated notes, study plans, reports
"""

from __future__ import annotations

import io
from typing import Optional

from backend.config import get_settings

_client = None


def _get_client():
    global _client
    if _client is None:
        from minio import Minio
        s = get_settings()
        _client = Minio(
            s.minio_endpoint,
            access_key=s.minio_access_key,
            secret_key=s.minio_secret_key,
            secure=s.minio_secure,
        )
        _ensure_bucket(_client, s.minio_bucket)
    return _client


def _ensure_bucket(client, bucket: str) -> None:
    from minio.error import S3Error
    try:
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
    except S3Error as e:
        print(f"[storage] bucket init error: {e}")


def _object_name(user_id: int, file_id: int, filename: str, generated: bool = False) -> str:
    prefix = "generated" if generated else "uploads"
    return f"{prefix}/{user_id}/{file_id}/{filename}"


async def upload_file(
    user_id: int,
    file_id: int,
    filename: str,
    data: bytes,
    content_type: str = "application/octet-stream",
    generated: bool = False,
) -> str:
    """Upload bytes to MinIO. Returns the object name (path within bucket)."""
    import asyncio
    client = _get_client()
    settings = get_settings()
    object_name = _object_name(user_id, file_id, filename, generated)

    def _put():
        client.put_object(
            settings.minio_bucket,
            object_name,
            io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )

    await asyncio.to_thread(_put)
    return object_name


async def download_file(user_id: int, file_id: int, filename: str, generated: bool = False) -> bytes:
    """Download bytes from MinIO."""
    import asyncio
    client = _get_client()
    settings = get_settings()
    object_name = _object_name(user_id, file_id, filename, generated)

    def _get():
        response = client.get_object(settings.minio_bucket, object_name)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    return await asyncio.to_thread(_get)


async def delete_file(user_id: int, file_id: int, filename: str, generated: bool = False) -> None:
    """Delete an object from MinIO."""
    import asyncio
    client = _get_client()
    settings = get_settings()
    object_name = _object_name(user_id, file_id, filename, generated)

    await asyncio.to_thread(
        client.remove_object, settings.minio_bucket, object_name
    )


def presigned_url(user_id: int, file_id: int, filename: str, generated: bool = False, expires_seconds: int = 3600) -> Optional[str]:
    """Return a presigned download URL valid for expires_seconds. Returns None on error."""
    from datetime import timedelta
    from minio.error import S3Error
    client = _get_client()
    settings = get_settings()
    object_name = _object_name(user_id, file_id, filename, generated)
    try:
        return client.presigned_get_object(
            settings.minio_bucket,
            object_name,
            expires=timedelta(seconds=expires_seconds),
        )
    except S3Error as e:
        print(f"[storage] presign error: {e}")
        return None
