import os
from pathlib import Path
from typing import Any

from storage.keys import validate_object_key
from storage.local import sha256


class S3ArtifactStorage:
    backend = "s3"

    def put_file(self, path: Path, object_key: str, content_type: str | None = None) -> dict:
        object_key = validate_object_key(object_key)
        checksum = sha256(path)
        client = self._client()
        extra_args: dict[str, Any] = {"Metadata": {"sha256": checksum}}
        if content_type:
            extra_args["ContentType"] = content_type
        client.upload_file(
            str(path),
            self._bucket(),
            object_key,
            ExtraArgs=extra_args,
        )
        return {"storage_backend": self.backend, "object_key": object_key, "checksum": checksum, "content_type": content_type}

    def open_file(self, object_key: str):
        response = self._client().get_object(Bucket=self._bucket(), Key=object_key)
        return response["Body"]

    def _bucket(self) -> str:
        bucket = os.getenv("S3_BUCKET", "").strip()
        if not bucket:
            raise RuntimeError("S3_BUCKET is required when ARTIFACT_STORAGE_BACKEND=s3")
        return bucket

    def _client(self):
        import boto3

        endpoint = os.getenv("S3_ENDPOINT_URL") or None
        region = os.getenv("S3_REGION") or "us-east-1"
        secure = os.getenv("S3_SECURE", "true").lower() not in {"0", "false", "no"}
        return boto3.client(
            "s3",
            endpoint_url=endpoint,
            region_name=region,
            aws_access_key_id=os.getenv("S3_ACCESS_KEY_ID") or None,
            aws_secret_access_key=os.getenv("S3_SECRET_ACCESS_KEY") or None,
            use_ssl=secure,
        )
