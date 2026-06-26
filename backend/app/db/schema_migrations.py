from typing import Dict

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


CANDIDATE_RESUME_COLUMNS: Dict[str, str] = {
    "major": "VARCHAR(128) NULL",
    "graduation_year": "VARCHAR(32) NULL",
    "work_years": "VARCHAR(64) NULL",
    "skills": "JSON NULL",
    "resume_summary": "TEXT NULL",
    "resume_parse_status": "VARCHAR(32) NULL",
    "latest_resume_id": "BIGINT NULL",
    "match_score": "FLOAT NULL",
    "match_level": "VARCHAR(32) NULL",
}


def ensure_resume_schema(engine: Engine) -> None:
    """create_all 不会给已有表自动加列；Demo 阶段用轻量 ALTER 保持旧库兼容。"""
    inspector = inspect(engine)
    if "candidates" not in inspector.get_table_names():
        return
    existing_columns = {column["name"] for column in inspector.get_columns("candidates")}
    missing_columns = {name: ddl for name, ddl in CANDIDATE_RESUME_COLUMNS.items() if name not in existing_columns}
    if not missing_columns:
        return

    with engine.begin() as connection:
        for column_name, column_ddl in missing_columns.items():
            connection.execute(text(f"ALTER TABLE candidates ADD COLUMN {column_name} {column_ddl}"))
