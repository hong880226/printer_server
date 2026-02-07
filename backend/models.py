"""
数据模型
"""
from datetime import datetime
from typing import Optional, List
from enum import Enum

class PrintJobStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PRINTING = "printing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class PrintJob:
    def __init__(
        self,
        job_id: str,
        filename: str,
        file_path: str,
        file_type: str,
        copies: int = 1,
        page_range: Optional[str] = None,
        status: PrintJobStatus = PrintJobStatus.PENDING,
        printer_name: str = None,
        created_at: datetime = None,
        completed_at: datetime = None,
        error_message: str = None
    ):
        self.job_id = job_id
        self.filename = filename
        self.file_path = file_path
        self.file_type = file_type
        self.copies = copies
        self.page_range = page_range
        self.status = status
        self.printer_name = printer_name
        self.created_at = created_at or datetime.now()
        self.completed_at = completed_at
        self.error_message = error_message
    
    def to_dict(self):
        return {
            'job_id': self.job_id,
            'filename': self.filename,
            'file_type': self.file_type,
            'copies': self.copies,
            'page_range': self.page_range,
            'status': self.status.value,
            'printer_name': self.printer_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message
        }

class Printer:
    def __init__(
        self,
        name: str,
        uri: str,
        device_id: str = None,
        state: str = "unknown",
        is_shared: bool = False,
        info: str = ""
    ):
        self.name = name
        self.uri = uri
        self.device_id = device_id
        self.state = state
        self.is_shared = is_shared
        self.info = info
    
    def to_dict(self):
        return {
            'name': self.name,
            'uri': self.uri,
            'device_id': self.device_id,
            'state': self.state,
            'is_shared': self.is_shared,
            'info': self.info
        }

class FileInfo:
    def __init__(
        self,
        filename: str,
        file_path: str,
        file_type: str,
        file_size: int,
        created_at: datetime,
        preview_path: str = None
    ):
        self.filename = filename
        self.file_path = file_path
        self.file_type = file_type
        self.file_size = file_size
        self.created_at = created_at
        self.preview_path = preview_path
    
    def to_dict(self):
        return {
            'filename': self.filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'created_at': self.created_at.isoformat(),
            'preview_path': self.preview_path
        }
