import aioboto3
from fastapi import Depends

from app.core.config import settings
from app.s3.presigned_url_service import PresignedURLService
from app.s3.s3_service import S3Service


async def get_s3_session() -> aioboto3.Session:
    return aioboto3.Session(
        region_name=settings.s3_region_name,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
    )


async def get_s3_service(
    s3_session: aioboto3.Session = Depends(get_s3_session),
) -> S3Service:
    return S3Service(s3_session=s3_session)


async def get_presigned_url_service(
    s3_service: S3Service = Depends(get_s3_service),
) -> PresignedURLService:
    return PresignedURLService(s3_service)
