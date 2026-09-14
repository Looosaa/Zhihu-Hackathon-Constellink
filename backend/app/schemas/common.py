from typing import Generic, TypeVar

from pydantic import BaseModel

from app.domain.enums import ExecutionMode

DataT = TypeVar("DataT")


class ResponseMeta(BaseModel):
    request_id: str
    execution_mode: ExecutionMode | None = None
    prompt_version: str | None = None


class ApiResponse(BaseModel, Generic[DataT]):
    data: DataT
    meta: ResponseMeta

