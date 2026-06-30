import React, { useEffect, useRef } from "react";
import { Terminal } from "lucide-react";

const TYPE_STYLES = {
  info:    { dot: "bg-indigo-400",  text: "text-indigo-300" },
  success: { dot: "bg-emerald-400", text: "text-emerald-300" },
  warning: { dot: "bg-amber-400",   text: "text-amber-300"  },
  error:   { dot: "bg-rose-400",    text: "text-rose-300"   },
};

export default function LiveTerminal({ events }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events]);

  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="flex items-center gap-2 mb-3">
        <Terminal className="w-4 h-4 text-slate-400" />
        <span className="text-xs font-semibold text-slate-400 uppercase tracking-widest">
          Live Agent Activity
        </span>
        <span className="ml-auto text-xs text-slate-600">{events.length} events</span>
      </div>

      <div className="font-mono text-xs bg-[#0a0b0f] border border-slate-800/70 rounded-xl overflow-hidden">
        {/* Terminal title bar */}
        <div className="flex items-center gap-1.5 px-4 py-2.5 border-b border-slate-800/50 bg-slate-950/50">
          <span className="w-3 h-3 rounded-full bg-rose-500/70" />
          <span className="w-3 h-3 rounded-full bg-amber-500/70" />
          <span className="w-3 h-3 rounded-full bg-emerald-500/70" />
          <span className="ml-3 text-slate-600 text-[10px]">codesmith-ai — agent output stream</span>
        </div>

        {/* Log body */}
        <div className="p-4 space-y-1.5 max-h-72 overflow-y-auto">
          {events.length === 0 ? (
            <p className="text-slate-600 italic">Waiting for agents to start...</p>
          ) : (
            events.map((ev, i) => {
              const style = TYPE_STYLES[ev.event_type] || TYPE_STYLES.info;
              return (
                <div key={i} className="flex items-start gap-2.5 leading-relaxed">
                  {/* Timestamp-style index */}
                  <span className="text-slate-700 shrink-0 select-none w-6 text-right">{i + 1}</span>
                  {/* Colored dot */}
                  <span className={`w-1.5 h-1.5 rounded-full mt-1.5 shrink-0 ${style.dot}`} />
                  {/* Agent badge */}
                  <span className="text-slate-500 shrink-0">[{ev.agent?.replace("Agent", "")}]</span>
                  {/* Message */}
                  <span className={`${style.text} flex-1`}>{ev.message}</span>
                  {/* Detail */}
                  {ev.detail && (
                    <span className="text-slate-600 ml-1 shrink-0 max-w-xs truncate">
                      — {ev.detail}
                    </span>
                  )}
                </div>
              );
            })
          )}
          <div ref={bottomRef} />
        </div>
      </div>
    </div>
  );
}
