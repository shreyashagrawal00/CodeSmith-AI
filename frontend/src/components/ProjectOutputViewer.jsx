import React, { useState } from "react";
import { Copy, Check, FileText, Database, ShieldAlert, Award, Terminal, Code, Settings } from "lucide-react";

export default function ProjectOutputViewer({ projectData }) {
  const [activeTab, setActiveTab] = useState("requirements");
  const [copied, setCopied] = useState(false);

  if (!projectData) return null;

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const tabs = [
    { id: "requirements", label: "Requirements", icon: FileText, data: projectData.requirements },
    { id: "architecture", label: "Architecture", icon: Terminal, data: projectData.architecture },
    { id: "database", label: "Database", icon: Database, data: projectData.database_schema },
    { id: "backend", label: "Backend", icon: Code, data: projectData.backend_code },
    { id: "frontend", label: "Frontend", icon: Code, data: projectData.frontend_code },
    { id: "review", label: "Code Review", icon: Award, data: projectData.review_report },
    { id: "security", label: "Security Audit", icon: ShieldAlert, data: projectData.security_report },
    { id: "testing", label: "Test Suite", icon: Settings, data: projectData.testing_report },
    { id: "deployment", label: "Deployment", icon: Settings, data: projectData.deployment },
    { id: "documentation", label: "Documentation", icon: FileText, data: projectData.documentation }
  ];

  const currentTab = tabs.find((t) => t.id === activeTab);
  const formattedContent = currentTab?.data ? JSON.stringify(currentTab.data, null, 2) : "No data available";

  return (
    <div className="w-full max-w-6xl mx-auto glass rounded-2xl border border-slate-800 overflow-hidden">
      <div className="flex flex-wrap border-b border-slate-800 bg-slate-950/40">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-5 py-4 text-sm font-medium transition-all outline-none border-b-2 ${
                activeTab === tab.id
                  ? "border-indigo-500 text-indigo-400 bg-indigo-500/5"
                  : "border-transparent text-slate-400 hover:text-white hover:bg-slate-900/50"
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      <div className="p-6 bg-slate-950/20 relative">
        <div className="absolute right-6 top-6 z-10">
          <button
            onClick={() => copyToClipboard(formattedContent)}
            className="p-2.5 bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 text-slate-300 rounded-lg transition-all flex items-center gap-2 text-xs font-semibold"
          >
            {copied ? (
              <>
                <Check className="w-4 h-4 text-emerald-400" />
                Copied!
              </>
            ) : (
              <>
                <Copy className="w-4 h-4" />
                Copy JSON
              </>
            )}
          </button>
        </div>

        {activeTab === "requirements" && currentTab.data && (
          <div className="space-y-6 text-slate-300">
            <div>
              <h3 className="text-2xl font-bold text-white mb-1">{currentTab.data.project_name}</h3>
              <p className="text-slate-400">{currentTab.data.description}</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800/80">
                <h4 className="font-bold text-indigo-400 mb-3 text-sm tracking-wider uppercase">Features</h4>
                <ul className="list-disc pl-5 space-y-1.5 text-sm">
                  {currentTab.data.features?.map((f, i) => <li key={i}>{f}</li>)}
                </ul>
              </div>
              <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800/80">
                <h4 className="font-bold text-purple-400 mb-3 text-sm tracking-wider uppercase">Target Users</h4>
                <ul className="list-disc pl-5 space-y-1.5 text-sm">
                  {currentTab.data.target_users?.map((u, i) => <li key={i}>{u}</li>)}
                </ul>
              </div>
            </div>
            <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800/80">
              <h4 className="font-bold text-emerald-400 mb-3 text-sm tracking-wider uppercase">Suggested Tech Stack</h4>
              <div className="flex flex-wrap gap-2">
                {currentTab.data.tech_stack?.map((t, i) => (
                  <span key={i} className="px-3 py-1 bg-slate-800 border border-slate-700 text-slate-200 rounded-full text-xs font-semibold">
                    {t}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === "architecture" && currentTab.data && (
          <div className="space-y-6 text-slate-300">
            <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800/80">
              <h4 className="font-bold text-indigo-400 mb-2 text-sm tracking-wider uppercase">System Design</h4>
              <p className="text-sm whitespace-pre-line leading-relaxed">{currentTab.data.system_design}</p>
            </div>
            <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800/80">
              <h4 className="font-bold text-purple-400 mb-2 text-sm tracking-wider uppercase">Components</h4>
              <ul className="list-disc pl-5 space-y-1 text-sm">
                {currentTab.data.components?.map((c, i) => <li key={i}>{c}</li>)}
              </ul>
            </div>
            <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800/80">
              <h4 className="font-bold text-emerald-400 mb-2 text-sm tracking-wider uppercase">API Design Spec</h4>
              <pre className="text-xs font-mono bg-slate-950 p-4 rounded-lg overflow-x-auto text-slate-300 border border-slate-800">
                {currentTab.data.api_design}
              </pre>
            </div>
          </div>
        )}

        {activeTab === "database" && currentTab.data && (
          <div className="space-y-6 text-slate-300">
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-slate-400">Database Engine:</span>
              <span className="px-3 py-1 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-lg text-xs font-bold uppercase">
                {currentTab.data.database_type}
              </span>
            </div>
            <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800/80">
              <h4 className="font-bold text-indigo-400 mb-3 text-sm tracking-wider uppercase">Migration SQL Schema</h4>
              <pre className="text-xs font-mono bg-slate-950 p-4 rounded-lg overflow-x-auto text-slate-300 border border-slate-800">
                {currentTab.data.migration_sql}
              </pre>
            </div>
          </div>
        )}

        {activeTab === "backend" && currentTab.data && (
          <div className="space-y-6 text-slate-300">
            <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800/80">
              <h4 className="font-bold text-indigo-400 mb-3 text-sm tracking-wider uppercase">Framework: {currentTab.data.framework}</h4>
              <div className="space-y-4">
                <div>
                  <span className="text-xs font-bold text-slate-500 block mb-1">main.py</span>
                  <pre className="text-xs font-mono bg-slate-950 p-4 rounded-lg overflow-x-auto text-slate-300 border border-slate-800 max-h-80 overflow-y-auto">
                    {currentTab.data.main_file}
                  </pre>
                </div>
                <div>
                  <span className="text-xs font-bold text-slate-500 block mb-1">models.py</span>
                  <pre className="text-xs font-mono bg-slate-950 p-4 rounded-lg overflow-x-auto text-slate-300 border border-slate-800 max-h-80 overflow-y-auto">
                    {currentTab.data.models_code}
                  </pre>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "frontend" && currentTab.data && (
          <div className="space-y-6 text-slate-300">
            <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800/80">
              <h4 className="font-bold text-indigo-400 mb-3 text-sm tracking-wider uppercase">Framework: {currentTab.data.framework}</h4>
              <div className="space-y-4">
                <div>
                  <span className="text-xs font-bold text-slate-500 block mb-1">App.jsx</span>
                  <pre className="text-xs font-mono bg-slate-950 p-4 rounded-lg overflow-x-auto text-slate-300 border border-slate-800 max-h-80 overflow-y-auto">
                    {currentTab.data.main_app_code}
                  </pre>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "review" && currentTab.data && (
          <div className="space-y-6 text-slate-300">
            <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800/80">
              <h4 className="font-bold text-indigo-400 mb-2 text-sm tracking-wider uppercase">Review Report</h4>
              <p className="text-sm italic mb-4">"{currentTab.data.overall_quality}"</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h5 className="font-bold text-rose-400 text-xs mb-2 uppercase">Backend Concerns</h5>
                  <ul className="list-disc pl-5 text-sm space-y-1">
                    {currentTab.data.backend_issues?.map((iss, i) => <li key={i}>{iss}</li>)}
                  </ul>
                </div>
                <div>
                  <h5 className="font-bold text-amber-400 text-xs mb-2 uppercase">Recommendations</h5>
                  <ul className="list-disc pl-5 text-sm space-y-1">
                    {currentTab.data.recommendations?.map((rec, i) => <li key={i}>{rec}</li>)}
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "security" && currentTab.data && (
          <div className="space-y-6 text-slate-300">
            <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800/80">
              <h4 className="font-bold text-rose-500 mb-2 text-sm tracking-wider uppercase flex items-center gap-2">
                Security Risk Level: <span className="text-white uppercase px-2 py-0.5 bg-rose-500/20 border border-rose-500/30 rounded text-xs">{currentTab.data.risk_level}</span>
              </h4>
              <ul className="list-disc pl-5 text-sm space-y-2 mt-4">
                {currentTab.data.vulnerabilities?.map((vuln, i) => (
                  <li key={i}>
                    <strong className="text-slate-200">{vuln.title}</strong>: {vuln.description}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {activeTab !== "requirements" && activeTab !== "architecture" && activeTab !== "database" && activeTab !== "backend" && activeTab !== "frontend" && activeTab !== "review" && activeTab !== "security" && (
          <div className="max-h-[500px] overflow-y-auto">
            <pre className="text-xs font-mono bg-slate-950 p-4 rounded-lg overflow-x-auto text-slate-300 border border-slate-800">
              {formattedContent}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
