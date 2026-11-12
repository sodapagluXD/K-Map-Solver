import React from "react";

export default function KMapGrid({
  kmap,
  groups = [],
  hoveredGroupId,
  onToggleCell,
}) {
  if (!kmap) return null;

  const {
    row_vars,
    col_vars,
    row_labels,
    col_labels,
    grid,
  } = kmap;

  const getCellGroups = (r, c) =>
    groups.filter((g) => g.cells.some(([gr, gc]) => gr === r && gc === c));

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-white">
            Interactive Gray-Code K-Map
          </h2>
          <p className="text-xs text-slate-400">
            Click any cell to cycle: <span className="text-slate-200 font-mono">0 → 1 → X</span>
          </p>
        </div>
        <span className="text-xs px-2.5 py-1 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 font-mono">
          {kmap.num_vars}-Variable Map
        </span>
      </div>

      <div className="overflow-x-auto flex justify-center py-2">
        <table className="border-collapse select-none">
          <thead>
            <tr>
              <th className="p-2 text-xs font-mono text-slate-400 border-b border-r border-slate-700 bg-slate-950/60">
                {row_vars} \ {col_vars}
              </th>
              {col_labels.map((label) => (
                <th
                  key={label}
                  className="px-5 py-2 text-sm font-mono font-semibold text-indigo-300 border-b border-slate-700 bg-slate-950/40"
                >
                  {label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {grid.map((row, rIdx) => (
              <tr key={row_labels[rIdx]}>
                <th className="px-4 py-2 text-sm font-mono font-semibold text-indigo-300 border-r border-slate-700 bg-slate-950/40">
                  {row_labels[rIdx]}
                </th>
                {row.map((cell) => {
                  const cellGroups = getCellGroups(cell.row, cell.col);
                  const isHighlighted =
                    hoveredGroupId !== null &&
                    cellGroups.some((g) => g.id === hoveredGroupId);
                  const isDimmed =
                    hoveredGroupId !== null &&
                    !cellGroups.some((g) => g.id === hoveredGroupId);

                  const primaryColor =
                    cellGroups.length > 0 ? cellGroups[0].color : null;

                  return (
                    <td
                      key={cell.minterm}
                      onClick={() => onToggleCell(cell.minterm)}
                      style={{
                        boxShadow: primaryColor
                          ? `inset 0 0 0 2px ${primaryColor}`
                          : undefined,
                        backgroundColor: isHighlighted
                          ? `${primaryColor}33`
                          : undefined,
                      }}
                      className={`relative w-20 h-20 border border-slate-700 text-center cursor-pointer transition-all duration-150 hover:bg-slate-800/80 ${
                        isDimmed ? "opacity-40" : "opacity-100"
                      }`}
                    >
                      {/* Minterm index top-left */}
                      <span className="absolute top-1 left-1.5 text-[10px] font-mono text-slate-500">
                        m{cell.minterm}
                      </span>

                      {/* Group color dots top-right */}
                      {cellGroups.length > 0 && (
                        <div className="absolute top-1.5 right-1.5 flex gap-1">
                          {cellGroups.map((g) => (
                            <span
                              key={g.id}
                              style={{ backgroundColor: g.color }}
                              className="w-2 h-2 rounded-full"
                              title={`Group ${g.id}: ${g.term}`}
                            />
                          ))}
                        </div>
                      )}

                      {/* Cell value */}
                      <span
                        className={`text-2xl font-mono font-bold ${
                          cell.value === "1"
                            ? "text-emerald-400"
                            : cell.value === "X"
                            ? "text-amber-400"
                            : "text-slate-600"
                        }`}
                      >
                        {cell.value}
                      </span>

                      {/* Binary address bottom-right */}
                      <span className="absolute bottom-1 right-1.5 text-[9px] font-mono text-slate-600">
                        {cell.binary}
                      </span>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}