import typing

from pydantic import BaseModel

from app.core.models import CoreModel
from app.s3.s3_service import S3Service

CM = typing.TypeVar("CM", bound=CoreModel | BaseModel)


class PresignedURLService:
    def __init__(self, s3_service: S3Service) -> None:
        self.s3_service = s3_service

    async def update_s3_urls_for_models(
        self,
        items: typing.Sequence[CM],
        key: str,
    ) -> typing.Sequence[CM]:
        for item in items:
            await self.update_s3_url_for_model(item, key)

        return items

    async def update_s3_url_for_model(self, item: CM, key: str) -> CM:
        s3_key = getattr(item, key, None)

        if s3_key is not None:
            pre_signed_url = await self.s3_service.get_presigned_url(s3_key)
            setattr(item, key, pre_signed_url)

        return item
