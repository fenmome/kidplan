import requests
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from database import SessionLocal
from models import Schedule, ReminderLog, SystemConfig
from config import get_settings

settings = get_settings()
scheduler = BackgroundScheduler()


class ReminderService:
    """提醒服务"""

    @staticmethod
    def get_config_value(db: Session, key: str, default: str = "") -> str:
        """获取配置值"""
        config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        return config.value if config and config.value else default

    @staticmethod
    def send_dingtalk(webhook: str, title: str, start_time: str, remark: str = "", prefix: str = "") -> tuple[bool, str]:
        """发送钉钉消息"""
        try:
            # 构建消息，添加前缀
            message_parts = []
            if prefix:
                message_parts.append(prefix)
            message_parts.append(f"【日程提醒】{title}")
            message_parts.append(f"开始时间: {start_time}")
            if remark:
                message_parts.append(f"备注: {remark}")
            message = "\n".join(message_parts)

            payload = {
                "msgtype": "text",
                "text": {
                    "content": message
                }
            }

            response = requests.post(
                webhook,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            result = response.json()

            if result.get("errcode") == 0:
                return True, json.dumps(result)
            else:
                return False, json.dumps(result)
        except Exception as e:
            return False, str(e)

    @staticmethod
    def send_lark(webhook: str, title: str, start_time: str, remark: str = "", prefix: str = "") -> tuple[bool, str]:
        """发送飞书消息"""
        try:
            # 构建消息，添加前缀
            message_parts = []
            if prefix:
                message_parts.append(prefix)
            message_parts.append(f"【日程提醒】{title}")
            message_parts.append(f"开始时间: {start_time}")
            if remark:
                message_parts.append(f"备注: {remark}")
            message = "\n".join(message_parts)

            payload = {
                "msg_type": "text",
                "content": {
                    "text": message
                }
            }

            response = requests.post(
                webhook,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            result = response.json()

            if result.get("code") == 0:
                return True, json.dumps(result)
            else:
                return False, json.dumps(result)
        except Exception as e:
            return False, str(e)

    @staticmethod
    def test_webhook(channel: str, webhook: str, prefix: str = "") -> tuple[bool, str]:
        """测试webhook发送"""
        test_title = "测试消息"
        test_time = datetime.now().strftime("%H:%M")
        test_remark = "这是一条测试消息，如果您收到说明配置正确"

        if channel == "dingtalk":
            return ReminderService.send_dingtalk(
                webhook, test_title, test_time, test_remark, prefix
            )
        elif channel == "lark":
            return ReminderService.send_lark(
                webhook, test_title, test_time, test_remark, prefix
            )
        else:
            return False, "不支持的渠道"

    @staticmethod
    def check_and_send_reminders():
        """检查并发送提醒"""
        db = SessionLocal()
        try:
            now = datetime.now()
            today = now.date()
            # 检测窗口：当前时间到1分钟后
            window_end = now + timedelta(minutes=1)

            # 获取所有启用提醒且未过期的日程
            schedules = db.query(Schedule).filter(
                Schedule.reminder_enabled == True
            ).all()

            for schedule in schedules:
                # 检查是否已过截止日期
                if schedule.end_date and schedule.end_date < today:
                    continue

                # 计算今天的提醒时间
                schedule_date = today + timedelta(days=(schedule.weekday - today.isoweekday()))

                # 组合日期和时间
                start_datetime = datetime.combine(schedule_date, schedule.start_time)
                remind_at = start_datetime - timedelta(minutes=schedule.reminder_minutes)

                # 检查提醒时间是否在窗口内
                if now <= remind_at <= window_end:
                    # 检查是否已发送
                    existing_log = db.query(ReminderLog).filter(
                        ReminderLog.schedule_id == schedule.id,
                        ReminderLog.scheduled_time == remind_at
                    ).first()

                    if not existing_log:
                        # 创建待发送日志
                        log = ReminderLog(
                            schedule_id=schedule.id,
                            schedule_title=schedule.title,
                            scheduled_time=remind_at,
                            status="pending"
                        )
                        db.add(log)
                        db.commit()
                        db.refresh(log)

                        # 获取配置
                        default_minutes = int(ReminderService.get_config_value(
                            db, "default_reminder_minutes", str(settings.DEFAULT_REMINDER_MINUTES)
                        ))
                        message_prefix = ReminderService.get_config_value(db, "message_prefix", "")
                        dingtalk_webhook = ReminderService.get_config_value(db, "dingtalk_webhook", "")
                        lark_webhook = ReminderService.get_config_value(db, "lark_webhook", "")

                        start_time_str = schedule.start_time.strftime("%H:%M")

                        # 发送钉钉
                        if dingtalk_webhook:
                            success, response = ReminderService.send_dingtalk(
                                dingtalk_webhook,
                                schedule.title,
                                start_time_str,
                                schedule.remark or "",
                                message_prefix
                            )
                            if success:
                                log.status = "sent"
                                log.channel = "dingtalk"
                            else:
                                log.status = "failed"
                            log.response = response
                            log.sent_at = datetime.now()
                            db.commit()

                        # 发送飞书
                        if lark_webhook:
                            success, response = ReminderService.send_lark(
                                lark_webhook,
                                schedule.title,
                                start_time_str,
                                schedule.remark or "",
                                message_prefix
                            )
                            if success:
                                log.status = "sent"
                                log.channel = "lark"
                            else:
                                log.status = "failed"
                            log.response = response
                            log.sent_at = datetime.now()
                            db.commit()

        finally:
            db.close()


def start_scheduler():
    """启动调度器"""
    # 添加每分钟执行的任务
    scheduler.add_job(
        ReminderService.check_and_send_reminders,
        trigger=IntervalTrigger(minutes=1),
        id="reminder_check",
        replace_existing=True
    )
    scheduler.start()
    print("提醒调度器已启动")


def stop_scheduler():
    """停止调度器"""
    scheduler.shutdown()
    print("提醒调度器已停止")
