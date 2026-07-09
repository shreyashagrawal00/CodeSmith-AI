import React, { useState, useRef, useEffect } from "react";
import { Copy, Check, FileText, Database, ShieldAlert, Award, Terminal, Code, Settings, ChevronLeft, ChevronRight, Inbox } from "lucide-react";

const TAB_GROUPS = [
  {
    label: "Plan",
    accent: "indigo",
    tabs: [
      { id: "requirements", label: "Requirements", icon: FileText, dataKey: "requirements" },
      { id: "architecture", label: "Architecture", icon: Terminal, dataKey: "architecture" },
      { id: "database", label: "Database", icon: Database, dataKey: "database_schema" },
    ],
  },
  {
    label: "Build",
    accent: "purple",
    tabs: [
      { id: "backend", label: "Backend", icon: Code, dataKey: "backend_code" },
      { id: "frontend", label: "Frontend", icon: Code, dataKey: "frontend_code" },
    ],
  },
  {
    label: "Verify",
    accent: "rose",
    tabs: [
      { id: "review", label: "Code Review", icon: Award, dataKey: "review_report" },
      { id: "security", label: "Security Audit", icon: ShieldAlert, dataKey: "security_report" },
      { id: "testing", label: "Test Suite", icon: Settings, dataKey: "testing_report" },
    ],
  },
  {
    label: "Ship",
    accent: "emerald",
    tabs: [
      { id: "deployment", label: "Deployment", icon: Settings, dataKey: "deployment" },
      { id: "documentation", label: "Documentation", icon: FileText, dataKey: "documentation" },
    ],
  },
];

const ACCENT_CLASSES = {
  indigo: { active: "border-indigo-500 text-indigo-400 bg-indigo-500/10", dot: "bg-indigo-500", eyebrow: "text-indigo-400/70" },
  purple: { active: "border-purple-500 text-purple-400 bg-purple-500/10", dot: "bg-purple-500", eyebrow: "text-purple-400/70" },
  rose: { active: "border-rose-500 text-rose-400 bg-rose-500/10", dot: "bg-rose-500", eyebrow: "text-rose-400/70" },
  emerald: { active: "border-emerald-500 text-emerald-400 bg-emerald-500/10", dot: "bg-emerald-500", eyebrow: "text-emerald-400/70" },
};

const ALL_TABS = TAB_GROUPS.flatMap((g) => g.tabs.map((t) => ({ ...t, accent: g.accent })));

