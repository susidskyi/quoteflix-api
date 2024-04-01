import humanize
from fastapi import HTTPException, UploadFile, status


class FileValidator:
    @staticmethod
    def validate_file_size(file: UploadFile, max_size: int) -> None:
        if file.size is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size is required",
            )

        if file.size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File is too large. Max file size is: "
                + humanize.naturalsize(max_size),
            )

    @staticmethod
    def validate_file_type(file: UploadFile, supported_extensions: list) -> None:
        if file.filename is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File name is required",
            )

        file_extension = file.filename.split(".")[-1]

        if file_extension not in supported_extensions:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail="File type not supported. Supported types: "
                + ", ".join(supported_extensions),
            )

    @staticmethod
    def validate_file_name(file: UploadFile) -> None:
        if file.filename is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File name is required",
            )
