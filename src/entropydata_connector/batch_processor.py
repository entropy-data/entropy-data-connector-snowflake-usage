"""Batch processor for handling large numbers of traces."""

from typing import Iterator, TypeVar, List

T = TypeVar('T')


class BatchProcessor:
    """Processes items in batches."""

    @staticmethod
    def batch(items: Iterator[T], batch_size: int) -> Iterator[List[T]]:
        """Batch items into fixed-size chunks.

        Args:
            items: Iterator of items to batch
            batch_size: Maximum size of each batch

        Yields:
            Lists of items up to batch_size
        """
        batch = []
        for item in items:
            batch.append(item)
            if len(batch) >= batch_size:
                yield batch
                batch = []

        # Yield remaining items
        if batch:
            yield batch

    @staticmethod
    def batch_list(items: List[T], batch_size: int) -> Iterator[List[T]]:
        """Batch a list into fixed-size chunks.

        Args:
            items: List of items to batch
            batch_size: Maximum size of each batch

        Yields:
            Lists of items up to batch_size
        """
        for i in range(0, len(items), batch_size):
            yield items[i:i + batch_size]
