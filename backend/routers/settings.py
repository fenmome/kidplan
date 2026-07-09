from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from models import SystemConfig, ReminderLog
from schemas import SettingsResponse, SettingsUpdate, TestWebhookRequest, ResponseModel, ReminderLogListResponse, ReminderLogResponse
from dependencies import get_current_user
from config import get_settings
from services.reminder import ReminderService

router = APIRouter(prefix="/settings", tags=["系统设置"])
settings_config = get_settings()

# 默认配置键
DEFAULT_REMINDER_MINUTES_KEY = "default_reminder_minutes"
MESSAGE_PREFIX_KEY = "message_prefix"
DINGTALK_WEBHOOK_KEY = "dingtalk_webhook"
LARK_WEBHOOK_KEY = "lark_webhook"


def get_or_create_config(db: Session, key: str, default_value: str = "") -> str:
    """获取或创建配置项"""
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if not config:
        config = SystemConfig(key=key, value=str(default_value))
        db.add(config)
        db.commit()
        db.refresh(config)
    return config.value


def set_config(db: Session, key: str, value: str):
    """设置配置项"""
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if config:
        config.value = value
    else:
        config = SystemConfig(key=key, value=value)
        db.add(config)
    db.commit()
    db.refresh(config)


@router.get("", response_model=ResponseModel)
def get_settings_api(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """获取系统配置"""
    default_minutes = get_or_create_config(
        db, DEFAULT_REMINDER_MINUTES_KEY,
        str(settings_config.DEFAULT_REMINDER_MINUTES)
    )
    prefix = get_or_create_config(db, MESSAGE_PREFIX_KEY, "")
    dingtalk = get_or_create_config(db, DINGTALK_WEBHOOK_KEY, "")
    lark = get_or_create_config(db, LARK_WEBHOOK_KEY, "")

    return ResponseModel(data={
        "default_reminder_minutes": int(default_minutes),
        "message_prefix": prefix if prefix else None,
        "dingtalk_webhook": dingtalk if dingtalk else None,
        "lark_webhook": lark if lark else None
    })


@router.put("", response_model=ResponseModel)
def update_settings(
    request: SettingsUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """更新系统配置"""
    if request.default_reminder_minutes is not None:
        set_config(db, DEFAULT_REMINDER_MINUTES_KEY, str(request.default_reminder_minutes))
    if request.message_prefix is not None:
        set_config(db, MESSAGE_PREFIX_KEY, request.message_prefix or "")
    if request.dingtalk_webhook is not None:
        set_config(db, DINGTALK_WEBHOOK_KEY, request.dingtalk_webhook or "")
    if request.lark_webhook is not None:
        set_config(db, LARK_WEBHOOK_KEY, request.lark_webhook or "")

    # 返回更新后的配置
    return get_settings_api(db, current_user)


@router.post("/test-webhook")
def test_webhook(
    request: TestWebhookRequest,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """测试webhook发送"""
    success, response = ReminderService.test_webhook(
        request.channel,
        request.webhook,
        request.message_prefix or ""
    )

    if success:
        return ResponseModel(data={
            "success": True,
            "message": "测试消息发送成功",
            "response": response
        })
    else:
        return ResponseModel(
            code=400,
            message="测试消息发送失败",
            data={
                "success": False,
                "message": "测试消息发送失败",
                "response": response
            }
        )


@router.get("/reminder-logs", response_model=ResponseModel)
def get_reminder_logs(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """获取提醒日志列表"""
    # 限制最大返回数量
    limit = min(limit, 100)

    # 查询总数
    total = db.query(ReminderLog).count()

    # 查询日志
    logs = db.query(ReminderLog).order_by(
        ReminderLog.created_at.desc()
    ).offset(offset).limit(limit).all()

    items = []
    for log in logs:
        items.append({
            "id": log.id,
            "schedule_id": log.schedule_id,
            "schedule_title": log.schedule_title,
            "scheduled_time": log.scheduled_time,
            "sent_at": log.sent_at,
            "status": log.status,
            "channel": log.channel,
            "response": log.response,
            "created_at": log.created_at
        })

    return ResponseModel(data={
        "total": total,
        "items": items
    })
