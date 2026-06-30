import zipfile
from pathlib import Path

GENERATED_DIR = Path(__file__).resolve().parents[2] / "generated_projects"


def zip_project(job_id: str) -> Path:
    """Zip the generated project directory and return the path to the ZIP file."""
    project_dir = GENERATED_DIR / job_id
    zip_path = GENERATED_DIR / f"{job_id}.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in project_dir.rglob("*"):
            if file_path.is_file():
                zf.write(file_path, file_path.relative_to(project_dir))

    return zip_path
