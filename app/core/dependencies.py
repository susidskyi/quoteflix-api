import aioboto3
from fastapi import Depends

from app.core.config import settings
from app.core.presigned_url_service import PresignedURLService
from app.core.s3_service import S3Service


async def get_s3_session() -> aioboto3.Session:
    return aioboto3.Session(region_name=settings.aws_region_name)


async def get_s3_service(
    s3_session: aioboto3.Session = Depends(get_s3_session),
) -> S3Service:
    return S3Service(s3_session=s3_session)


async def get_presigned_url_service(
    s3_service: S3Service = Depends(get_s3_service),
) -> PresignedURLService:
    return PresignedURLService(s3_service)
