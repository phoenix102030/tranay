from typing import Any, Callable, Iterator, TypeVar

import polars as pl

T = TypeVar("T")


def map_to_records(
    items: list[T], map_fn: Callable[[T], list[dict[str, Any]]]
) -> list[dict[str, Any]]:
    """Map a list of objects to flat records."""
    return [record for item in items for record in map_fn(item)]


def create_dataframe(
    records: list[dict[str, Any]], schema: dict[str, Any]
) -> pl.DataFrame:
    """Create a Polars DataFrame from records with a schema."""
    return pl.DataFrame(records).cast(schema)  # type: ignore[arg-type]


def to_polars(
    items: list[T], map_fn: Callable[[T], list[dict[str, Any]]], schema: dict[str, Any]
) -> pl.DataFrame:
    """Convert a list of objects to a Polars DataFrame."""
    records = map_to_records(items, map_fn)
    return create_dataframe(records, schema)


def map_to_record_chunks(
    items: Iterator[T],
    map_fn: Callable[[T], list[dict[str, Any]]],
    chunk_size: int = 10000,
) -> Iterator[list[dict[str, Any]]]:
    """
    Map an iterator of items to chunks of records.

    Args:
        items: Iterator of objects to map
        map_fn: Function to convert each item to a list of records
        chunk_size: Number of records per chunk

    Yields:
        Chunks of records as lists of dictionaries
    """
    chunk = []
    for item in items:
        chunk.extend(map_fn(item))
        if len(chunk) >= chunk_size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def to_lazy_frame(
    records_iter: Iterator[list[dict[str, Any]]], schema: dict[str, Any]
) -> pl.LazyFrame:
    """
    Convert an iterator of record chunks to a Polars LazyFrame.

    Args:
        records_iter: Iterator yielding chunks of records
        schema: Polars schema for the resulting LazyFrame

    Returns:
        Polars LazyFrame
    """
    lazy_frames = [pl.LazyFrame(chunk, schema=schema) for chunk in records_iter]
    return (
        pl.concat(lazy_frames, rechunk=False)
        if lazy_frames
        else pl.LazyFrame(schema=schema)
    )


def stream_to_polars(
    items: Iterator[T],
    map_fn: Callable[[T], list[dict[str, Any]]],
    schema: dict[str, Any],
    chunk_size: int = 10000,
) -> pl.LazyFrame:
    """
    Transform a stream of items to a Polars LazyFrame.

    Args:
        items: Iterator of objects to transform
        map_fn: Function to map each item to a list of records
        schema: Polars schema for the resulting LazyFrame
        chunk_size: Number of records per chunk

    Returns:
        Polars LazyFrame
    """
    records_iter = map_to_record_chunks(items, map_fn, chunk_size)
    return to_lazy_frame(records_iter, schema)
