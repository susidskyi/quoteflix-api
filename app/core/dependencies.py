import aioboto3
from typing import AsyncGenerator
from fastapi import Depends
from types_aiobotocore_s3 import S3Client
from app.core.presigned_url_service import PresignedURLService
from app.core.s3_service import S3Service


async def get_s3_session() -> AsyncGenerator[S3Client, None]:
    session = aioboto3.Session(region_name="eu-center-1")

    return session


async def get_s3_service(s3_session: S3Client = Depends(get_s3_session)):
    return S3Service(s3_session=s3_session)


async def get_presigned_url_service(s3_service: S3Service = Depends(get_s3_service)):
    return PresignedURLService(s3_service)
