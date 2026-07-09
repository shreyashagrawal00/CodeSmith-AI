import React, { useState, useEffect, useCallback, useRef } from "react";
import { Terminal, Download, Cpu, RefreshCw, ExternalLink, Globe } from "lucide-react";
import ProjectForm from "./components/ProjectForm";
import ProgressBar from "./components/ProgressBar";
import ProjectOutputViewer from "./components/ProjectOutputViewer";
import LiveTerminal from "./components/LiveTerminal";

const AUTO_PROCEED_SECONDS = 10;

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
  const [autoProceedSeconds, setAutoProceedSeconds] = useState(null);
  const [autoProceedCancelled, setAutoProceedCancelled] = useState(false);
  // Refs mirror the state above so the interval callback always sees the
  // latest value rather than a stale closure from when the interval was set up.
  const autoProceedCancelledRef = useRef(false);
  const handleApprovalRef = useRef(null);

  const handleSkip = async (agentId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/skip/${jobId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ agent: agentId }),
      });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        setError(data.detail || `Failed to skip ${agentId}.`);
      }
    } catch {
      setError(`Failed to connect to backend to skip ${agentId}.`);
    }
  };

  const cancelAutoProceed = useCallback(() => {
    autoProceedCancelledRef.current = true;
    setAutoProceedCancelled(true);
    setAutoProceedSeconds(null);
  }, []);

  const handleApproval = useCallback(async (approved) => {
    // Whichever path triggers this (manual click or the timer), stop the
    // countdown immediately so it can't also fire afterward.
    autoProceedCancelledRef.current = true;
    setAutoProceedCancelled(true);
    setAutoProceedSeconds(null);

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
  }, [jobId, feedback]);

  // Keep a ref to the latest handleApproval so the countdown effect below
  // doesn't need it in its dependency array (which would restart the timer
  // every time `feedback` changes as the user types).
  useEffect(() => {
    handleApprovalRef.current = handleApproval;
  }, [handleApproval]);

  // Auto-proceed countdown: whenever the workflow pauses for human review,
  // start a 10s countdown. If the user doesn't manually approve/reject
  // before it runs out, auto-approve so the pipeline isn't stuck waiting
  // on someone who stepped away.
  useEffect(() => {
    if (status !== "paused") {
      setAutoProceedSeconds(null);
      return;
    }

    autoProceedCancelledRef.current = false;
    setAutoProceedCancelled(false);
    setAutoProceedSeconds(AUTO_PROCEED_SECONDS);

    const interval = setInterval(() => {
      if (autoProceedCancelledRef.current) {
        clearInterval(interval);
        return;
      }
      setAutoProceedSeconds((prev) => {
        if (prev === null) return null;
        if (prev <= 1) {
          clearInterval(interval);
          if (!autoProceedCancelledRef.current) {
            handleApprovalRef.current?.(true);
          }
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [status, jobId]);

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
      if (!response.ok) return; // e.g. job just flipped to "failed" mid-poll; the status poller already surfaces that error
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
        } else if (data.status === "running") {
          // Also pull whatever partial output exists so far, so completed
          // sections (e.g. Requirements while Architect is still running)
          // are viewable live instead of only at a pause/completion point.
          fetchResult();
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
          // NOTE: deliberately NOT calling setStatus(data.job_status) here.
          // If this message's job_status is already a terminal value
          // ("completed"), setting it immediately re-runs this effect
          // (status is a dependency) and closes the socket right away --
          // racing against the "done" message that's typically sent in the
          // same burst right after this one. If "done" loses that race,
          // fetchResult() never fires and the output viewer never renders,
          // even though status now shows "completed". The "done" handler
          // below is the sole source of truth for terminal status
          // transitions; while running, status is already "running" from
          // when the job started/resumed, so there's nothing to update here.
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
    setLoading(false);
    setSubmitLoading(false);
    setFeedback("");
    setAutoProceedSeconds(null);
    setAutoProceedCancelled(false);
    autoProceedCancelledRef.current = false;
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
            <ProgressBar currentAgent={currentAgent} log={log} status={status} jobId={jobId} onSkip={handleSkip} />
            
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
                {autoProceedSeconds !== null && !autoProceedCancelled && (
                  <div className="flex items-center justify-between gap-3 px-4 py-2.5 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-xs text-indigo-300">
                    <span>Auto-approving and proceeding in {autoProceedSeconds}s if no action is taken…</span>
                    <button
                      onClick={cancelAutoProceed}
                      className="shrink-0 underline decoration-dotted underline-offset-2 hover:text-indigo-200 transition-colors cursor-pointer"
                    >
                      Cancel
                    </button>
                  </div>
                )}
                <textarea
                  value={feedback}
                  onChange={(e) => {
                    setFeedback(e.target.value);
                    if (e.target.value.trim()) cancelAutoProceed();
                  }}
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

            {liveEvents.length > 0 && <LiveTerminal events={liveEvents} />}
          </>
        )}

        {error && (
          <div className="w-full max-w-2xl p-5 bg-rose-500/10 border border-rose-500/20 text-rose-400 rounded-xl text-center text-sm font-semibold">
            {error}
          </div>
        )}

        {(status === "completed" || status === "paused" || status === "running") && projectData && (
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
                        <ExternalLink className="w-4 h-4" />
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
                        <ExternalLink className="w-4 h-4" />
                      </a>
                    )}
                  </div>
                )}

                {projectData.preview && !projectData.preview.frontend_url && !projectData.preview.backend_url && (
                  <div className="flex items-center gap-2 px-4 py-3 bg-amber-500/10 border border-amber-500/30 rounded-xl text-amber-300 text-sm max-w-2xl">
                    <span>
                      Live preview couldn't start:{" "}
                      {projectData.preview.error ||
                        projectData.preview.frontend_error ||
                        projectData.preview.backend_error ||
                        "unknown error — check backend logs."}
                    </span>
                  </div>
                )}

                {projectData.preview && projectData.preview.backend_error && projectData.preview.frontend_url && (
                  <div className="flex items-center gap-2 px-4 py-3 bg-amber-500/10 border border-amber-500/30 rounded-xl text-amber-300 text-sm max-w-2xl">
                    <span>Frontend preview is live, but the backend preview failed to start: {projectData.preview.backend_error}</span>
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