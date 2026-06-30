from langchain_core.prompts import ChatPromptTemplate

DEPLOYMENT_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are a DevOps Engineer and Cloud Infrastructure Specialist.

Generate complete deployment configuration for the project including:
- docker-compose.yml for the full stack
- nginx.conf for reverse proxy
- .env.example with all required environment variables
- Deployment guide
- GitHub Actions CI/CD pipeline

Return ONLY the requested structured output.
            """,
        ),
        (
            "human",
            """
Project Name: {project_name}
Tech Stack: {tech_stack}
Components: {components}
Database Type: {database_type}
            """,
        ),
    ]
)
