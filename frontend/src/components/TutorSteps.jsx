import React, { useState } from "react";

export default function TutorSteps({
  result,
  formMode = "SOP",
  setFormMode,
  hoveredGroupId,
  setHoveredGroupId,
}) {
  const [activeTab, setActiveTab] = useState("tutor");

  if (!result) return null;

  const { kmap, grouping, verification, tutor_steps, agent_trace } = result;
  const vars = kmap.variables;
  const activeGroups =
    formMode === "SOP" ? grouping.groups : grouping.pos_groups || [];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-5">
      {/* Final Minimized SOP & POS Banner */}
      <div className="p-4 rounded-lg bg-gradient-to-r from-indigo-950 to-slate-900 border border-indigo-500/40 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="space-y-1.5">
            <div>
              <span className="text-[11px] uppercase tracking-wider text-emerald-300 font-semibold">
                Minimized SOP (Sum of Products)
              </span>
              <p className="text-xl font-mono font-bold text-white">
                F({vars.join(", ")}) = {grouping.minimized_sop}
              </p>
            </div>
            <div>
              <span className="text-[11px] uppercase tracking-wider text-amber-300 font-semibold">
                Minimized POS (Product of Sums)
              </span>
              <p className="text-xl font-mono font-bold text-white">
                F({vars.join(", ")}) = {grouping.minimized_pos}
              </p>
            </div>
          </div>

          <span
            className={`px-3 py-1 rounded-full text-xs font-semibold ${
              verification.all_passed
                ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                : "bg-rose-500/20 text-rose-300 border border-rose-500/40"
            }`}
          >
            {verification.all_passed
              ? `✓ Verified (${verification.total_rows}/${verification.total_rows} Rows Match)`
              : "✗ Verification Mismatch"}
          </span>
        </div>

        {/* Toggle K-Map Overlay Between SOP (1s) and POS (0s) */}
        <div className="flex items-center gap-2 pt-2 border-t border-indigo-500/20">
          <span className="text-xs text-slate-400">Map Overlay Mode:</span>
          <button
            onClick={() => setFormMode("SOP")}
            className={`px-3 py-1 rounded-md text-xs font-semibold transition ${
              formMode === "SOP"
                ? "bg-emerald-600 text-white"
                : "bg-slate-800 text-slate-300 hover:bg-slate-700"
            }`}
          >
            SOP (Group 1s)
          </button>
          <button
            onClick={() => setFormMode("POS")}
            className={`px-3 py-1 rounded-md text-xs font-semibold transition ${
              formMode === "POS"
                ? "bg-amber-600 text-white"
                : "bg-slate-800 text-slate-300 hover:bg-slate-700"
            }`}
          >
            POS (Group 0s)
          </button>
        </div>
      </div>

      {/* Interactive Prime Implicant Group Pills */}
      {activeGroups.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">
            Detected {formMode} Groups ({formMode === "SOP" ? "1-Cells" : "0-Cells"}) — Hover to Highlight
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {activeGroups.map((g) => (
              <div
                key={`${formMode}-${g.id}`}
                onMouseEnter={() => setHoveredGroupId(g.id)}
                onMouseLeave={() => setHoveredGroupId(null)}
                style={{
                  borderColor:
                    hoveredGroupId === g.id ? g.color : "rgb(30 41 59)",
                }}
                className="p-3 rounded-lg bg-slate-950/70 border transition-all cursor-pointer"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span
                      style={{ backgroundColor: g.color }}
                      className="w-3 h-3 rounded-full"
                    />
                    <span className="font-mono font-bold text-white text-base">
                      {g.term}
                    </span>
                  </div>
                  <span className="text-[11px] px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                    {g.size_name.split(" ")[0]}
                  </span>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Cells:{" "}
                  <span className="font-mono text-slate-200">
                    {g.minterms.map((m) => `m${m}`).join(", ")}
                  </span>
                </p>
                <div className="flex flex-wrap gap-1.5 mt-1.5">
                  {g.is_essential && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
                      Essential PI
                    </span>
                  )}
                  {g.wraps_around && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-500/15 text-amber-300 border border-amber-500/30">
                      {g.wrap_type}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Keep the rest of TutorSteps.jsx (Navigation Tabs & Tab 1/2/3 content) unchanged below */}

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-800 gap-4 text-sm">
        <button
          onClick={() => setActiveTab("tutor")}
          className={`pb-2 font-medium transition-colors ${
            activeTab === "tutor"
              ? "text-indigo-400 border-b-2 border-indigo-400"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          Step-by-Step Tutor
        </button>
        <button
          onClick={() => setActiveTab("truth")}
          className={`pb-2 font-medium transition-colors ${
            activeTab === "truth"
              ? "text-indigo-400 border-b-2 border-indigo-400"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          Truth Table ({verification.total_rows} Rows)
        </button>
        <button
          onClick={() => setActiveTab("trace")}
          className={`pb-2 font-medium transition-colors ${
            activeTab === "trace"
              ? "text-indigo-400 border-b-2 border-indigo-400"
              : "text-slate-400 hover:text-slate-200"
          }`}
        >
          Agent Tool Trace
        </button>
      </div>

      {/* Tab 1: Step-by-Step Tutor */}
      {activeTab === "tutor" && (
        <div className="space-y-3 text-sm text-slate-300">
          <div className="p-3 rounded-lg bg-indigo-950/30 border border-indigo-500/20 text-indigo-200">
            <strong className="text-indigo-300">AI Tutor Insight: </strong>
            {tutor_steps.ai_tutor_summary}
          </div>

          <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
            <p className="font-semibold text-white mb-1">
              Step 1: Gray-Code Cell Plotting
            </p>
            <p className="text-slate-400 leading-relaxed">
              {tutor_steps.step_1_plotting}
            </p>
          </div>

          <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
            <p className="font-semibold text-white mb-1">
              Step 2: Power-of-2 Grouping & Wrap-Arounds
            </p>
            <p className="text-slate-400 leading-relaxed">
              {tutor_steps.step_2_grouping}
            </p>
          </div>

          <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
            <p className="font-semibold text-white mb-1">
              Step 3: Variable Cancellation
            </p>
            <p className="text-slate-400 leading-relaxed">
              {tutor_steps.step_3_elimination}
            </p>
          </div>

          <div className="p-3 rounded-lg bg-slate-950/60 border border-slate-800">
            <p className="font-semibold text-white mb-1">
              Step 4: Exhaustive Truth-Table Check
            </p>
            <p className="text-slate-400 leading-relaxed">
              {tutor_steps.step_4_verification}
            </p>
          </div>
        </div>
      )}

      {/* Tab 2: Full Truth Table Verification */}
      {activeTab === "truth" && (
        <div className="max-h-80 overflow-y-auto border border-slate-800 rounded-lg">
          <table className="w-full text-xs font-mono text-center">
            <thead className="bg-slate-950 text-slate-300 sticky top-0">
              <tr>
                <th className="py-2 px-2">Row</th>
                {vars.map((v) => (
                  <th key={v} className="py-2 px-2">
                    {v}
                  </th>
                ))}
                <th className="py-2 px-2 text-amber-300">Original F</th>
                <th className="py-2 px-2 text-indigo-300">Minimized F</th>
                <th className="py-2 px-2">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {verification.rows.map((r) => (
                <tr key={r.minterm} className="hover:bg-slate-800/40">
                  <td className="py-1.5 text-slate-400">m{r.minterm}</td>
                  {vars.map((v) => (
                    <td key={v} className="py-1.5 text-slate-200">
                      {r.inputs[v]}
                    </td>
                  ))}
                  <td className="py-1.5 font-bold text-amber-300">
                    {r.expected}
                  </td>
                  <td className="py-1.5 font-bold text-indigo-300">
                    {r.actual}
                  </td>
                  <td className="py-1.5">
                    {r.passed ? (
                      <span className="text-emerald-400">PASS</span>
                    ) : (
                      <span className="text-rose-400">FAIL</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Tab 3: Agent Execution Trace */}
      {activeTab === "trace" && (
        <div className="space-y-2 max-h-80 overflow-y-auto">
          {(agent_trace || []).map((step, idx) => (
            <div
              key={idx}
              className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono"
            >
              <p className="text-indigo-400 font-semibold">
                [{idx + 1}] Tool: {step.tool}
              </p>
              <pre className="text-slate-400 mt-1 overflow-x-auto">
                {JSON.stringify(step.output, null, 2)}
              </pre>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}