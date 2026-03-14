from dataclasses import dataclass
from typing import Optional

@dataclass
class DownloadItem:
    title: str
    tag: str
    description: str
    path: Optional[str]

    @property
    def is_completed(self) -> bool:
        # Thông tin description trống / rỗng khi hoàn tất (tùy Chrome version có thể khác)
        return (self.description is None) or (self.description.strip() == "")
