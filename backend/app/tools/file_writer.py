from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)

def write_file(filepath: str, content: str) -> str:
    """Write text content to a file, automatically creating parent directories.

    Args:
        filepath: Path to the target file.
        content: Content string to write to the file.

    Returns:
        A status message indicating success.
    """
    try:
        path = Path(filepath).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        logger.info(f"Tool write_file: Wrote {len(content)} characters to {filepath}")
        return f"Successfully wrote file to {filepath}"
    except Exception as e:
        logger.error(f"Tool write_file failed for {filepath}: {str(e)}")
        raise RuntimeError(f"Failed to write file {filepath}: {str(e)}")
