import os
import json
import re
from pathlib import Path

GENERATED_DIR = Path(__file__).resolve().parents[2] / "generated_projects"

# Matches e.g. `import './styles.css'` or `import "./App.css";` inside
# AI-generated App.jsx -- used to catch cases where the model names its
# stylesheet import something other than index.css (see write_project_files).
_CSS_IMPORT_PATTERN = re.compile(r"""import\s+['"]\.\/([\w.-]+\.css)['"]""")


def _ensure_vite_package_json(raw_pkg_json: str, main_app_file_name: str = "App.jsx") -> str:
    """Normalise an LLM-generated package.json so it always uses Vite.

    The LLM occasionally generates a Create-React-App style package.json
    (react-scripts start/build) even though we inject a vite.config.js and
    a Vite-style main.jsx. That mismatch means `npm install` either installs
    the entire CRA toolchain (slow, >100 MB) or fails outright because
    react-scripts has undeclared peer dependencies that conflict with newer
    Node versions.  This function detects and fixes the most common
    incompatible patterns so we always get a lightweight Vite project.
    """
    try:
        pkg = json.loads(raw_pkg_json)
    except (json.JSONDecodeError, TypeError):
        # If the LLM gave us garbage JSON, return a safe minimal default.
        pkg = {}

    pkg.setdefault("name", "generated-app")
    pkg.setdefault("version", "1.0.0")
    pkg["type"] = "module"
    pkg["private"] = True

    # --- Fix scripts ---
    scripts = pkg.get("scripts", {})
    # Remove CRA scripts
    for bad in ("react-scripts start", "react-scripts build",
                "react-scripts test", "react-scripts eject"):
        for k, v in list(scripts.items()):
            if v == bad:
                del scripts[k]
    # Always set the Vite scripts
    scripts["dev"] = "vite"
    scripts["build"] = "vite build"
    scripts["preview"] = "vite preview"
    pkg["scripts"] = scripts

    # --- Fix dependencies ---
    deps = pkg.get("dependencies", {})
    dev_deps = pkg.get("devDependencies", {})

    # Remove CRA from everywhere
    for bad in ("react-scripts", "@craco/craco"):
        deps.pop(bad, None)
        dev_deps.pop(bad, None)

    # Ensure React is in dependencies
    deps.setdefault("react", "^18.3.1")
    deps.setdefault("react-dom", "^18.3.1")

    # Ensure Vite is in devDependencies
    dev_deps["vite"] = dev_deps.get("vite") or "^5.4.0"
    dev_deps["@vitejs/plugin-react"] = dev_deps.get("@vitejs/plugin-react") or "^4.3.1"

    if deps:
        pkg["dependencies"] = deps
    if dev_deps:
        pkg["devDependencies"] = dev_deps

    return json.dumps(pkg, indent=2)


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
    is_no_backend = (
        backend_code.get("framework") in ("None", "none", None)
        or backend_code.get("main_file_name") in ("none", "", None)
        or not backend_code.get("main_file")
        or str(backend_code.get("main_file", "")).startswith("# No backend required")
    )

    if not is_no_backend:
        be_dir = project_dir / "backend"
        be_dir.mkdir(exist_ok=True)

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

        extra_files = backend_code.get("extra_files") or []
        for extra in extra_files:
            file_path = extra.get("path") if isinstance(extra, dict) else getattr(extra, "path", None)
            file_code = extra.get("code") if isinstance(extra, dict) else getattr(extra, "code", None)
            if not file_path or not file_code:
                continue
            safe_path = Path(file_path.lstrip("/").lstrip("\\"))
            if ".." in safe_path.parts:
                continue
            dest = be_dir / safe_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(file_code, encoding="utf-8")

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

    main_app_file_name = frontend_code.get("main_app_file_name") or "App.jsx"
    if frontend_code.get("main_app_code"):
        (src_dir / main_app_file_name).write_text(frontend_code["main_app_code"], encoding="utf-8")
    # Always write api client as api.js so imports like `import { ... } from './api'`
    # always resolve. If the LLM also named it something else, write both so either works.
    if frontend_code.get("api_client_code"):
        (src_dir / "api.js").write_text(frontend_code["api_client_code"], encoding="utf-8")
    if frontend_code.get("package_json"):
        normalized_pkg = _ensure_vite_package_json(
            frontend_code["package_json"],
            frontend_code.get("main_app_file_name", "App.jsx"),
        )
        (fe_dir / "package.json").write_text(normalized_pkg, encoding="utf-8")
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

    # Write any extra files in frontend_code (e.g. added by BugFixer agent)
    known_fe_keys = {
        "framework", "main_app_code", "main_app_file_name", "components_code",
        "api_client_code", "package_json", "dockerfile", "styles_code",
        "entry_point_code", "entry_point_file_name", "index_html"
    }
    for key, value in frontend_code.items():
        if key not in known_fe_keys and isinstance(value, str) and (key.endswith(".js") or key.endswith(".jsx") or key.endswith(".ts") or key.endswith(".tsx") or key.endswith(".css")):
            # Guard against path traversal
            safe_name = Path(key).name
            (src_dir / safe_name).write_text(value, encoding="utf-8")

    # Static Vite boilerplate: the LLM-generated FrontendCode schema only
    # produces App.jsx/api.js/styles/package.json. We also write index.html,
    # main.jsx, and vite.config.js if the LLM didn't provide them, so
    # `npm run dev` always has what it needs.
    #
    # Prefer LLM-provided files over boilerplate when available (schema fields
    # entry_point_code/entry_point_file_name/index_html), so framework-specific
    # scaffolding (e.g. Vue/Svelte) is respected.
    if frontend_code.get("main_app_code"):
        framework_str = str(frontend_code.get("framework", "")).lower()
        is_vanilla = (
            "vanilla" in framework_str
            or "html" in framework_str
            or "javascript" in framework_str and "react" not in framework_str
            or not (main_app_file_name.endswith(".jsx") or main_app_file_name.endswith(".tsx"))
        )

        entry_file_name = frontend_code.get("entry_point_file_name") or ("main.js" if is_vanilla else "main.jsx")
        entry_code = frontend_code.get("entry_point_code")
        has_css = bool(frontend_code.get("styles_code"))

        if not (src_dir / entry_file_name).exists():
            if entry_code:
                (src_dir / entry_file_name).write_text(entry_code, encoding="utf-8")
            elif is_vanilla:
                (src_dir / entry_file_name).write_text(
                    ("import './index.css';\n" if has_css else "")
                    + f"import './{main_app_file_name}';\n",
                    encoding="utf-8",
                )
            else:
                (src_dir / entry_file_name).write_text(
                    "import React from 'react';\n"
                    "import ReactDOM from 'react-dom/client';\n"
                    f"import App from './{main_app_file_name}';\n"
                    + ("import './index.css';\n" if has_css else "")
                    + "\n"
                    "ReactDOM.createRoot(document.getElementById('root')).render(\n"
                    "  <React.StrictMode>\n"
                    "    <App />\n"
                    "  </React.StrictMode>\n"
                    ");\n",
                    encoding="utf-8",
                )

        if not (fe_dir / "index.html").exists():
            ai_index_html = frontend_code.get("index_html")
            if ai_index_html:
                (fe_dir / "index.html").write_text(ai_index_html, encoding="utf-8")
            else:
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
                    f'    <script type="module" src="/src/{entry_file_name}"></script>\n'
                    '  </body>\n'
                    '</html>\n',
                    encoding="utf-8",
                )

        if not (fe_dir / "vite.config.js").exists():
            if is_vanilla:
                (fe_dir / "vite.config.js").write_text(
                    "import { defineConfig } from 'vite';\n\n"
                    "export default defineConfig({\n"
                    "  server: { port: 5173 }\n"
                    "});\n",
                    encoding="utf-8",
                )
            else:
                (fe_dir / "vite.config.js").write_text(
                    "import { defineConfig } from 'vite';\n"
                    "import react from '@vitejs/plugin-react';\n\n"
                    "export default defineConfig({\n"
                    "  plugins: [react()],\n"
                    "});\n",
                    encoding="utf-8",
                )

        # If no package.json was provided by the LLM, write a safe Vite default.
        if not (fe_dir / "package.json").exists():
            safe_pkg = _ensure_vite_package_json("{}", frontend_code.get("main_app_file_name", "App.jsx"))
            (fe_dir / "package.json").write_text(safe_pkg, encoding="utf-8")

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


