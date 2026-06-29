from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ScanOptions:
    folders: list
    include_hidden: bool       = False
    min_file_size_kb: int      = 1
    max_file_size_mb: int      = 0
    file_type_filter: list     = field(default_factory=list)
    exclude_folders: list      = field(default_factory=list)
    enable_image_similarity: bool = False
    similarity_threshold: int  = 90
    scan_profile_name: str     = ""

    def to_dict(self) -> dict:
        return {
            "include_hidden":         self.include_hidden,
            "min_file_size_kb":       self.min_file_size_kb,
            "max_file_size_mb":       self.max_file_size_mb,
            "file_type_filter":       self.file_type_filter,
            "exclude_folders":        self.exclude_folders,
            "enable_image_similarity":self.enable_image_similarity,
            "similarity_threshold":   self.similarity_threshold,
            "scan_profile_name":      self.scan_profile_name,
        }

    @classmethod
    def from_dict(cls, folders: list, d: dict) -> "ScanOptions":
        return cls(
            folders=folders,
            include_hidden=d.get("include_hidden", False),
            min_file_size_kb=d.get("min_file_size_kb", 1),
            max_file_size_mb=d.get("max_file_size_mb", 0),
            file_type_filter=d.get("file_type_filter", []),
            exclude_folders=d.get("exclude_folders", []),
            enable_image_similarity=d.get("enable_image_similarity", False),
            similarity_threshold=d.get("similarity_threshold", 90),
            scan_profile_name=d.get("scan_profile_name", ""),
        )


@dataclass
class FileInfo:
    path: str
    name: str
    size_bytes: int
    modified_at: datetime
    extension: str
    thumbnail: bytes | None       = None
    marked_for_delete: bool       = False
    is_recommended_keep: bool     = False


@dataclass
class DuplicateGroup:
    hash_value: str
    files: list           # list[FileInfo]
    total_size_bytes: int
    wasted_bytes: int
    group_type: str       # "exact" | "similar_image"
    similarity_score: float = 1.0


@dataclass
class ScanProfile:
    id: int
    name: str
    folders: list
    options: ScanOptions
    created_at: str
    updated_at: str


@dataclass
class TrashItem:
    id: int
    original_path: str
    trash_path: str
    file_name: str
    size_bytes: int
    deleted_at: str
    scan_history_id: int | None
