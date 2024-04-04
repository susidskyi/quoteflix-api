from fastapi import Depends

from app.core.presigned_url_service import PresignedURLService
from app.core.s3_service import S3Service


async def get_s3_service():
    return S3Service()


async def get_presigned_url_service(s3_service: S3Service = Depends(get_s3_service)):
    return PresignedURLService(s3_service)
