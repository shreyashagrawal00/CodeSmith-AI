import React from "react";
import { CheckCircle2, Loader2, Hourglass } from "lucide-react";

const AGENT_ROLES = [
  { id: "PM", label: "Product Manager", desc: "Gathering requirements" },
  { id: "Architect", label: "System Architect", desc: "Designing system layout" },
  { id: "DatabaseDesigner", label: "DB Designer", desc: "Modeling schemas & SQL" },
  { id: "BackendEngineer", label: "Backend Engineer", desc: "Developing APIs & services" },
  { id: "FrontendEngineer", label: "Frontend Engineer", desc: "Coding UI components" },
  { id: "Reviewer", label: "Code Reviewer", desc: "Auditing implementation" },
  { id: "SecurityExpert", label: "Security Expert", desc: "Performing vulnerability checks" },
  { id: "QAEngineer", label: "QA Engineer", desc: "Generating comprehensive tests" },
  { id: "BugFixer", label: "Bug Fixer", desc: "Resolving detected issues" },
  { id: "TechWriter", label: "Technical Writer", desc: "Compiling README & API docs" },
  { id: "DevOps", label: "DevOps Engineer", desc: "Creating Docker & CI/CD configs" }
];

export default function ProgressBar({ currentAgent, log, status }) {
  const completedAgents = new Set(log.map(entry => entry.agent));

  return (
    <div className="w-full max-w-4xl mx-auto space-y-8 glass rounded-2xl p-8 border border-slate-800/80">
      <div className="flex justify-between items-center pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            Orchestration Status: 
            <span className={`text-sm px-3 py-1 rounded-full uppercase tracking-wider font-semibold ${
              status === "completed" ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30" :
              status === "failed" ? "bg-rose-500/20 text-rose-400 border border-rose-500/30" :
              "bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 animate-pulse"
            }`}>
              {status}
            </span>
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            {status === "completed" ? "Generation finished successfully!" : 
             status === "failed" ? "An error occurred during build." : 
             `Currently running: ${currentAgent || "PM"}`}
          </p>
        </div>
        {status === "running" && (
          <Loader2 className="w-6 h-6 text-indigo-500 animate-spin" />
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {AGENT_ROLES.map((agent) => {
          const isCompleted = completedAgents.has(agent.id) || (status === "completed");
          const isActive = currentAgent === agent.id && status === "running";
          
          return (
            <div 
              key={agent.id}
              className={`p-4 rounded-xl border transition-all duration-300 ${
                isActive ? "bg-indigo-500/10 border-indigo-500 glow-indigo" :
                isCompleted ? "bg-emerald-500/5 border-emerald-500/30" :
                "bg-slate-950/20 border-slate-800/50 opacity-60"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h3 className="font-semibold text-sm text-slate-200">{agent.label}</h3>
                  <p className="text-xs text-slate-500 mt-1">{agent.desc}</p>
                </div>
                <div>
                  {isCompleted ? (
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  ) : isActive ? (
                    <Loader2 className="w-5 h-5 text-indigo-400 animate-spin" />
                  ) : (
                    <Hourglass className="w-5 h-5 text-slate-600" />
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
