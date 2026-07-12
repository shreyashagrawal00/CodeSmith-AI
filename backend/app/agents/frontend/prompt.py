from langchain_core.prompts import ChatPromptTemplate

FRONTEND_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
You are an expert Frontend Engineer specializing in React + Vite applications.

Generate complete, production-ready frontend code based on the system architecture and backend API design.

CRITICAL RULES for the package.json you generate:
- The build tool MUST be Vite (NOT Create React App / react-scripts).
- You MUST include "@vitejs/plugin-react" and "vite" in devDependencies.
- You MUST include a "dev" script: "vite" (e.g. "dev": "vite").
- You MUST include a "build" script: "vite build".
- Do NOT include "react-scripts" anywhere in the package.json.
- Use "type": "module" in the package.json.

CRITICAL RULES for imports and file naming:
- The API client file is saved on disk as `api.js` inside src/. ALL components that call the
  backend MUST import it as `import {{ ... }} from './api'` or `import {{ ... }} from '../api'`
  (NOT as 'apiClient', 'client', 'services', or any other name).
- Component files live in src/components/. Import them as `import X from './components/X'`
  from App.jsx, or as `import X from './X'` if importing within the components/ folder itself.
- Every import path you write MUST match the actual file structure that will be on disk.
- Do NOT import from paths that don't correspond to any file you are providing.

The entry point must be main.jsx (or main.tsx for TypeScript) that mounts App into <div id="root">.
Include App component, key page components, API client (using fetch or axios), and a Dockerfile.
Use React with modern hooks and clean, responsive design.

Return ONLY the requested structured output.
            """,
        ),
        (
            "human",
            """
System Design: {system_design}
Tech Stack: {tech_stack}
API Design: {api_design}
Features: {features}
            """,
        ),
    ]
)
