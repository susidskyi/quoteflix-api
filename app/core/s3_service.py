import io
import itertools
import logging
from typing import Any

import aioboto3

from app.core.config import settings

# Disable a lot of boto3 logs such as binary file data etc.
logging.getLogger("boto3").setLevel(logging.CRITICAL)
logging.getLogger("botocore").setLevel(logging.CRITICAL)


class S3Service:
    def __init__(self) -> None:
        self.s3_bucket = settings.s3_bucket
        self.session = aioboto3.Session(region_name=settings.aws_region_name)

    async def get_all_objects_in_folder(self, prefix: str) -> list[str]:
        async with self.session.client("s3") as s3_client:
            paginator = s3_client.get_paginator("list_objects_v2")

            all_objects = []

            async for page in paginator.paginate(Bucket=self.s3_bucket, Prefix=prefix):
                # Collect only the objects keys
                new_objects = list(map(lambda x: x["Key"], page["Contents"]))

                all_objects.extend(new_objects)

        return all_objects

    async def upload_fileobj(self, fileobj: io.BytesIO, key: str) -> None:
        async with self.session.client("s3") as s3_client:
            await s3_client.upload_fileobj(fileobj, settings.s3_bucket, key)

    async def delete_folder(self, prefix: str) -> None:
        all_objects = await self.get_all_objects_in_folder(prefix)

        await self.delete_objects(all_objects)

    async def delete_object(self, key: str) -> None:
        async with self.session.client("s3") as s3_client:
            await s3_client.delete_object(Bucket=self.s3_bucket, Key=key)

    async def delete_objects(self, keys: list[str]) -> None:
        async with self.session.client("s3") as s3_client:
            objects_list = {"Objects": []}

            for key in keys:
                objects_list["Objects"].append({"Key": key})

            for batched_objects in itertools.batched(objects_list["Objects"], 1000):
                await s3_client.delete_objects(
                    Bucket=self.s3_bucket, Delete={"Objects": batched_objects}
                )

    async def get_presigned_url(self, key: str) -> str:
        async with self.session.client("s3") as s3_client:
            return await s3_client.generate_presigned_url(
                "get_object", Params={"Bucket": self.s3_bucket, "Key": key}
            )
