import os
import json
from pathlib import Path

GENERATED_DIR = Path(__file__).resolve().parents[2] / "generated_projects"


def write_project_files(job_id: str, state: dict):
    """Write generated code files to disk under generated_projects/{job_id}/."""
    project_dir = GENERATED_DIR / job_id
    project_dir.mkdir(parents=True, exist_ok=True)

    backend_code = state.get("backend_code", {})
    frontend_code = state.get("frontend_code", {})
    deployment = state.get("deployment", {})
    documentation = state.get("documentation", {})
    db = state.get("database_schema", {})

    # Backend files
    be_dir = project_dir / "backend"
    be_dir.mkdir(exist_ok=True)
    if backend_code.get("main_file"):
        (be_dir / "main.py").write_text(backend_code["main_file"], encoding="utf-8")
    if backend_code.get("models_code"):
        (be_dir / "models.py").write_text(backend_code["models_code"], encoding="utf-8")
    if backend_code.get("routes_code"):
        (be_dir / "routes.py").write_text(backend_code["routes_code"], encoding="utf-8")
    if backend_code.get("services_code"):
        (be_dir / "services.py").write_text(backend_code["services_code"], encoding="utf-8")
    if backend_code.get("requirements_txt"):
        (be_dir / "requirements.txt").write_text(backend_code["requirements_txt"], encoding="utf-8")
    if backend_code.get("dockerfile"):
        (be_dir / "Dockerfile").write_text(backend_code["dockerfile"], encoding="utf-8")

    # Frontend files
    fe_dir = project_dir / "frontend"
    fe_dir.mkdir(exist_ok=True)
    if frontend_code.get("main_app_code"):
        (fe_dir / "App.jsx").write_text(frontend_code["main_app_code"], encoding="utf-8")
    if frontend_code.get("api_client_code"):
        (fe_dir / "api.js").write_text(frontend_code["api_client_code"], encoding="utf-8")
    if frontend_code.get("package_json"):
        (fe_dir / "package.json").write_text(frontend_code["package_json"], encoding="utf-8")
    if frontend_code.get("dockerfile"):
        (fe_dir / "Dockerfile").write_text(frontend_code["dockerfile"], encoding="utf-8")
    if frontend_code.get("styles_code"):
        (fe_dir / "index.css").write_text(frontend_code["styles_code"], encoding="utf-8")

    # Database migration
    db_dir = project_dir / "database"
    db_dir.mkdir(exist_ok=True)
    if db.get("migration_sql"):
        (db_dir / "migration.sql").write_text(db["migration_sql"], encoding="utf-8")

    # Deployment files
    docker_dir = project_dir / "docker"
    docker_dir.mkdir(exist_ok=True)
    if deployment.get("docker_compose_yml"):
        (docker_dir / "docker-compose.yml").write_text(deployment["docker_compose_yml"], encoding="utf-8")
    if deployment.get("nginx_conf"):
        (docker_dir / "nginx.conf").write_text(deployment["nginx_conf"], encoding="utf-8")
    if deployment.get("env_example"):
        (project_dir / ".env.example").write_text(deployment["env_example"], encoding="utf-8")
    if deployment.get("ci_cd_yml"):
        ci_dir = project_dir / ".github" / "workflows"
        ci_dir.mkdir(parents=True, exist_ok=True)
        (ci_dir / "ci.yml").write_text(deployment["ci_cd_yml"], encoding="utf-8")

    # Documentation
    docs_dir = project_dir / "docs"
    docs_dir.mkdir(exist_ok=True)
    if documentation.get("readme_md"):
        (project_dir / "README.md").write_text(documentation["readme_md"], encoding="utf-8")
    if documentation.get("api_docs_md"):
        (docs_dir / "api.md").write_text(documentation["api_docs_md"], encoding="utf-8")
    if documentation.get("architecture_md"):
        (docs_dir / "architecture.md").write_text(documentation["architecture_md"], encoding="utf-8")
    if documentation.get("setup_guide_md"):
        (docs_dir / "setup.md").write_text(documentation["setup_guide_md"], encoding="utf-8")

    # Save full state as JSON
    (project_dir / "state.json").write_text(json.dumps(state, indent=2), encoding="utf-8")

    return str(project_dir)
