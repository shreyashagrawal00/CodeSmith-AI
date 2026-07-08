import os
import json
import re
from pathlib import Path

GENERATED_DIR = Path(__file__).resolve().parents[2] / "generated_projects"

# Matches e.g. `import './styles.css'` or `import "./App.css";` inside
# AI-generated App.jsx -- used to catch cases where the model names its
# stylesheet import something other than index.css (see write_project_files).
_CSS_IMPORT_PATTERN = re.compile(r"""import\s+['"]\.\/([\w.-]+\.css)['"]""")


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

    # Use whatever filename/extension the AI actually specified for the
    # main file (e.g. 'main.py' for FastAPI, 'index.js' for Express) --
    # previously this was hardcoded to main.py/requirements.txt/models.py/
    # etc. regardless of the requested language, so asking for a Node.js
    # backend still produced Python filenames (and a broken preview, since
    # preview_service tried to `pip install` a package.json).
    main_file_name = backend_code.get("main_file_name") or "main.py"
    ext = Path(main_file_name).suffix or ".py"

    if backend_code.get("main_file"):
        (be_dir / main_file_name).write_text(backend_code["main_file"], encoding="utf-8")
    if backend_code.get("models_code"):
        (be_dir / f"models{ext}").write_text(backend_code["models_code"], encoding="utf-8")
    if backend_code.get("routes_code"):
        (be_dir / f"routes{ext}").write_text(backend_code["routes_code"], encoding="utf-8")
    if backend_code.get("services_code"):
        (be_dir / f"services{ext}").write_text(backend_code["services_code"], encoding="utf-8")
    dependency_manifest_name = backend_code.get("dependency_manifest_name") or "requirements.txt"
    if backend_code.get("dependency_manifest"):
        (be_dir / dependency_manifest_name).write_text(backend_code["dependency_manifest"], encoding="utf-8")
    if backend_code.get("dockerfile"):
        (be_dir / "Dockerfile").write_text(backend_code["dockerfile"], encoding="utf-8")

    # Frontend files
    fe_dir = project_dir / "frontend"
    fe_dir.mkdir(exist_ok=True)
    src_dir = fe_dir / "src"
    src_dir.mkdir(exist_ok=True)

    if frontend_code.get("main_app_code"):
        (src_dir / "App.jsx").write_text(frontend_code["main_app_code"], encoding="utf-8")
    if frontend_code.get("api_client_code"):
        (src_dir / "api.js").write_text(frontend_code["api_client_code"], encoding="utf-8")
    if frontend_code.get("package_json"):
        (fe_dir / "package.json").write_text(frontend_code["package_json"], encoding="utf-8")
    if frontend_code.get("dockerfile"):
        (fe_dir / "Dockerfile").write_text(frontend_code["dockerfile"], encoding="utf-8")
    if frontend_code.get("styles_code"):
        (src_dir / "index.css").write_text(frontend_code["styles_code"], encoding="utf-8")

        # The AI is free to name its own CSS import anything (e.g.
        # 'styles.css', 'App.css') -- but we always write our own
        # generated main.jsx to import 'index.css'. If App.jsx's own
        # import doesn't match index.css, the build fails with
        # "Could not resolve './whatever.css'". Detect the actual import
        # and write a copy under that name too, so either resolves.
        main_app_code = frontend_code.get("main_app_code") or ""
        match = _CSS_IMPORT_PATTERN.search(main_app_code)
        if match and match.group(1) != "index.css":
            (src_dir / match.group(1)).write_text(frontend_code["styles_code"], encoding="utf-8")

    # Individual React components (previously silently dropped — the AI
    # returns these as a list of {filename, code} objects).
    components_code = frontend_code.get("components_code") or []
    if components_code:
        components_dir = src_dir / "components"
        components_dir.mkdir(exist_ok=True)
        for component in components_code:
            filename = component.get("filename") if isinstance(component, dict) else None
            code = component.get("code") if isinstance(component, dict) else None
            if not filename or not code:
                continue
            # Guard against path traversal / nested paths in filenames.
            safe_name = Path(filename).name or "component.jsx"
            (components_dir / safe_name).write_text(code, encoding="utf-8")

    # Static Vite boilerplate: the LLM-generated FrontendCode schema only
    # produces App.jsx/api.js/styles/package.json — it never produces an
    # index.html or a main.jsx entry point, so `npm run dev` has nothing to
    # actually serve. These two files are effectively identical for any
    # Vite + React app, so we write them directly rather than depending on
    # the model to generate boilerplate correctly every time.
    if frontend_code.get("main_app_code") and not (fe_dir / "index.html").exists():
        (fe_dir / "index.html").write_text(
            '<!doctype html>\n'
            '<html lang="en">\n'
            '  <head>\n'
            '    <meta charset="UTF-8" />\n'
            '    <meta name="viewport" content="width=device-width, initial-scale=1.0" />\n'
            '    <title>CodeSmith AI Generated App</title>\n'
            '  </head>\n'
            '  <body>\n'
            '    <div id="root"></div>\n'
            '    <script type="module" src="/src/main.jsx"></script>\n'
            '  </body>\n'
            '</html>\n',
            encoding="utf-8",
        )
    if frontend_code.get("main_app_code") and not (src_dir / "main.jsx").exists():
        has_css = bool(frontend_code.get("styles_code"))
        (src_dir / "main.jsx").write_text(
            "import React from 'react';\n"
            "import ReactDOM from 'react-dom/client';\n"
            "import App from './App.jsx';\n"
            + ("import './index.css';\n" if has_css else "")
            + "\n"
            "ReactDOM.createRoot(document.getElementById('root')).render(\n"
            "  <React.StrictMode>\n"
            "    <App />\n"
            "  </React.StrictMode>\n"
            ");\n",
            encoding="utf-8",
        )
    if frontend_code.get("main_app_code") and not (fe_dir / "vite.config.js").exists():
        (fe_dir / "vite.config.js").write_text(
            "import { defineConfig } from 'vite';\n"
            "import react from '@vitejs/plugin-react';\n\n"
            "export default defineConfig({\n"
            "  plugins: [react()],\n"
            "});\n",
            encoding="utf-8",
        )

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