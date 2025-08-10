from pydantic import BaseModel, Field
from typing import Optional, TypeVar, Generic

T = TypeVar('T')

class Response(BaseModel, Generic[T]):
    success: bool = Field(True, description="操作是否成功")
    data: Optional[T] = Field(None, description="响应数据")
    message: Optional[str] = Field(None, description="响应消息")

class SuccessResponse(BaseModel):
    success: bool
    message: Optional[str] = None
