import zipfile
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def create_zip_archive(dir_path: str, output_zip_path: str) -> str:
    """Create a zip archive of a directory.

    Args:
        dir_path: Path of the directory to zip.
        output_zip_path: Target path for the output zip file.

    Returns:
        A status message indicating success.
    """
    try:
        source_dir = Path(dir_path).resolve()
        zip_file = Path(output_zip_path).resolve()
        zip_file.parent.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in source_dir.rglob("*"):
                if file_path.is_file():
                    zf.write(file_path, file_path.relative_to(source_dir))

        logger.info(f"Tool create_zip_archive: Created zip archive of {dir_path} at {output_zip_path}")
        return f"Successfully created zip archive at {output_zip_path}"
    except Exception as e:
        logger.error(f"Tool create_zip_archive failed: {str(e)}")
        raise RuntimeError(f"Failed to create zip archive: {str(e)}")
