from pydantic import BaseModel, Field, field_validator
from typing import Optional, Any
from datetime import time, datetime


# ========== 通用响应模型 ==========
class ResponseModel(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[Any] = None


# ========== 认证相关 ==========
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


# ========== 日程相关 ==========
class ScheduleBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    start_time: str = Field(..., pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    end_time: str = Field(..., pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    weekday: int = Field(..., ge=1, le=7)
    remark: Optional[str] = Field(None, max_length=500)
    reminder_enabled: bool = True
    reminder_minutes: int = Field(default=10, ge=1, le=120)
    is_recurring: bool = False  # 是否每周重复
    end_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")  # 截止日期 YYYY-MM-DD

    @field_validator('end_time')
    @classmethod
    def validate_end_time(cls, v: str, info) -> str:
        values = info.data
        if 'start_time' in values:
            start = values['start_time']
            if v <= start:
                raise ValueError('结束时间必须晚于开始时间')
        return v


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleUpdate(ScheduleBase):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    start_time: Optional[str] = Field(None, pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    end_time: Optional[str] = Field(None, pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    weekday: Optional[int] = Field(None, ge=1, le=7)
    is_recurring: Optional[bool] = None
    end_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")


class ScheduleResponse(BaseModel):
    id: int
    title: str
    start_time: str
    end_time: str
    weekday: int
    remark: Optional[str]
    reminder_enabled: bool
    reminder_minutes: int
    is_recurring: bool
    end_date: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ScheduleCopyRequest(BaseModel):
    source_week_offset: int = 0
    target_week_offset: int = 1


class ScheduleCopyResponse(BaseModel):
    copied_count: int


# ========== 配置相关 ==========
class SettingsResponse(BaseModel):
    default_reminder_minutes: int
    message_prefix: Optional[str]
    dingtalk_webhook: Optional[str]
    lark_webhook: Optional[str]


class SettingsUpdate(BaseModel):
    default_reminder_minutes: Optional[int] = Field(None, ge=1, le=120)
    message_prefix: Optional[str] = Field(None, max_length=100)
    dingtalk_webhook: Optional[str] = Field(None, max_length=500)
    lark_webhook: Optional[str] = Field(None, max_length=500)


class TestWebhookRequest(BaseModel):
    channel: str = Field(..., pattern="^(dingtalk|lark)$")
    webhook: str = Field(..., max_length=500)
    message_prefix: Optional[str] = Field(None, max_length=100)


class TestWebhookResponse(BaseModel):
    success: bool
    message: str
    response: Optional[str] = None


# ========== 日志相关 ==========
class ReminderLogResponse(BaseModel):
    id: int
    schedule_id: int
    schedule_title: str
    scheduled_time: datetime
    sent_at: Optional[datetime]
    status: str
    channel: Optional[str]
    response: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ReminderLogListResponse(BaseModel):
    total: int
    items: list[ReminderLogResponse]
