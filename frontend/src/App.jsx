import React, { useState, useEffect } from "react";
import KMapGrid from "./components/KMapGrid";
import TutorSteps from "./components/TutorSteps";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

const PRESETS = [
  {
    label: "4-Var Corner Wrap-Around",
    num_vars: 4,
    minterms: [0, 2, 8, 10],
    dont_cares: [],
  },
  {
    label: "4-Var with Don't-Cares (X)",
    num_vars: 4,
    minterms: [0, 1, 2, 5, 8, 9, 10],
    dont_cares: [3, 7],
  },
  {
    label: "3-Var Standard Function",
    num_vars: 3,
    minterms: [1, 2, 3, 5, 7],
    dont_cares: [],
  },
];

export default function App() {
  const [numVars, setNumVars] = useState(4);
  const [minterms, setMinterms] = useState([0, 2, 8, 10]);
  const [dontCares, setDontCares] = useState([]);
  const [promptText, setPromptText] = useState("");
  const [result, setResult] = useState(null);
  const [hoveredGroupId, setHoveredGroupId] = useState(null);
  const [formMode, setFormMode] = useState("SOP");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const solveGrid = async (v = numVars, m = minterms, d = dontCares) => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE}/solve-grid`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ num_vars: v, minterms: m, dont_cares: d }),
      });
      if (!res.ok) throw new Error("Failed to solve K-Map");
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const solvePrompt = async (e) => {
    e.preventDefault();
    if (!promptText.trim()) return;
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE}/solve-prompt`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt: promptText }),
      });
      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Failed to parse prompt");
      }
      const data = await res.json();
      setNumVars(data.kmap.num_vars);
      setMinterms(data.kmap.minterms);
      setDontCares(data.kmap.dont_cares);
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    solveGrid(numVars, minterms, dontCares);
  }, []);

  const handleToggleCell = (m) => {
    let nextM = [...minterms];
    let nextD = [...dontCares];

    if (nextM.includes(m)) {
      // 1 -> X
      nextM = nextM.filter((x) => x !== m);
      nextD.push(m);
    } else if (nextD.includes(m)) {
      // X -> 0
      nextD = nextD.filter((x) => x !== m);
    } else {
      // 0 -> 1
      nextM.push(m);
    }

    setMinterms(nextM);
    setDontCares(nextD);
    solveGrid(numVars, nextM, nextD);
  };

  const handleVarChange = (newVars) => {
    const maxM = (1 << newVars) - 1;
    const filteredM = minterms.filter((m) => m <= maxM);
    const filteredD = dontCares.filter((d) => d <= maxM);
    setNumVars(newVars);
    setMinterms(filteredM);
    setDontCares(filteredD);
    solveGrid(newVars, filteredM, filteredD);
  };

  const applyPreset = (p) => {
    setNumVars(p.num_vars);
    setMinterms(p.minterms);
    setDontCares(p.dont_cares);
    solveGrid(p.num_vars, p.minterms, p.dont_cares);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 md:p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <header className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800 pb-5">
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">
              Agentic AI Karnaugh Map Solver & Tutor
            </h1>
            <p className="text-sm text-slate-400">
              ESC392 Digital Electronics Lab — Project P7 (Deterministic Gray-Code Grouping + LLM Tutor)
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            {PRESETS.map((p) => (
              <button
                key={p.label}
                onClick={() => applyPreset(p)}
                className="text-xs px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-300 transition"
              >
                {p.label}
              </button>
            ))}
          </div>
        </header>

        {/* Natural Language Prompt Input */}
        <form
          onSubmit={solvePrompt}
          className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col sm:flex-row gap-3"
        >
          <input
            type="text"
            value={promptText}
            onChange={(e) => setPromptText(e.target.value)}
            placeholder='Ask the AI Agent: e.g., "Minimize a 4-variable function with minterms 0, 1, 2, 5, 8, 9, 10 and don&apos;t care 3"'
            className="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-4 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
          <button
            type="submit"
            disabled={loading}
            className="px-5 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-semibold transition"
          >
            {loading ? "Solving..." : "Ask Agent"}
          </button>
        </form>

        {error && (
          <div className="p-3 rounded-lg bg-rose-950/60 border border-rose-500/40 text-rose-300 text-sm">
            {error} — Ensure the FastAPI backend is running on port 8000.
          </div>
        )}

        {/* Controls Bar */}
        <div className="flex flex-wrap items-center justify-between gap-4 bg-slate-900/60 border border-slate-800 rounded-xl px-4 py-3">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400 font-medium">Variables:</span>
            {[2, 3, 4].map((v) => (
              <button
                key={v}
                onClick={() => handleVarChange(v)}
                className={`px-3 py-1 rounded-md text-xs font-mono font-semibold transition ${
                  numVars === v
                    ? "bg-indigo-600 text-white"
                    : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                }`}
              >
                {v} Vars
              </button>
            ))}
          </div>

          <div className="text-xs font-mono text-slate-400">
            Σm({[...minterms].sort((a, b) => a - b).join(", ")})
            {dontCares.length > 0 &&
              ` + d(${[...dontCares].sort((a, b) => a - b).join(", ")})`}
          </div>

          <button
            onClick={() => {
              setMinterms([]);
              setDontCares([]);
              solveGrid(numVars, [], []);
            }}
            className="text-xs px-3 py-1 rounded-md bg-slate-800 hover:bg-rose-900/50 text-slate-300 hover:text-rose-200 transition"
          >
            Clear Grid
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <div className="lg:col-span-5">
          <KMapGrid
            kmap={result?.kmap}
            groups={
              formMode === "SOP"
                ? result?.grouping?.groups || []
                : result?.grouping?.pos_groups || []
            }
            hoveredGroupId={hoveredGroupId}
            onToggleCell={handleToggleCell}
          />
        </div>

        <div className="lg:col-span-7">
          <TutorSteps
            result={result}
            formMode={formMode}
            setFormMode={setFormMode}
            hoveredGroupId={hoveredGroupId}
            setHoveredGroupId={setHoveredGroupId}
          />
        </div>
      </div>
      </div>
    </div>
  );
}