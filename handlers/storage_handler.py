import random
import string
from datetime import datetime


def _fake_id(prefix="bkt"):
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{prefix}-{suffix}"


def handle(intent, params, dry_run):
    handler = {
        "storage.bucket_create": _bucket_create,
        "storage.bucket_delete": _bucket_delete,
        "storage.upload":        _upload,
        "storage.lifecycle":     _lifecycle,
        "storage.status":        _status,
    }.get(intent)
    if not handler:
        return {"status": "error", "message": f"No storage handler for intent: {intent}"}
    return handler(params, dry_run)


def _bucket_create(params, dry_run):
    name   = params.get("name", _fake_id())
    region = params.get("region", "us-east-1")
    if dry_run:
        return {"status": "dry_run", "message": f"Would create bucket '{name}' in {region}", "would_call": "PUT /s3/v1/buckets"}
    return {"status": "success", "message": f"Bucket '{name}' created", "name": name, "region": region, "arn": f"arn:aws:s3:::{name}", "created_at": datetime.utcnow().isoformat() + "Z"}


def _bucket_delete(params, dry_run):
    name = params.get("name", "unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would delete bucket '{name}' and all contents", "would_call": "DELETE /s3/v1/buckets/{name}"}
    return {"status": "success", "message": f"Bucket '{name}' deleted", "deleted_at": datetime.utcnow().isoformat() + "Z"}


def _upload(params, dry_run):
    bucket = params.get("bucket", params.get("name", "unknown"))
    key    = params.get("key", params.get("file", "upload.dat"))
    if dry_run:
        return {"status": "dry_run", "message": f"Would upload '{key}' to bucket '{bucket}'", "would_call": f"PUT /s3/v1/buckets/{bucket}/objects"}
    return {"status": "success", "message": f"Uploaded '{key}' to '{bucket}'", "bucket": bucket, "key": key, "size_bytes": random.randint(1024, 10485760), "uploaded_at": datetime.utcnow().isoformat() + "Z"}


def _lifecycle(params, dry_run):
    bucket = params.get("bucket", params.get("name", "unknown"))
    if dry_run:
        return {"status": "dry_run", "message": f"Would set lifecycle policy on bucket '{bucket}'", "would_call": f"PUT /s3/v1/buckets/{bucket}/lifecycle"}
    return {"status": "success", "message": f"Lifecycle policy applied to '{bucket}'", "applied_at": datetime.utcnow().isoformat() + "Z"}


def _status(params, dry_run):
    name = params.get("name", "unknown")
    if dry_run:
        return {"status": "dry_run", "message": f"Would fetch status for bucket '{name}'", "would_call": f"GET /s3/v1/buckets/{name}"}
    return {"status": "success", "name": name, "objects": random.randint(10, 100000), "size_gb": round(random.uniform(0.1, 500), 1), "checked_at": datetime.utcnow().isoformat() + "Z"}
