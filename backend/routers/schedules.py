from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta, date
import re

from database import get_db
from models import Schedule
from schemas import (
    ScheduleCreate, ScheduleUpdate, ScheduleResponse,
    ScheduleCopyRequest, ScheduleCopyResponse, ResponseModel
)
from dependencies import get_current_user

router = APIRouter(prefix="/schedules", tags=["日程管理"])


def time_to_minutes(time_str: str) -> int:
    """将时间字符串转换为分钟数"""
    hour, minute = map(int, time_str.split(":"))
    return hour * 60 + minute


@router.get("", response_model=ResponseModel)
def get_schedules(
    week_offset: int = 0,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """获取指定周的日程列表"""
    schedules = db.query(Schedule).order_by(
        Schedule.weekday,
        Schedule.start_time
    ).all()

    result = []
    for s in schedules:
        result.append({
            "id": s.id,
            "title": s.title,
            "start_time": s.start_time.strftime("%H:%M") if s.start_time else "",
            "end_time": s.end_time.strftime("%H:%M") if s.end_time else "",
            "weekday": s.weekday,
            "remark": s.remark,
            "reminder_enabled": s.reminder_enabled,
            "reminder_minutes": s.reminder_minutes,
            "is_recurring": s.is_recurring,
            "end_date": s.end_date.strftime("%Y-%m-%d") if s.end_date else None,
            "created_at": s.created_at,
            "updated_at": s.updated_at
        })

    return ResponseModel(data=result)


@router.post("", response_model=ResponseModel)
def create_schedule(
    request: ScheduleCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """创建日程"""
    from datetime import time as dt_time

    # 解析时间
    start_parts = list(map(int, request.start_time.split(":")))
    end_parts = list(map(int, request.end_time.split(":")))

    # 解析截止日期
    end_date = None
    if request.end_date:
        end_date = datetime.strptime(request.end_date, "%Y-%m-%d").date()

    schedule = Schedule(
        title=request.title,
        start_time=dt_time(start_parts[0], start_parts[1]),
        end_time=dt_time(end_parts[0], end_parts[1]),
        weekday=request.weekday,
        remark=request.remark,
        reminder_enabled=request.reminder_enabled,
        reminder_minutes=request.reminder_minutes,
        is_recurring=request.is_recurring,
        end_date=end_date
    )

    db.add(schedule)
    db.commit()
    db.refresh(schedule)

    return ResponseModel(data={
        "id": schedule.id,
        "title": schedule.title,
        "start_time": schedule.start_time.strftime("%H:%M"),
        "end_time": schedule.end_time.strftime("%H:%M"),
        "weekday": schedule.weekday,
        "remark": schedule.remark,
        "reminder_enabled": schedule.reminder_enabled,
        "reminder_minutes": schedule.reminder_minutes,
        "is_recurring": schedule.is_recurring,
        "end_date": schedule.end_date.strftime("%Y-%m-%d") if schedule.end_date else None,
        "created_at": schedule.created_at,
        "updated_at": schedule.updated_at
    })


@router.put("/{schedule_id}", response_model=ResponseModel)
def update_schedule(
    schedule_id: int,
    request: ScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """更新日程"""
    from datetime import time as dt_time

    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="日程不存在")

    # 更新字段
    if request.title is not None:
        schedule.title = request.title
    if request.start_time is not None:
        start_parts = list(map(int, request.start_time.split(":")))
        schedule.start_time = dt_time(start_parts[0], start_parts[1])
    if request.end_time is not None:
        end_parts = list(map(int, request.end_time.split(":")))
        schedule.end_time = dt_time(end_parts[0], end_parts[1])
    if request.weekday is not None:
        schedule.weekday = request.weekday
    if request.remark is not None:
        schedule.remark = request.remark
    if request.reminder_enabled is not None:
        schedule.reminder_enabled = request.reminder_enabled
    if request.reminder_minutes is not None:
        schedule.reminder_minutes = request.reminder_minutes
    if request.is_recurring is not None:
        schedule.is_recurring = request.is_recurring
    if request.end_date is not None:
        schedule.end_date = datetime.strptime(request.end_date, "%Y-%m-%d").date()

    db.commit()
    db.refresh(schedule)

    return ResponseModel(data={
        "id": schedule.id,
        "title": schedule.title,
        "start_time": schedule.start_time.strftime("%H:%M"),
        "end_time": schedule.end_time.strftime("%H:%M"),
        "weekday": schedule.weekday,
        "remark": schedule.remark,
        "reminder_enabled": schedule.reminder_enabled,
        "reminder_minutes": schedule.reminder_minutes,
        "is_recurring": schedule.is_recurring,
        "end_date": schedule.end_date.strftime("%Y-%m-%d") if schedule.end_date else None,
        "created_at": schedule.created_at,
        "updated_at": schedule.updated_at
    })


@router.delete("/{schedule_id}", response_model=ResponseModel)
def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """删除日程"""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="日程不存在")

    db.delete(schedule)
    db.commit()

    return ResponseModel(data=None)


@router.post("/copy-to-next-week", response_model=ResponseModel)
def copy_to_next_week(
    request: ScheduleCopyRequest,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """复制本周日程到下周（只复制设置了每周重复的日程）"""
    from datetime import time as dt_time

    today = date.today()
    next_week_start = today + timedelta(days=(7 - today.weekday()) + 7 * request.target_week_offset)

    # 获取设置了每周重复且未过期的日程
    source_schedules = db.query(Schedule).filter(
        Schedule.is_recurring == True
    ).all()

    copied_count = 0
    for s in source_schedules:
        # 检查是否过期
        if s.end_date and s.end_date < next_week_start:
            continue

        # 创建新日程（相同时间，不同周）
        new_schedule = Schedule(
            title=s.title,
            start_time=s.start_time,
            end_time=s.end_time,
            weekday=s.weekday,
            remark=s.remark,
            reminder_enabled=s.reminder_enabled,
            reminder_minutes=s.reminder_minutes,
            is_recurring=False,  # 复制后的日程不自动重复
            end_date=s.end_date
        )
        db.add(new_schedule)
        copied_count += 1

    db.commit()

    return ResponseModel(data=ScheduleCopyResponse(copied_count=copied_count).model_dump())
