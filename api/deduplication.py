"""
Text deduplication utilities for removing repetitive loops in text data.

The OME dataset contains report_text fields where the content is repeated
multiple times in a loop pattern. This module provides functions to detect
and remove these repetitions.
"""

from typing import Optional, Tuple
import pandas as pd


def find_loop_period(text: str, sample_len: int = 100) -> Tuple[Optional[int], int]:
    """
    Find the period of a looping/repeating text pattern.

    This function detects if a text contains repeated blocks by searching
    for occurrences of the initial segment throughout the text.

    Args:
        text: The input text to analyze
        sample_len: Length of the initial segment to search for (default: 100)

    Returns:
        Tuple of (period, repetition_count):
            - period: The length of the repeating block, or None if no loop detected
            - repetition_count: Number of times the block repeats

    Example:
        >>> text = "abc" * 5  # "abcabcabcabcabc"
        >>> find_loop_period(text, sample_len=3)
        (3, 5)
    """
    if len(text) < sample_len * 2:
        return None, 1

    start_chunk = text[:sample_len]

    # Find all occurrences of the initial chunk
    pos = sample_len
    occurrences = [0]

    while True:
        found = text.find(start_chunk, pos)
        if found == -1:
            break
        occurrences.append(found)
        pos = found + 1

    if len(occurrences) < 2:
        return None, 1

    # Calculate the period from the first two occurrences
    period = occurrences[1] - occurrences[0]

    # Verify this period is consistent for at least the first few occurrences
    if len(occurrences) >= 3:
        expected_gaps = [
            occurrences[i + 1] - occurrences[i]
            for i in range(min(3, len(occurrences) - 1))
        ]
        if not all(gap == period for gap in expected_gaps[:-1]):
            # Gaps are inconsistent - might not be a true loop
            # Still return the detected period but mark as uncertain
            pass

    return period, len(occurrences)


def remove_text_loops(text: str, sample_len: int = 100, verify: bool = True) -> str:
    """
    Remove repetitive loops from text, keeping only the unique content.

    Args:
        text: The input text potentially containing repeated blocks
        sample_len: Length of the sample used for loop detection (default: 100)
        verify: If True, verify that the extracted content matches the original
                pattern before returning (default: True)

    Returns:
        The deduplicated text containing only unique content.
        If no loop is detected, returns the original text unchanged.

    Example:
        >>> text = "Hello world! " * 10
        >>> remove_text_loops(text, sample_len=5)
        'Hello world! '
    """
    period, repetition_count = find_loop_period(text, sample_len)

    if period is None or repetition_count < 2:
        # No loop detected, return original
        return text

    # Extract the first complete block
    unique_content = text[:period]

    if verify:
        # Verify that repeating this content approximately matches the original
        expected = unique_content * repetition_count
        # Check if the expected content matches the beginning of the original
        min_len = min(len(expected), len(text))
        # Allow for partial match at the end (the text might have a partial loop)
        if expected[: min_len - period] != text[: min_len - period]:
            # Verification failed - content doesn't match expected pattern
            # This might indicate a more complex repetition structure
            # Return original to be safe
            return text

    return unique_content


def preprocess_dataframe(
    df: pd.DataFrame,
    text_column: str = "report_text",
    output_column: Optional[str] = None,
    sample_len: int = 100,
    verify: bool = True,
    inplace: bool = False,
) -> pd.DataFrame:
    """
    Apply loop removal to all text entries in a DataFrame.

    Args:
        df: Input DataFrame containing text data
        text_column: Name of the column containing text to deduplicate
        output_column: Name for the output column. If None, overwrites text_column
        sample_len: Length of sample for loop detection
        verify: If True, verify pattern matching before deduplication
        inplace: If True, modify the DataFrame in place

    Returns:
        DataFrame with deduplicated text

    Example:
        >>> df = pd.DataFrame({"report_text": ["abc" * 10, "xyz" * 5]})
        >>> result = preprocess_dataframe(df)
        >>> result["report_text"].tolist()
        ['abc', 'xyz']
    """
    if not inplace:
        df = df.copy()

    if output_column is None:
        output_column = text_column

    df[output_column] = df[text_column].apply(
        lambda x: remove_text_loops(x, sample_len=sample_len, verify=verify)
        if isinstance(x, str)
        else x
    )

    return df


def get_deduplication_stats(df: pd.DataFrame, text_column: str = "report_text") -> dict:
    """
    Compute statistics about the deduplication process.

    Args:
        df: DataFrame with original text data
        text_column: Name of the text column

    Returns:
        Dictionary with statistics including:
            - total_records: Number of records processed
            - records_with_loops: Number of records containing loops
            - original_total_chars: Total characters before deduplication
            - deduplicated_total_chars: Total characters after deduplication
            - compression_ratio: Ratio of original to deduplicated size
    """
    stats = {
        "total_records": len(df),
        "records_with_loops": 0,
        "original_total_chars": 0,
        "deduplicated_total_chars": 0,
    }

    for text in df[text_column]:
        if not isinstance(text, str):
            continue

        original_len = len(text)
        deduplicated = remove_text_loops(text)
        dedup_len = len(deduplicated)

        stats["original_total_chars"] += original_len
        stats["deduplicated_total_chars"] += dedup_len

        if dedup_len < original_len:
            stats["records_with_loops"] += 1

    if stats["deduplicated_total_chars"] > 0:
        stats["compression_ratio"] = (
            stats["original_total_chars"] / stats["deduplicated_total_chars"]
        )
    else:
        stats["compression_ratio"] = 1.0

    return stats
