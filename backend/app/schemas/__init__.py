from pydantic import BaseModel, Field
from typing import List, Dict, Any

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
    framework: str = Field(description="FastAPI or other chosen framework")
    language: str = Field(description="Language used")
    main_file: str = Field(description="Content of main.py")
    models_code: str = Field(description="Database models (SQLAlchemy/SQLModel) file content")
    routes_code: str = Field(description="FastAPI endpoints and routers file content")
    services_code: str = Field(description="Business logic service functions file content")
    requirements_txt: str = Field(description="requirements.txt dependencies file content")
    dockerfile: str = Field(description="Dockerfile for backend containerization")

# 5. Frontend Developer Agent Output Schema
class FrontendCode(BaseModel):
    framework: str = Field(description="React or chosen frontend framework")
    main_app_code: str = Field(description="Content of App.jsx")
    components_code: Dict[str, str] = Field(default={}, description="Map of component filenames to their React code content")
    api_client_code: str = Field(description="Axios/Fetch client integration with backend")
    package_json: str = Field(description="package.json manifest code")
    dockerfile: str = Field(description="Dockerfile for frontend containerization")
    styles_code: str = Field(description="Tailwind CSS / index.css stylesheet code")

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
    fixed_backend_files: Dict[str, str] = Field(default={}, description="Map of backend keys (e.g. 'main_file', 'routes_code') to their updated file contents")
    fixed_frontend_files: Dict[str, str] = Field(default={}, description="Map of frontend keys (e.g. 'main_app_code', 'components_code', 'styles_code') to their updated file contents")
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
