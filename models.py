from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Student:
    id: str
    telegram_id: int
    first_name: str
    last_name: str = ""
    nfc_id: Optional[str] = None
    registration_date: datetime = None
    is_active: bool = True
    
    def __post_init__(self):
        if self.registration_date is None:
            self.registration_date = datetime.now()

@dataclass
class AttendanceRecord:
    id: int
    student_id: str
    timestamp: datetime
    method: str
    terminal_id: str
    confidence: float = 1.0