export default function ProjectOutputViewer({ projectData }) {
  const [activeTab, setActiveTab] = useState("requirements");
  const [copied, setCopied] = useState(false);
  const [selectedFileIndex, setSelectedFileIndex] = useState(0);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);
  const scrollerRef = useRef(null);

  const updateScrollShadows = () => {
    const el = scrollerRef.current;
    if (!el) return;
    setCanScrollLeft(el.scrollLeft > 4);
    setCanScrollRight(el.scrollLeft + el.clientWidth < el.scrollWidth - 4);
  };

  useEffect(() => {
    updateScrollShadows();
    const el = scrollerRef.current;
    if (!el) return;
    el.addEventListener("scroll", updateScrollShadows, { passive: true });
    window.addEventListener("resize", updateScrollShadows);
    return () => {
      el.removeEventListener("scroll", updateScrollShadows);
      window.removeEventListener("resize", updateScrollShadows);
    };
  }, []);

  useEffect(() => {
    setSelectedFileIndex(0);
  }, [activeTab]);

  const scrollBy = (delta) => {
    scrollerRef.current?.scrollBy({ left: delta, behavior: "smooth" });
  };

  if (!projectData) return null;

  const copyToClipboard = (text) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getBackendFiles = () => {
    const data = projectData?.backend_code;
    if (!data) return [];
    const list = [];
    if (data.main_file) {
      list.push({ name: data.main_file_name || "main.py", code: data.main_file });
    }
    const ext = (data.main_file_name || "main.py").endsWith(".py") ? ".py" : ".js";
    if (data.models_code) {
      list.push({ name: `models${ext}`, code: data.models_code });
    }
    if (data.routes_code) {
      list.push({ name: `routes${ext}`, code: data.routes_code });
    }
    if (data.services_code) {
      list.push({ name: `services${ext}`, code: data.services_code });
    }
    if (data.dependency_manifest) {
      list.push({ name: data.dependency_manifest_name || "requirements.txt", code: data.dependency_manifest });
    }
    if (data.dockerfile) {
      list.push({ name: "Dockerfile", code: data.dockerfile });
    }
    if (data.extra_files) {
      data.extra_files.forEach((f) => {
        list.push({ name: f.path || f.filename || "file", code: f.code });
      });
    }
    return list;
  };

  const getFrontendFiles = () => {
    const data = projectData?.frontend_code;
    if (!data) return [];
    const list = [];
    if (data.main_app_code) {
      list.push({ name: data.main_app_file_name || "App.jsx", code: data.main_app_code });
    }
    if (data.entry_point_code) {
      list.push({ name: data.entry_point_file_name || "main.jsx", code: data.entry_point_code });
    }
    if (data.api_client_code) {
      list.push({ name: "api.js", code: data.api_client_code });
    }
    if (data.styles_code) {
      list.push({ name: "index.css", code: data.styles_code });
    }
    if (data.index_html) {
      list.push({ name: "index.html", code: data.index_html });
    }
    if (data.package_json) {
      list.push({ name: "package.json", code: data.package_json });
    }
    if (data.dockerfile) {
      list.push({ name: "Dockerfile", code: data.dockerfile });
    }
    if (data.components_code) {
      data.components_code.forEach((c) => {
        list.push({ name: `components/${c.filename}`, code: c.code });
      });
    }
    return list;
  };

  const renderFileViewer = (files, framework) => {
    if (!files || files.length === 0) {
      return (
        <div className="flex flex-col items-center justify-center gap-3 py-16 text-slate-500">
          <Inbox className="w-8 h-8" />
          <p className="text-sm font-medium">No files generated for this stage.</p>
        </div>
      );
    }
    const currentFile = files[selectedFileIndex] || files[0] || { name: "", code: "" };

    return (
      <div className="flex flex-col md:flex-row gap-6">
        {/* File Sidebar */}
        <div className="w-full md:w-64 flex-shrink-0 bg-slate-950/40 border border-slate-800/80 rounded-xl overflow-hidden flex flex-col max-h-[480px]">
          <div className="px-4 py-3 bg-slate-900/60 border-b border-slate-800/80 flex items-center justify-between">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wide">Workspace</span>
            {framework && (
              <span className="px-2 py-0.5 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-md text-[10px] font-bold uppercase">
                {framework}
              </span>
            )}
          </div>
          <div className="overflow-y-auto p-2 space-y-1">
            {files.map((file, idx) => (
              <button
                key={idx}
                onClick={() => setSelectedFileIndex(idx)}
                className={`w-full text-left px-3 py-2 rounded-lg text-xs font-semibold font-mono flex items-center gap-2 transition-all ${
                  selectedFileIndex === idx
                    ? "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/40 border border-transparent"
                }`}
              >
                <FileText className="w-3.5 h-3.5 flex-shrink-0" />
                <span className="truncate">{file.name}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Code Content */}
        <div className="flex-1 min-w-0 flex flex-col bg-slate-950/40 border border-slate-800/80 rounded-xl overflow-hidden">
          <div className="px-4 py-3 bg-slate-900/60 border-b border-slate-800/80 flex items-center justify-between">
            <span className="text-xs font-bold font-mono text-slate-300 truncate">{currentFile.name}</span>
            <button
              onClick={() => copyToClipboard(currentFile.code)}
              className="px-2.5 py-1 bg-slate-950 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-slate-200 rounded-md transition-all flex items-center gap-1.5 text-[10px] font-bold"
            >
              {copied ? (
                <>
                  <Check className="w-3 h-3 text-emerald-400" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="w-3 h-3" />
                  Copy File
                </>
              )}
            </button>
          </div>
          <pre className="text-xs font-mono p-4 overflow-x-auto text-slate-300 max-h-[420px] overflow-y-auto leading-relaxed whitespace-pre-wrap">
            {currentFile.code || "// Empty file"}
          </pre>
        </div>
      </div>
    );
  };

  const currentMeta = ALL_TABS.find((t) => t.id === activeTab);
  const currentData = currentMeta ? projectData[currentMeta.dataKey] : null;
  const formattedContent = currentData ? JSON.stringify(currentData, null, 2) : "No data available";
  const accent = ACCENT_CLASSES[currentMeta?.accent] || ACCENT_CLASSES.indigo;

  return (
    <div className="w-full max-w-6xl mx-auto glass rounded-2xl border border-slate-800 overflow-hidden">
      {/* ── Grouped, horizontally-scrollable tab bar ─────────────────────── */}
      <div className="relative bg-slate-950/40 border-b border-slate-800">
        {canScrollLeft && (
          <button
            onClick={() => scrollBy(-220)}
            aria-label="Scroll tabs left"
            className="absolute left-0 top-0 bottom-0 z-20 flex items-center px-1.5 bg-gradient-to-r from-slate-950 via-slate-950/90 to-transparent"
          >
            <ChevronLeft className="w-4 h-4 text-slate-400" />
          </button>
        )}
        {canScrollRight && (
          <button
            onClick={() => scrollBy(220)}
            aria-label="Scroll tabs right"
            className="absolute right-0 top-0 bottom-0 z-20 flex items-center px-1.5 bg-gradient-to-l from-slate-950 via-slate-950/90 to-transparent"
          >
            <ChevronRight className="w-4 h-4 text-slate-400" />
          </button>
        )}

        <div
          ref={scrollerRef}
          className="flex items-stretch overflow-x-auto no-scrollbar scroll-smooth"
        >
          {TAB_GROUPS.map((group, gi) => {
            const groupAccent = ACCENT_CLASSES[group.accent];
            return (
              <div key={group.label} className="flex flex-col shrink-0">
                <span className={`text-[10px] font-bold uppercase tracking-widest px-4 pt-3 pb-1 ${groupAccent.eyebrow}`}>
                  {String(gi + 1).padStart(2, "0")} · {group.label}
                </span>
                <div className="flex">
                  {group.tabs.map((tab) => {
                    const Icon = tab.icon;
                    const isActive = activeTab === tab.id;
                    return (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex items-center gap-2 px-4 py-3 text-sm font-medium whitespace-nowrap transition-all outline-none border-b-2 focus-visible:ring-2 focus-visible:ring-indigo-400/60 ${
                          isActive
                            ? groupAccent.active
                            : "border-transparent text-slate-400 hover:text-white hover:bg-slate-900/50"
                        }`}
                      >
                        <Icon className="w-4 h-4" />
                        {tab.label}
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Content header: current section + copy action ────────────────── */}
      <div className="flex items-center justify-between px-6 pt-5">
        <div className="flex items-center gap-2">
          <span className={`w-1.5 h-1.5 rounded-full ${accent.dot}`} />
          <h3 className="text-sm font-bold text-white tracking-wide">{currentMeta?.label}</h3>
        </div>
        {!["backend", "frontend"].includes(activeTab) && (
          <button
            onClick={() => copyToClipboard(formattedContent)}
            disabled={!currentData}
            className="p-2.5 bg-slate-900 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed border border-slate-800 hover:border-slate-700 text-slate-300 rounded-lg transition-all flex items-center gap-2 text-xs font-semibold"
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
        )}
      </div>

      <div className="p-6 bg-slate-950/20">
        {!currentData && (
          <div className="flex flex-col items-center justify-center gap-3 py-16 text-slate-500">
            <Inbox className="w-8 h-8" />
            <p className="text-sm font-medium">Nothing here yet — this stage hasn't produced output.</p>
          </div>
        )}

        {activeTab === "requirements" && currentData && (
          <div className="space-y-6 text-slate-300">
            <div>
              <h3 className="text-2xl font-bold text-white mb-1">{currentData.project_name}</h3>
              <p className="text-slate-400">{currentData.description}</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800/80">
                <h4 className="font-bold text-indigo-400 mb-3 text-sm tracking-wider uppercase">Features</h4>
                <ul className="list-disc pl-5 space-y-1.5 text-sm">
                  {currentData.features?.map((f, i) => <li key={i}>{f}</li>)}
                </ul>
              </div>
              <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800/80">
                <h4 className="font-bold text-purple-400 mb-3 text-sm tracking-wider uppercase">Target Users</h4>
                <ul className="list-disc pl-5 space-y-1.5 text-sm">
                  {currentData.target_users?.map((u, i) => <li key={i}>{u}</li>)}
                </ul>
              </div>
            </div>
            <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800/80">
              <h4 className="font-bold text-emerald-400 mb-3 text-sm tracking-wider uppercase">Suggested Tech Stack</h4>
              <div className="flex flex-wrap gap-2">
                {currentData.tech_stack?.map((t, i) => (
                  <span key={i} className="px-3 py-1 bg-slate-800 border border-slate-700 text-slate-200 rounded-full text-xs font-semibold">
                    {t}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === "architecture" && currentData && (
          <div className="space-y-6 text-slate-300">
            <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800/80">
              <h4 className="font-bold text-indigo-400 mb-2 text-sm tracking-wider uppercase">System Design</h4>
              <p className="text-sm whitespace-pre-line leading-relaxed">{currentData.system_design}</p>
            </div>
            <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800/80">
              <h4 className="font-bold text-purple-400 mb-2 text-sm tracking-wider uppercase">Components</h4>
              <ul className="list-disc pl-5 space-y-1 text-sm">
                {currentData.components?.map((c, i) => <li key={i}>{c}</li>)}
              </ul>
            </div>
            <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800/80">
              <h4 className="font-bold text-emerald-400 mb-2 text-sm tracking-wider uppercase">API Design Spec</h4>
              <pre className="text-xs font-mono bg-slate-950 p-4 rounded-lg overflow-x-auto text-slate-300 border border-slate-800">
                {currentData.api_design}
              </pre>
            </div>
          </div>
        )}

        {activeTab === "database" && currentData && (
          <div className="space-y-6 text-slate-300">
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-slate-400">Database Engine:</span>
              <span className="px-3 py-1 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-lg text-xs font-bold uppercase">
                {currentData.database_type}
              </span>
            </div>
            <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800/80">
              <h4 className="font-bold text-indigo-400 mb-3 text-sm tracking-wider uppercase">Migration SQL Schema</h4>
              <pre className="text-xs font-mono bg-slate-950 p-4 rounded-lg overflow-x-auto text-slate-300 border border-slate-800 font-semibold leading-relaxed">
                {currentData.migration_sql}
              </pre>
            </div>
          </div>
        )}

        {activeTab === "backend" && currentData && renderFileViewer(getBackendFiles(), currentData.framework)}

        {activeTab === "frontend" && currentData && renderFileViewer(getFrontendFiles(), currentData.framework)}

        {activeTab === "review" && currentData && (
          <div className="space-y-6 text-slate-300">
            <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800/80">
              <h4 className="font-bold text-indigo-400 mb-2 text-sm tracking-wider uppercase">Review Report</h4>
              <p className="text-sm italic mb-4">"{currentData.overall_quality}"</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <h5 className="font-bold text-rose-400 text-xs mb-2 uppercase">Backend Concerns</h5>
                  <ul className="list-disc pl-5 text-sm space-y-1">
                    {currentData.backend_issues?.map((iss, i) => <li key={i}>{iss}</li>)}
                  </ul>
                </div>
                <div>
                  <h5 className="font-bold text-amber-400 text-xs mb-2 uppercase">Recommendations</h5>
                  <ul className="list-disc pl-5 text-sm space-y-1">
                    {currentData.recommendations?.map((rec, i) => <li key={i}>{rec}</li>)}
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "security" && currentData && (
          <div className="space-y-6 text-slate-300">
            <div className="p-5 rounded-xl bg-slate-900/50 border border-slate-800/80">
              <h4 className="font-bold text-rose-500 mb-2 text-sm tracking-wider uppercase flex items-center gap-2">
                Security Risk Level: <span className="text-white uppercase px-2 py-0.5 bg-rose-500/20 border border-rose-500/30 rounded text-xs">{currentData.risk_level}</span>
              </h4>
              <ul className="list-disc pl-5 text-sm space-y-2 mt-4">
                {currentData.vulnerabilities?.map((vuln, i) => (
                  <li key={i}>
                    <strong className="text-slate-200">{vuln.title}</strong>: {vuln.description}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {currentData && !["requirements", "architecture", "database", "backend", "frontend", "review", "security"].includes(activeTab) && (
          <div className="max-h-[500px] overflow-y-auto">
            <pre className="text-xs font-mono bg-slate-950 p-4 rounded-lg overflow-x-auto text-slate-300 border border-slate-800 leading-relaxed font-semibold">
              {formattedContent}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}