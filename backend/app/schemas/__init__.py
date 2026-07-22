from pydantic import BaseModel, Field
from typing import List, Dict, Any


class ComponentFile(BaseModel):
    """One React component file. Used instead of a raw Dict[str, str] map
    because several providers' strict structured-output / tool-calling
    validation rejects "object" schemas with arbitrary keys
    (additionalProperties, no fixed properties) -- observed as Groq's
    "Failed to call a function" and Cerebras' "Object fields..." 400
    errors. A list of fixed-shape objects is fully strict-schema
    compatible."""
    filename: str = Field(description="Component filename, e.g. 'Header.jsx'")
    code: str = Field(description="React code content for this component")


class BackendFile(BaseModel):
    """One extra backend file (middleware, config, additional routes, helpers,
    etc.). Using an explicit list of (path, code) pairs instead of a raw
    dict for the same strict-schema-compatibility reason as ComponentFile."""
    path: str = Field(
        description="Relative path from the backend root, e.g. 'routes/taskRoutes.js', "
        "'middleware/authMiddleware.js', 'config/db.js', 'utils/helpers.py'. "
        "Use forward slashes. MUST match exactly what the main file imports."
    )
    code: str = Field(description="Full source code content of this file.")


class FileEdit(BaseModel):
    """One file/field correction from the bugfix agent. Same rationale as
    ComponentFile above -- replaces a raw Dict[str, str] map."""
    key: str = Field(
        description="Which field this fix applies to. For core backend fields use: "
        "'main_file', 'routes_code', 'models_code', 'services_code', 'dependency_manifest', 'dockerfile'. "
        "For extra backend files, use the relative path exactly as declared in extra_files, "
        "e.g. 'routes/taskRoutes.js'. "
        "For frontend fields: 'main_app_code', 'entry_point_code', 'api_client_code', "
        "'package_json', 'dockerfile', 'styles_code', or a components_code filename like 'Header.jsx'."
    )
    content: str = Field(description="The corrected file content")

# 1. PM Agent Output Schema
class PMOutput(BaseModel):
    project_name: str = Field(description="Name of the project")
    description: str = Field(description="High-level description of the project")
    target_users: List[str] = Field(default=[], description="List of target users for the platform")
    features: List[str] = Field(default=[], description="List of core features/requirements")
    tech_stack: List[str] = Field(default=[], description="Suggested technology stack")

# 2. Architect Agent Output Schema
class ArchitectOutput(BaseModel):
    system_design: str = Field(description="System design outline and decisions")
    components: List[str] = Field(default=[], description="Core system components/modules")
    tech_stack: List[str] = Field(default=[], description="Finalized tech stack details")
    api_design: str = Field(description="API design endpoints and details")
    scalability_notes: str = Field(description="Scalability and reliability notes")

# 3. Database Designer Agent Output Schema
class DatabaseSchema(BaseModel):
    database_type: str = Field(description="Database type (e.g. PostgreSQL)")
    tables: List[Dict[str, Any]] = Field(default=[], description="List of database tables and columns")
    relationships: List[str] = Field(default=[], description="ER relationships")
    indexes: List[str] = Field(default=[], description="Database indexes suggested")
    migration_sql: str = Field(description="Raw SQL schema script for migrations")

# 4. Backend Developer Agent Output Schema
class BackendCode(BaseModel):
    framework: str = Field(description="Backend framework, matching EXACTLY what was specified in the tech stack -- e.g. 'FastAPI' (Python), 'Express.js' (Node.js), 'NestJS' (Node.js), 'Django' (Python), 'Spring Boot' (Java). Do NOT default to FastAPI/Python unless that is what the tech stack actually specifies.")
    language: str = Field(description="Programming language for the backend, matching the tech stack exactly (e.g. 'Python', 'JavaScript', 'TypeScript', 'Java').")
    main_file: str = Field(description="Content of the main application entry file, written in the chosen language/framework's idioms and conventions.")
    main_file_name: str = Field(description="Filename for the main entry file, matching the language's convention -- e.g. 'main.py' for Python/FastAPI, 'index.js' or 'server.js' for Node.js/Express, 'main.ts' for NestJS.")
    models_code: str = Field(default="", description="Database models/schema file content. For Python use SQLAlchemy/SQLModel; for Node.js inline models here OR put them in extra_files if separate model files are needed.")
    routes_code: str = Field(default="", description="Primary API routes/endpoints file. Put ALL route logic here if using a single-file approach, OR use this as a router index and declare individual route files in extra_files.")
    services_code: str = Field(default="", description="Business logic / service layer file content.")
    extra_files: List[BackendFile] = Field(
        default=[],
        description="Additional backend files needed to make the project work -- e.g. "
        "'middleware/authMiddleware.js', 'routes/userRoutes.js', 'routes/taskRoutes.js', "
        "'config/db.js', 'utils/helpers.py', '.env.example'. "
        "CRITICAL: Every file that main_file, routes_code, or services_code imports "
        "from a sub-path (e.g. require('./middleware/auth')) MUST appear here with the "
        "matching relative path so it actually exists on disk."
    )
    dependency_manifest: str = Field(default="", description="Dependency manifest file content, matching the chosen language -- e.g. requirements.txt content for Python, package.json content for Node.js.")
    dependency_manifest_name: str = Field(default="", description="Filename for the dependency manifest, matching the language convention -- e.g. 'requirements.txt' for Python, 'package.json' for Node.js.")
    dockerfile: str = Field(default="", description="Dockerfile for backend containerization, appropriate for the chosen language/runtime.")

