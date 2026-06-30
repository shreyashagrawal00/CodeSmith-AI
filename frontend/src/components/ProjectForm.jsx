import React, { useState } from "react";
import { Sparkles, Terminal } from "lucide-react";

export default function ProjectForm({ onSubmit, loading }) {
  const [prompt, setPrompt] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!prompt.trim()) return;
    onSubmit(prompt);
  };

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-3xl mx-auto space-y-6">
      <div className="relative glass rounded-2xl p-6 glow-indigo border border-indigo-500/20">
        <label className="block text-sm font-semibold tracking-wider uppercase text-indigo-400 mb-2">
          What would you like to build?
        </label>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Build a Hospital Management System using React, FastAPI, PostgreSQL and Docker..."
          disabled={loading}
          rows={4}
          className="w-full bg-slate-950/50 text-white placeholder-slate-500 border border-slate-800 rounded-xl p-4 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all resize-none text-base font-medium"
        />
        <div className="flex justify-end mt-4">
          <button
            type="submit"
            disabled={loading || !prompt.trim()}
            className="flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-semibold rounded-xl transition-all duration-300 disabled:opacity-40 disabled:cursor-not-allowed hover:shadow-lg hover:shadow-indigo-500/20 hover:scale-[1.02]"
          >
            {loading ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Orchestrating...
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                Spawn Agents
              </>
            )}
          </button>
        </div>
      </div>
      
      <div className="flex items-center justify-center gap-6 text-xs text-slate-500 font-medium tracking-wide">
        <span className="flex items-center gap-1.5"><Terminal className="w-3.5 h-3.5 text-indigo-400" /> Multi-Agent Collaboration</span>
        <span className="h-1.5 w-1.5 rounded-full bg-slate-800"></span>
        <span className="flex items-center gap-1.5"><Sparkles className="w-3.5 h-3.5 text-purple-400" /> LangGraph Orchestrated</span>
      </div>
    </form>
  );
}
