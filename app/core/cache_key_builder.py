import hashlib
import typing
from typing import Callable, Optional
from urllib.request import Request

from fastapi import Response
from fastapi_cache import FastAPICache


def key_builder_phrase_search_by_text(
    func: Callable,  # type: ignore
    namespace: Optional[str] = "",
    request: Optional[Request] = None,
    response: Optional[Response] = None,
    args: Optional[tuple] = None,  # type: ignore
    kwargs: Optional[dict] = None,  # type: ignore
) -> str:
    """
    Custom key builder because of issue: https://github.com/long2ice/fastapi-cache/issues/279
    """

    prefix = f"{FastAPICache.get_prefix()}:{namespace}:"
    search_text = kwargs.get("search_text", "").strip()  # type: ignore
    page = kwargs.get("page")  # type: ignore

    cache_key = hashlib.blake2b(
        f"{func.__module__}:{func.__name__}:{args}:{search_text}:{page}".encode(),
    ).hexdigest()

    return f"{prefix}:{cache_key}"