# 5. Frontend Developer Agent Output Schema
class FrontendCode(BaseModel):
    framework: str = Field(description="Frontend framework, matching EXACTLY what was specified in the tech stack -- e.g. 'React', 'Vue', 'Angular', 'Svelte', 'vanilla JavaScript'. Do NOT default to React unless that is what the tech stack actually specifies.")
    main_app_code: str = Field(description="Content of the main application component/entry file, written in the chosen framework's idioms (e.g. App.jsx for React, App.vue for Vue, App.svelte for Svelte).")
    main_app_file_name: str = Field(description="Filename for the main app component, matching the framework convention -- e.g. 'App.jsx' for React, 'App.vue' for Vue, 'App.svelte' for Svelte.")
    components_code: List[ComponentFile] = Field(default=[], description="List of component files (filename + code), using the chosen framework's file extension (e.g. .jsx for React, .vue for Vue, .svelte for Svelte).")
    api_client_code: str = Field(default="", description="HTTP client integration with the backend (e.g. Axios/Fetch), written in the chosen framework's conventions.")
    package_json: str = Field(description="package.json manifest code with dependencies matching the chosen framework, including a 'dev' (or 'start'/'serve') script to run a local dev server.")
    dockerfile: str = Field(default="", description="Dockerfile for frontend containerization.")
    styles_code: str = Field(description="Main stylesheet code (CSS/SCSS/Tailwind) for the application.")
    entry_point_code: str = Field(default="", description="Content of the JS/TS entry file that bootstraps/mounts the app into the DOM under a Vite-style workflow (e.g. main.jsx for React+Vite, main.js for Vue+Vite, main.ts for Svelte+Vite). Required for React/Vue/Svelte/vanilla-via-Vite; leave blank only for frameworks with a fundamentally different build tool (e.g. Angular CLI).")
    entry_point_file_name: str = Field(default="", description="Filename for the entry point file, e.g. 'main.jsx', 'main.js', 'main.ts'.")
    index_html: str = Field(default="", description="Content of index.html that loads the entry point via <script type=\"module\" src=\"/src/ENTRY_FILE\">, following Vite conventions. Leave blank only if not applicable to the chosen framework/build tool.")

# 6. Reviewer Agent Output Schema
class ReviewReport(BaseModel):
    overall_quality: str = Field(description="High-level assessment of code quality")
    quality_score: float = Field(default=100.0, description="Numerical quality score from 0.0 to 100.0")
    backend_issues: List[str] = Field(default=[], description="List of issues found in backend code")
    frontend_issues: List[str] = Field(default=[], description="List of issues found in frontend code")
    code_smells: List[str] = Field(default=[], description="Refactoring opportunities / smells")
    recommendations: List[str] = Field(default=[], description="Actionable recommendations")
    approved: bool = Field(description="True if code is good to pass, False if bug fixes needed")

# 7. Security Engineer Agent Output Schema
class SecurityReport(BaseModel):
    risk_level: str = Field(description="High, Medium, or Low risk rating")
    vulnerabilities: List[Dict[str, Any]] = Field(default=[], description="List of vulnerability details")
    owasp_checklist: Dict[str, bool] = Field(default={}, description="OWASP standard compliance checklist status")
    recommendations: List[str] = Field(default=[], description="Vulnerability remediation suggestions")
    is_secure: bool = Field(description="True if safe to proceed, False otherwise")

# 8. Testing Engineer Agent Output Schema
class TestingReport(BaseModel):
    unit_tests_code: str = Field(description="Pytest/Vitest code for unit testing")
    integration_tests_code: str = Field(description="Integration/API endpoint tests code")
    frontend_tests_code: str = Field(default="", description="Frontend component tests (e.g., React Testing Library)")
    test_coverage_estimate: str = Field(description="Estimate of test coverage percentage/report")
    test_cases: List[Dict[str, Any]] = Field(default=[], description="List of generated test scenarios")

# 9. Bug Fix Engineer Agent Output Schema
class BugfixReport(BaseModel):
    bugs_found: List[str] = Field(default=[], description="List of descriptions of bugs addressed")
    fixed_backend_files: List[FileEdit] = Field(default=[], description="List of backend file fixes (key + corrected content). Valid keys: 'main_file', 'models_code', 'routes_code', 'services_code', 'dependency_manifest', 'dockerfile'")
    fixed_frontend_files: List[FileEdit] = Field(default=[], description="List of frontend file fixes (key + corrected content). Valid keys: 'main_app_code', 'entry_point_code', 'api_client_code', 'package_json', 'dockerfile', 'styles_code', or a components_code filename like 'Header.jsx'")
    changes_summary: List[str] = Field(default=[], description="Summary log of changes made")

# 10. Documentation Engineer Agent Output Schema
class Documentation(BaseModel):
    readme_md: str = Field(description="Markdown README file content")
    api_docs_md: str = Field(description="API design & endpoint docs")
    architecture_md: str = Field(description="Architecture and flow design document")
    setup_guide_md: str = Field(description="Step by step setup / deployment instructions")

# 11. Deployment Engineer Agent Output Schema
class DeploymentConfig(BaseModel):
    docker_compose_yml: str = Field(description="docker-compose.yml configuration")
    nginx_conf: str = Field(description="NGINX config for reverse proxy")
    env_example: str = Field(description="Template .env file contents")
    deployment_guide_md: str = Field(description="Step by step deployment guide")
    ci_cd_yml: str = Field(description="GitHub Actions or GitLab CI file content")