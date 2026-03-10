"""
历史记录 CRUD 操作
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_
from typing import Optional, List
from datetime import datetime
import uuid

from .history import GenerationHistory


def add_generation_record(
    db: Session,
    session_id: str,
    title: str,
    grade: str,
    subject: str,
    style: str,
    file_name: str,
    file_path: str,
    content_text: Optional[dict] = None,
    slide_count: Optional[int] = None,
    chapter: Optional[str] = None,
    ppt_content: Optional[dict] = None,
) -> GenerationHistory:
    """添加生成历史记录"""
    record = GenerationHistory(
        session_id=session_id,
        title=title,
        content_text=content_text,
        grade=grade,
        subject=subject,
        style=style,
        slide_count=slide_count,
        chapter=chapter,
        file_name=file_name,
        file_path=file_path,
        ppt_content=ppt_content,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_history_record(db: Session, record_id: int) -> Optional[GenerationHistory]:
    """获取单条历史记录"""
    return db.query(GenerationHistory).filter(GenerationHistory.id == record_id).first()


def delete_history_record(db: Session, record_id: int, session_id: str) -> bool:
    """删除历史记录（只能删除自己的记录）- 物理删除，保留用于兼容"""
    record = (
        db.query(GenerationHistory)
        .filter(GenerationHistory.id == record_id, GenerationHistory.session_id == session_id)
        .first()
    )
    if record:
        db.delete(record)
        db.commit()
        return True
    return False


def get_history_count(db: Session, session_id: str) -> int:
    """获取历史记录总数"""
    return db.query(GenerationHistory).filter(GenerationHistory.session_id == session_id).count()


def regenerate_from_history(
    db: Session,
    record_id: int,
    session_id: str,
    new_file_name: str,
    new_file_path: str,
    new_ppt_content: Optional[dict] = None,
) -> Optional[GenerationHistory]:
    """基于历史记录重新生成（创建新记录）"""
    record = (
        db.query(GenerationHistory)
        .filter(GenerationHistory.id == record_id, GenerationHistory.session_id == session_id)
        .first()
    )
    if not record:
        return None

    # 创建新记录，复用原有配置
    new_record = GenerationHistory(
        session_id=session_id,
        title=record.title,
        content_text=record.content_text,
        grade=record.grade,
        subject=record.subject,
        style=record.style,
        slide_count=record.slide_count,
        chapter=record.chapter,
        file_name=new_file_name,
        file_path=new_file_path,
        ppt_content=new_ppt_content,
    )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    return new_record


def soft_delete_history_record(db: Session, record_id: int, session_id: str) -> bool:
    """软删除历史记录（标记删除但保留数据）"""
    record = (
        db.query(GenerationHistory)
        .filter(GenerationHistory.id == record_id, GenerationHistory.session_id == session_id)
        .first()
    )
    if record:
        record.is_deleted = True
        record.deleted_at = datetime.now()
        db.commit()
        return True
    return False


def restore_history_record(db: Session, record_id: int, session_id: str) -> bool:
    """恢复已删除的历史记录"""
    record = (
        db.query(GenerationHistory)
        .filter(GenerationHistory.id == record_id, GenerationHistory.session_id == session_id)
        .first()
    )
    if record:
        record.is_deleted = False
        record.deleted_at = None
        db.commit()
        return True
    return False


def get_history_by_session(
    db: Session,
    session_id: str,
    limit: int = 20,
    offset: int = 0,
    include_deleted: bool = False,
) -> List[GenerationHistory]:
    """获取指定 session 的生成历史（默认排除已删除）"""
    query = db.query(GenerationHistory).filter(GenerationHistory.session_id == session_id)

    if not include_deleted:
        query = query.filter(GenerationHistory.is_deleted == False)

    return (
        query.order_by(desc(GenerationHistory.created_at))
        .offset(offset)
        .limit(limit)
        .all()
    )


def search_history(
    db: Session,
    session_id: str,
    keyword: Optional[str] = None,
    grade: Optional[str] = None,
    subject: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    include_deleted: bool = False,
) -> List[GenerationHistory]:
    """搜索历史记录（默认排除已删除）"""
    query = db.query(GenerationHistory).filter(GenerationHistory.session_id == session_id)

    # 默认排除已删除记录
    if not include_deleted:
        query = query.filter(GenerationHistory.is_deleted == False)

    if keyword:
        query = query.filter(
            or_(
                GenerationHistory.title.contains(keyword),
                GenerationHistory.chapter.contains(keyword),
            )
        )

    if grade:
        query = query.filter(GenerationHistory.grade == grade)

    if subject:
        query = query.filter(GenerationHistory.subject == subject)

    return query.order_by(desc(GenerationHistory.created_at)).offset(offset).limit(limit).all()


def get_deleted_history(
    db: Session,
    session_id: str,
    limit: int = 20,
    offset: int = 0,
) -> List[GenerationHistory]:
    """获取已删除的历史记录"""
    return (
        db.query(GenerationHistory)
        .filter(GenerationHistory.session_id == session_id, GenerationHistory.is_deleted == True)
        .order_by(desc(GenerationHistory.deleted_at))
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_deleted_count(db: Session, session_id: str) -> int:
    """获取已删除记录的数量"""
    return (
        db.query(GenerationHistory)
        .filter(GenerationHistory.session_id == session_id, GenerationHistory.is_deleted == True)
        .count()
    )
