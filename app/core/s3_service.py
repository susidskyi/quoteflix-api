import logging
from typing import Any

import aioboto3
from fastapi import UploadFile

from app.core.config import settings

# Disable a lot of boto3 logs such as binary file data etc.
logging.getLogger("boto3").setLevel(logging.CRITICAL)
logging.getLogger("botocore").setLevel(logging.CRITICAL)


class S3Service:
    def __init__(self) -> None:
        self.s3_bucket = settings.s3_bucket
        self.session = aioboto3.Session(region_name=settings.aws_region_name)

    async def upload_file_object(self, upload_file: UploadFile, key: str) -> bool:
        async with self.session.client("s3") as s3_client:
            await s3_client.upload_fileobj(upload_file, self.s3_bucket, key)

        return True

    async def get_object(self, key: str) -> Any:
        async with self.session.client("s3") as s3_client:
            return await s3_client.get_object(Bucket=self.s3_bucket, Key=key)

    async def delete_file(self, key: str) -> bool:
        async with self.session.client("s3") as s3_client:
            await s3_client.delete_object(Bucket=self.s3_bucket, Key=key)

        return True
