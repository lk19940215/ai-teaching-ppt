"""
PPT 生成历史记录模型
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()


class GenerationHistory(Base):
    """PPT 生成历史记录表"""
    __tablename__ = "generation_history"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 用户标识（支持多用户扩展，目前使用 session_id）
    session_id = Column(String(64), index=True, nullable=False)

    # 教学内容信息
    title = Column(String(255), nullable=False, comment="PPT 标题/主题")
    content_text = Column(JSON, nullable=True, comment="原始内容文本（JSON 格式存储）")

    # 配置信息
    grade = Column(String(32), nullable=False, comment="年级（如：1-9 年级）")
    subject = Column(String(32), nullable=False, default="general", comment="学科")
    style = Column(String(32), nullable=False, default="simple", comment="PPT 风格")
    slide_count = Column(Integer, nullable=True, comment="幻灯片页数")
    chapter = Column(String(255), nullable=True, comment="章节名称")

    # 生成结果
    file_name = Column(String(255), nullable=False, comment="生成的文件名")
    file_path = Column(String(512), nullable=False, comment="文件存储路径")
    ppt_content = Column(JSON, nullable=True, comment="生成的 PPT 内容结构（JSON）")

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, nullable=False, index=True)

    # 软删除标记
    is_deleted = Column(Boolean, default=False, nullable=False, index=True, comment="是否已删除")
    deleted_at = Column(DateTime, nullable=True, comment="删除时间")

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "title": self.title,
            "grade": self.grade,
            "subject": self.subject,
            "style": self.style,
            "slide_count": self.slide_count,
            "chapter": self.chapter,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_deleted": self.is_deleted,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
        }
