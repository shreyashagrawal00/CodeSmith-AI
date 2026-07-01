import React, { useState, useEffect, useCallback } from "react";
import { Terminal, Download, Cpu, RefreshCw, ExternalLink, Globe } from "lucide-react";
import ProjectForm from "./components/ProjectForm";
import ProgressBar from "./components/ProgressBar";
import ProjectOutputViewer from "./components/ProjectOutputViewer";
import LiveTerminal from "./components/LiveTerminal";

export default function App() {
  const [loading, setLoading] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState("idle");
  const [currentAgent, setCurrentAgent] = useState("");
  const [log, setLog] = useState([]);
  const [liveEvents, setLiveEvents] = useState([]);
  const [projectData, setProjectData] = useState(null);
  const [error, setError] = useState(null);
  const [feedback, setFeedback] = useState("");
  const [submitLoading, setSubmitLoading] = useState(false);

  const handleApproval = async (approved) => {
    setSubmitLoading(true);
    setError(null);
    try {
      const response = await fetch(`http://localhost:8000/api/v1/approve/${jobId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ approved, feedback }),
      });
      const data = await response.json();
      if (data.status === "resumed") {
        setStatus("running");
        setFeedback("");
      } else {
        setError(data.message || "Failed to submit approval.");
      }
    } catch {
      setError("Failed to connect to backend for approval.");
    } finally {
      setSubmitLoading(false);
    }
  };

  const startGeneration = async (prompt) => {
    setLoading(true);
    setError(null);
    setProjectData(null);
    try {
      const response = await fetch("http://localhost:8000/api/v1/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      const data = await response.json();
      setJobId(data.job_id);
      setStatus(data.status);
      setLog([]);
      setLiveEvents([]);
    } catch {
      setError("Failed to connect to CodeSmith AI Backend.");
      setLoading(false);
    }
  };

  const fetchResult = useCallback(async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/result/${jobId}`);
      const data = await response.json();
      setProjectData(data);
      setLoading(false);
    } catch {
      setError("Failed to fetch generated project content.");
      setLoading(false);
    }
  }, [jobId]);

  const startPolling = useCallback(() => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`http://localhost:8000/api/v1/status/${jobId}`);
        const data = await response.json();
        setStatus(data.status);
        setCurrentAgent(data.current_agent);
        setLog(data.log || []);
        
        if (data.status === "completed" || data.status === "paused") {
          clearInterval(interval);
          fetchResult();
        } else if (data.status === "failed") {
          clearInterval(interval);
          setError(data.error || "Workflow failed");
          setLoading(false);
        }
      } catch {
        clearInterval(interval);
      }
    }, 2000);
  }, [jobId, fetchResult]);

  useEffect(() => {
    if (!jobId || status === "completed" || status === "failed" || status === "paused") return;

    let socket;
    try {
      socket = new WebSocket(`ws://localhost:8000/ws/${jobId}`);
      
      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "progress") {
          setCurrentAgent(data.current_agent);
          setStatus(data.job_status);
          setLog((prev) => {
            const exists = prev.some((e) => e.agent === data.agent);
            if (!exists) {
              return [...prev, { agent: data.agent, status: data.status }];
            }
            return prev;
          });
        } else if (data.type === "live") {
          setLiveEvents((prev) => [...prev, data]);
        } else if (data.type === "done") {
          setStatus(data.status);
          if (data.status === "completed" || data.status === "paused") {
            fetchResult();
          } else {
            setError(data.error || "Workflow failed");
            setLoading(false);
          }
        }
      };

      socket.onerror = () => {
        startPolling();
      };
    } catch {
      startPolling();
    }

    return () => {
      if (socket) socket.close();
    };
  }, [jobId, status, startPolling, fetchResult]);

  const handleDownload = () => {
    window.open(`http://localhost:8000/api/v1/download/${jobId}`);
  };

  const resetFlow = () => {
    setJobId(null);
    setStatus("idle");
    setCurrentAgent("");
    setLog([]);
    setLiveEvents([]);
    setProjectData(null);
    setError(null);
  };

  return (
    <div className="relative min-h-screen bg-[#030408] text-slate-100 overflow-hidden flex flex-col">
      {/* Decorative Orbs */}
      <div className="absolute top-0 left-1/4 w-[500px] h-[500px] bg-indigo-900/10 rounded-full blur-[120px] animate-pulse-slow pointer-events-none" />
      <div className="absolute bottom-0 right-1/4 w-[600px] h-[600px] bg-purple-900/10 rounded-full blur-[140px] animate-pulse-slow pointer-events-none" />

      {/* Header */}
      <header className="relative z-10 glass border-b border-slate-900/80 px-8 py-5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-gradient-to-tr from-indigo-500 to-purple-600 rounded-xl shadow-lg shadow-indigo-500/25">
            <Cpu className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              CodeSmith AI
              <span className="text-[10px] bg-indigo-500/15 border border-indigo-500/25 text-indigo-400 px-2 py-0.5 rounded font-extrabold uppercase tracking-widest">v1.0</span>
            </h1>
            <p className="text-xs text-slate-500 font-medium">Autonomous Multi-Agent Software Team</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          {jobId && (
            <button
              onClick={resetFlow}
              className="flex items-center gap-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 text-slate-300 text-xs font-semibold rounded-lg transition-all"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              New Project
            </button>
          )}
        </div>
      </header>

      {/* Main Body */}
      <main className="flex-1 relative z-10 max-w-7xl mx-auto w-full px-6 py-12 flex flex-col items-center justify-center gap-12">
        {status === "idle" && (
          <div className="text-center space-y-4 max-w-2xl animate-fade-in">
            <h2 className="text-4xl md:text-5xl font-extrabold text-white leading-tight">
              An entire software team in <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-rose-400 bg-clip-text text-transparent">one prompt.</span>
            </h2>
            <p className="text-base text-slate-400 font-medium max-w-lg mx-auto">
              Transform your idea into a complete production-ready project: full backend APIs, database schemas, responsive React pages, security audits, tests, Docker, and CI/CD pipelines.
            </p>
          </div>
        )}

        {status === "idle" && (
          <ProjectForm onSubmit={startGeneration} loading={loading} />
        )}

        {status !== "idle" && (
          <>
            <ProgressBar currentAgent={currentAgent} log={log} status={status} />
            
            {status === "paused" && (
              <div className="w-full max-w-2xl p-6 bg-slate-900/40 border border-indigo-500/30 rounded-2xl space-y-4 shadow-lg shadow-indigo-500/5 animate-fade-in relative z-10">
                <div className="flex items-center gap-3">
                  <span className="w-3.5 h-3.5 rounded-full bg-amber-500 animate-pulse" />
                  <h3 className="text-lg font-bold text-white">
                    Human Review Required — Paused at {currentAgent === "approval_gate" ? "Requirements & Architecture" : currentAgent === "database_designer" ? "Database Design" : currentAgent === "deployment" ? "Deployment Review" : currentAgent}
                  </h3>
                </div>
                <p className="text-sm text-slate-400">
                  Please review the generated output below. You can approve to proceed to the next step, or request revisions by typing feedback below and clicking Request Changes.
                </p>
                <textarea
                  value={feedback}
                  onChange={(e) => setFeedback(e.target.value)}
                  placeholder="Provide review feedback (optional if approving)..."
                  className="w-full h-24 bg-slate-950 border border-slate-800 focus:border-indigo-500/50 rounded-xl p-4 text-sm text-slate-200 placeholder-slate-600 outline-none transition-all resize-none"
                />
                <div className="flex gap-4">
                  <button
                    disabled={submitLoading}
                    onClick={() => handleApproval(true)}
                    className="flex-1 py-3 px-6 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold rounded-xl transition-all duration-300 shadow-md shadow-emerald-500/10 hover:scale-[1.01] disabled:opacity-50 cursor-pointer"
                  >
                    {submitLoading ? "Submitting..." : "Approve & Proceed"}
                  </button>
                  <button
                    disabled={submitLoading}
                    onClick={() => handleApproval(false)}
                    className="flex-1 py-3 px-6 bg-slate-950 hover:bg-slate-900 border border-rose-500/30 hover:border-rose-500/50 text-rose-400 font-bold rounded-xl transition-all duration-300 hover:scale-[1.01] disabled:opacity-50 cursor-pointer"
                  >
                    {submitLoading ? "Submitting..." : "Request Changes"}
                  </button>
                </div>
              </div>
            )}

            <LiveTerminal events={liveEvents} />
          </>
        )}

        {error && (
          <div className="w-full max-w-2xl p-5 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-xl text-center text-sm font-semibold">
            {error}
          </div>
        )}

        {(status === "completed" || status === "paused") && projectData && (
          <div className="w-full space-y-6 flex flex-col items-center">
            {status === "completed" && (
              <div className="flex flex-wrap items-center justify-center gap-4">
                <button
                  onClick={handleDownload}
                  className="flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold rounded-xl transition-all duration-300 shadow-lg shadow-emerald-500/20 hover:scale-[1.02]"
                >
                  <Download className="w-5 h-5" />
                  Download Complete Project ZIP
                </button>

                {projectData.preview && (
                  <div className="flex items-center gap-3">
                    {projectData.preview.frontend_url && (
                      <a
                        href={projectData.preview.frontend_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 px-6 py-4 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl transition-all duration-300 shadow-lg shadow-indigo-500/20 hover:scale-[1.02]"
                      >
                        <Globe className="w-5 h-5" />
                        Open Live Frontend
                        <ExternalLink className="w-4.5 h-4.5" />
                      </a>
                    )}
                    {projectData.preview.backend_url && (
                      <a
                        href={`${projectData.preview.backend_url}/docs`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 px-6 py-4 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-200 font-bold rounded-xl transition-all duration-300 hover:scale-[1.02]"
                      >
                        <Terminal className="w-5 h-5" />
                        API Swagger Docs
                        <ExternalLink className="w-4.5 h-4.5" />
                      </a>
                    )}
                  </div>
                )}
              </div>
            )}

            {status === "completed" && projectData.preview && projectData.preview.frontend_url && (
              <div className="w-full max-w-6xl rounded-2xl border border-slate-800 bg-slate-950/40 p-4 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div className="flex items-center gap-2 text-slate-400 text-sm">
                    <span className="w-3.5 h-3.5 rounded-full bg-emerald-500 animate-pulse" />
                    <span>Live App Preview running on {projectData.preview.frontend_url}</span>
                  </div>
                </div>
                <div className="w-full aspect-video rounded-xl bg-slate-900 overflow-hidden border border-slate-800/80">
                  <iframe
                    src={projectData.preview.frontend_url}
                    title="Live App Preview"
                    className="w-full h-full border-none bg-slate-950"
                    sandbox="allow-scripts allow-same-origin allow-forms"
                  />
                </div>
              </div>
            )}

            <ProjectOutputViewer projectData={projectData} />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="py-6 border-t border-slate-900/50 text-center text-xs text-slate-600 font-medium relative z-10">
        © 2026 CodeSmith AI Engineering. Powered by LangGraph & Gemini.
      </footer>
    </div>
  );
}