def validate_project_build(job_id: str, project_dir: str) -> dict:
    """Run real build tools to check if the generated project compiles.
    Returns a dict with 'backend_errors' and 'frontend_errors' keys (strings).
    """
    import subprocess
    from app.services.preview_service import _normalize_frontend_package_json

    results = {"backend_errors": "", "frontend_errors": ""}

    # 1. Frontend validation
    fe_dir = os.path.join(project_dir, "frontend")
    if os.path.exists(fe_dir) and os.path.exists(os.path.join(fe_dir, "package.json")):
        npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
        # Normalize package.json first
        _normalize_frontend_package_json(fe_dir)

        # Run npm install (fast if already installed)
        try:
            proc = subprocess.run(
                [npm_cmd, "install"],
                cwd=fe_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=90,
                text=True,
            )
            if proc.returncode != 0:
                # If install failed, try with legacy peer deps
                proc = subprocess.run(
                    [npm_cmd, "install", "--legacy-peer-deps"],
                    cwd=fe_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=90,
                    text=True,
                )
            if proc.returncode != 0:
                results["frontend_errors"] = f"npm install failed:\n{proc.stdout[-1500:]}"
        except Exception as e:
            results["frontend_errors"] = f"npm install failed to execute: {str(e)}"

        # Run npm run build if install succeeded
        if not results["frontend_errors"]:
            try:
                build_proc = subprocess.run(
                    [npm_cmd, "run", "build"],
                    cwd=fe_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=90,
                    text=True,
                )
                if build_proc.returncode != 0:
                    results["frontend_errors"] = f"Build failed (npm run build):\n{build_proc.stdout[-2500:]}"
            except Exception as e:
                results["frontend_errors"] = f"Build execution failed: {str(e)}"

    # 2. Backend validation (Syntax check)
    be_dir = os.path.join(project_dir, "backend")
    if os.path.exists(be_dir):
        # Find Python files and check syntax
        py_files = [f for f in os.listdir(be_dir) if f.endswith(".py")]
        if py_files:
            import py_compile
            syntax_errors = []
            for py_file in py_files:
                path = os.path.join(be_dir, py_file)
                try:
                    py_compile.compile(path, doraise=True)
                except py_compile.PyCompileError as e:
                    syntax_errors.append(f"Syntax error in {py_file}:\n{str(e)}")
            if syntax_errors:
                results["backend_errors"] = "\n".join(syntax_errors)

    return results