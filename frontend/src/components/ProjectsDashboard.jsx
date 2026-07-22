import React, { useState, useEffect } from "react";
import {
  Folder,
  CheckCircle,
  XCircle,
  Clock,
  Loader,
  Download,
  Eye,
  Search,
  Star,
  Calendar,
  RefreshCw,
  Trash2,
  AlertTriangle,
} from "lucide-react";

const STATUS_CONFIG = {
  completed: {
    label: "Completed",
    color: "text-emerald-400",
    bg: "bg-emerald-500/10 border-emerald-500/20",
    dot: "bg-emerald-500",
  },
  failed: {
    label: "Failed",
    color: "text-rose-400",
    bg: "bg-rose-500/10 border-rose-500/20",
    dot: "bg-rose-500",
  },
  paused: {
    label: "Paused",
    color: "text-amber-400",
    bg: "bg-amber-500/10 border-amber-500/20",
    dot: "bg-amber-400",
  },
  running: {
    label: "Running",
    color: "text-indigo-400",
    bg: "bg-indigo-500/10 border-indigo-500/20",
    dot: "bg-indigo-400",
  },
};

function formatDate(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function QualityBar({ score }) {
  if (!score) return null;
  const pct = Math.min(100, Math.max(0, score));
  const color =
    pct >= 80
      ? "from-emerald-500 to-teal-400"
      : pct >= 60
      ? "from-amber-500 to-yellow-400"
      : "from-rose-500 to-orange-400";
  return (
    <div className="flex items-center gap-2">
      <Star className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
      <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full bg-gradient-to-r ${color} transition-all`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs text-slate-400 font-mono w-8 text-right">
        {pct.toFixed(0)}
      </span>
    </div>
  );
}

function ProjectCard({ project, onOpen, onDownload, onDelete }) {
  const cfg = STATUS_CONFIG[project.status] || STATUS_CONFIG.failed;
  const isCompleted = project.status === "completed";

  return (
    <div className="group flex flex-col gap-3 p-5 bg-slate-900/40 hover:bg-slate-900/70 border border-slate-800/80 hover:border-indigo-500/30 rounded-2xl transition-all duration-300">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="p-2 bg-indigo-500/10 border border-indigo-500/20 rounded-lg flex-shrink-0">
            <Folder className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="min-w-0">
            <h3 className="text-sm font-bold text-white truncate">
              {project.project_name || "(Untitled Project)"}
            </h3>
            <p className="text-xs text-slate-500 truncate mt-0.5 italic">
              &quot;{project.user_prompt}&quot;
            </p>
          </div>
        </div>
        <span
          className={`flex-shrink-0 flex items-center gap-1.5 px-2.5 py-1 text-xs font-semibold rounded-full border ${cfg.bg} ${cfg.color}`}
        >
          <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot} ${project.status === "running" ? "animate-pulse" : ""}`} />
          {cfg.label}
        </span>
      </div>

      {/* Description */}
      {project.description && (
        <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
          {project.description}
        </p>
      )}

      {/* Quality score */}
      {project.quality_score > 0 && (
        <QualityBar score={project.quality_score} />
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-2 border-t border-slate-800/60">
        <div className="flex items-center gap-1.5 text-xs text-slate-500">
          <Calendar className="w-3 h-3" />
          {formatDate(project.created_at)}
        </div>
        <div className="flex items-center gap-2">
          {isCompleted && (
            <button
              onClick={() => onDownload(project.job_id)}
              title="Download ZIP"
              className="p-1.5 rounded-lg text-slate-500 hover:text-emerald-400 hover:bg-emerald-500/10 transition-all"
            >
              <Download className="w-3.5 h-3.5" />
            </button>
          )}
          <button
            onClick={() => onDelete(project)}
            title="Delete Project"
            className="p-1.5 rounded-lg text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition-all"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => onOpen(project.job_id)}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600/20 hover:bg-indigo-600/40 border border-indigo-500/20 hover:border-indigo-500/40 text-indigo-300 text-xs font-semibold rounded-lg transition-all"
          >
            <Eye className="w-3 h-3" />
            Open
          </button>
        </div>
      </div>
    </div>
  );
}

export default function ProjectsDashboard({ onOpenProject }) {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [projectToDelete, setProjectToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const fetchProjects = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("http://127.0.0.1:8000/api/v1/projects?limit=100");
      if (!res.ok) throw new Error("Failed to fetch projects");
      const data = await res.json();
      setProjects(data.projects || []);
    } catch (e) {
      setError(e.message || "Could not load projects");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleDownload = (jobId) => {
    window.open(`http://127.0.0.1:8000/api/v1/download/${jobId}`);
  };

  const handleDeleteConfirm = async (jobId) => {
    setDeleting(true);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/v1/projects/${jobId}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Failed to delete project");
      
      setProjects((prev) => prev.filter((p) => p.job_id !== jobId));
      setProjectToDelete(null);
    } catch (e) {
      alert(e.message || "Could not delete project");
    } finally {
      setDeleting(false);
    }
  };

  const filtered = projects.filter((p) => {
    const matchesFilter = filter === "all" || p.status === filter;
    const q = search.toLowerCase();
    const matchesSearch =
      !q ||
      (p.project_name || "").toLowerCase().includes(q) ||
      (p.user_prompt || "").toLowerCase().includes(q) ||
      (p.description || "").toLowerCase().includes(q);
    return matchesFilter && matchesSearch;
  });

  const counts = {
    all: projects.length,
    completed: projects.filter((p) => p.status === "completed").length,
    paused: projects.filter((p) => p.status === "paused").length,
    failed: projects.filter((p) => p.status === "failed").length,
  };

  return (
    <div className="w-full max-w-7xl mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-extrabold text-white">My Projects</h2>
          <p className="text-sm text-slate-500 mt-1">
            {projects.length} project{projects.length !== 1 ? "s" : ""} — persisted across restarts
          </p>
        </div>
        <button
          onClick={fetchProjects}
          className="flex items-center gap-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 text-slate-300 text-xs font-semibold rounded-lg transition-all self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Search + Filter bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name, prompt, or description…"
            className="w-full pl-9 pr-4 py-2.5 bg-slate-900 border border-slate-800 focus:border-indigo-500/50 rounded-xl text-sm text-slate-200 placeholder-slate-600 outline-none transition-all"
          />
        </div>
        <div className="flex gap-2 flex-wrap">
          {["all", "completed", "paused", "failed"].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-2 rounded-lg text-xs font-semibold border transition-all ${
                filter === f
                  ? "bg-indigo-600 border-indigo-500 text-white"
                  : "bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700"
              }`}
            >
              {f === "all" ? "All" : f.charAt(0).toUpperCase() + f.slice(1)}
              <span className="ml-1.5 opacity-60">({counts[f] ?? 0})</span>
            </button>
          ))}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-xl text-rose-400 text-sm text-center">
          {error}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-24 gap-3 text-slate-500">
          <Loader className="w-5 h-5 animate-spin" />
          <span className="text-sm">Loading projects…</span>
        </div>
      )}

      {/* Empty */}
      {!loading && !error && filtered.length === 0 && (
        <div className="flex flex-col items-center justify-center py-24 gap-3 text-slate-500">
          <Folder className="w-10 h-10 opacity-30" />
          <p className="text-sm">
            {search || filter !== "all"
              ? "No projects match your search."
              : "No projects yet. Generate your first project!"}
          </p>
        </div>
      )}

      {/* Grid */}
      {!loading && filtered.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((project) => (
            <ProjectCard
              key={project.job_id}
              project={project}
              onOpen={onOpenProject}
              onDownload={handleDownload}
              onDelete={setProjectToDelete}
            />
          ))}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {projectToDelete && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div 
            className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl text-left animate-scale-in"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center gap-3 text-rose-500 mb-4">
              <div className="p-2 bg-rose-500/10 rounded-lg">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-white">Delete Project</h3>
            </div>
            
            <p className="text-sm text-slate-400 mb-2 leading-relaxed">
              Are you sure you want to delete <span className="text-slate-200 font-semibold">"{projectToDelete.project_name || '(Untitled Project)'}"</span>?
            </p>
            <p className="text-xs text-rose-400/80 mb-6 bg-rose-500/5 border border-rose-500/10 rounded-lg p-2.5">
              This will permanently delete the project from the database, erase all generated code/files on disk, and remove the zip archive. This action cannot be undone.
            </p>

            <div className="flex justify-end gap-3">
              <button
                onClick={() => setProjectToDelete(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 rounded-lg transition-all"
                disabled={deleting}
              >
                Cancel
              </button>
              <button
                onClick={() => handleDeleteConfirm(projectToDelete.job_id)}
                className="flex items-center gap-1.5 px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold rounded-lg transition-all disabled:opacity-50"
                disabled={deleting}
              >
                {deleting ? (
                  <>
                    <Loader className="w-3.5 h-3.5 animate-spin" />
                    Deleting...
                  </>
                ) : (
                  "Delete Project"
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
