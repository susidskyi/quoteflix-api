import io

import aioboto3
import pytest

from app.s3.s3_service import S3Service


@pytest.mark.asyncio()
class TestS3Service:
    async def test_get_all_objects_in_folder_empty(self, s3_service: S3Service):
        objects = await s3_service.get_all_objects_in_folder("non-existed-prefix")

        assert len(objects) == 0

    async def test_get_all_objects_in_folder_not_empty(
        self,
        s3_session: aioboto3.Session,
        s3_service: S3Service,
        created_file_in_s3: None,
        movie_in_s3_prefix: str,
        file_in_s3_key: str,
    ):
        objects = await s3_service.get_all_objects_in_folder(movie_in_s3_prefix)

        assert len(objects) == 1
        assert objects[0] == file_in_s3_key

    async def test_delete_object_exists(
        self,
        s3_service: S3Service,
        created_file_in_s3: None,
        movie_in_s3_prefix: str,
        file_in_s3_key: str,
    ):
        objects = await s3_service.get_all_objects_in_folder(movie_in_s3_prefix)
        assert len(objects) == 1

        await s3_service.delete_object(file_in_s3_key)

        objects = await s3_service.get_all_objects_in_folder(movie_in_s3_prefix)
        assert len(objects) == 0

    async def test_delete_object_does_not_exist(
        self,
        s3_service: S3Service,
        movie_in_s3_prefix: str,
        file_in_s3_key: str,
    ):
        objects = await s3_service.get_all_objects_in_folder(movie_in_s3_prefix)
        assert len(objects) == 0

        await s3_service.delete_objects(file_in_s3_key)

        objects = await s3_service.get_all_objects_in_folder(movie_in_s3_prefix)
        assert len(objects) == 0

    async def test_delete_objects_exists(
        self,
        s3_service: S3Service,
        created_file_in_s3: None,
        movie_in_s3_prefix: str,
        file_in_s3_key: str,
    ):
        objects = await s3_service.get_all_objects_in_folder(movie_in_s3_prefix)
        assert len(objects) == 1

        await s3_service.delete_objects([file_in_s3_key])

        objects = await s3_service.get_all_objects_in_folder(movie_in_s3_prefix)

        assert len(objects) == 0

    async def test_delete_objects_does_not_exist(
        self,
        s3_service: S3Service,
        movie_in_s3_prefix: str,
        file_in_s3_key: str,
    ):
        objects = await s3_service.get_all_objects_in_folder(movie_in_s3_prefix)
        assert len(objects) == 0

        await s3_service.delete_objects([file_in_s3_key])

        objects = await s3_service.get_all_objects_in_folder(movie_in_s3_prefix)
        assert len(objects) == 0

    async def test_upload_fileobj(
        self,
        s3_service: S3Service,
        file_in_s3_key: str,
        movie_in_s3_prefix: str,
    ):
        fileobj = io.BytesIO(b"test")
        await s3_service.upload_fileobj(fileobj, file_in_s3_key)

        objects = await s3_service.get_all_objects_in_folder(movie_in_s3_prefix)
        assert len(objects) == 1

    async def test_delete_folder_is_empty(
        self,
        s3_service: S3Service,
        movie_in_s3_prefix: str,
    ):
        await s3_service.delete_folder(movie_in_s3_prefix)

        objects = await s3_service.get_all_objects_in_folder(movie_in_s3_prefix)
        assert len(objects) == 0

    async def test_delete_folder_is_not_empty(
        self,
        s3_service: S3Service,
        created_file_in_s3: None,
        movie_in_s3_prefix: str,
    ):
        objects = await s3_service.get_all_objects_in_folder(movie_in_s3_prefix)
        assert len(objects) == 1

        await s3_service.delete_folder(movie_in_s3_prefix)

        objects = await s3_service.get_all_objects_in_folder(movie_in_s3_prefix)
        assert len(objects) == 0

    async def test_get_presigned_url(self, s3_service: S3Service, file_in_s3_key: str):
        url = await s3_service.get_presigned_url(file_in_s3_key)

        assert "http://motoserver:5000" in url
        assert file_in_s3_key in url
