from sqlalchemy import Column, Integer, String, Boolean, DateTime, Time, Text, Date, create_engine
from sqlalchemy.sql import func
from database import Base


class Schedule(Base):
    """日程表"""
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    weekday = Column(Integer, nullable=False)  # 1-7, 周一为1
    remark = Column(Text, nullable=True)
    reminder_enabled = Column(Boolean, default=True)
    reminder_minutes = Column(Integer, default=10)
    is_recurring = Column(Boolean, default=False)  # 是否每周重复
    end_date = Column(Date, nullable=True)  # 重复截止日期
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ReminderLog(Base):
    """提醒日志表"""
    __tablename__ = "reminder_logs"

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, nullable=False)
    schedule_title = Column(String(100), nullable=False)
    scheduled_time = Column(DateTime(timezone=True), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="pending")  # pending, sent, failed
    channel = Column(String(20), nullable=True)  # dingtalk, lark
    response = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SystemConfig(Base):
    """系统配置表"""
    __tablename__ = "system_configs"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(50), unique=True, nullable=False)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
