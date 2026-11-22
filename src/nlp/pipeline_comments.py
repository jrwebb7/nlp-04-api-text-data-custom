# Customized by James Webb (2026-11)

"""Retrieve, validate, and summarize JSONPlaceholder comments."""

from typing import Any

from datafun_toolkit.logger import get_logger
import polars as pl

from nlp.config import PROCESSED_PATH, RAW_PATH
from nlp.stage01_extract import run_extract
from nlp.stage04_load import run_load

API_URL = "https://jsonplaceholder.typicode.com/comments"
REQUEST_HEADERS = {
    "User-Agent": "nlp-04-comments/1.0",
    "Accept": "application/json",
}
RAW_JSON_PATH = RAW_PATH / "comments_raw.json"
PROCESSED_CSV_PATH = PROCESSED_PATH / "comments_processed.csv"


def validate_comments(data: Any) -> list[dict[str, Any]]:
    """Check that every comment has the required fields and types."""
    if not isinstance(data, list) or not data:
        raise ValueError("Expected a nonempty list of comments.")

    required_fields = {"id": int, "postId": int, "name": str, "body": str}
    for index, record in enumerate(data):
        if not isinstance(record, dict):
            raise TypeError(f"Comment at index {index} must be an object.")
        for field, expected_type in required_fields.items():
            if type(record.get(field)) is not expected_type:
                raise ValueError(
                    f"Comment at index {index}: {field} must be "
                    f"{expected_type.__name__}."
                )

    return data


def transform_comments(records: list[dict[str, Any]]) -> pl.DataFrame:
    """Select analysis fields and calculate comment body word counts."""
    return pl.DataFrame(records).select(
        pl.col("id").alias("comment_id"),
        pl.col("postId").alias("post_id"),
        pl.col("name").alias("comment_name"),
        pl.col("body"),
        pl.col("body").str.count_matches(r"\S+").alias("body_word_count"),
    )


def main() -> None:
    """Run the comments pipeline from the repository root."""
    logger = get_logger("CI", level="INFO")
    RAW_PATH.mkdir(parents=True, exist_ok=True)
    PROCESSED_PATH.mkdir(parents=True, exist_ok=True)

    raw = run_extract(API_URL, REQUEST_HEADERS, RAW_JSON_PATH, logger)
    comments = validate_comments(raw)
    table = transform_comments(comments)
    run_load(table, PROCESSED_CSV_PATH, logger)
    logger.info("Comments pipeline completed: %s records.", table.height)


if __name__ == "__main__":
    main()
