from app.core.s3_service import S3Service


async def get_s3_service():
    return S3Service()
