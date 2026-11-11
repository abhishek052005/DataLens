{/* Column Roles */}
<div className="relative bg-[#0f1320] border border-white/5 rounded-2xl p-6 overflow-hidden">
  <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-fuchsia-500/50 to-transparent" />
  <h2 className="text-[11px] font-bold uppercase tracking-[0.15em] text-gray-500 mb-5">
    Column Roles
  </h2>

  <div className="grid grid-cols-2 gap-4">
    {/* Left: Selected */}
    <div>
      <p className="text-[10px] uppercase tracking-wider text-emerald-500/70 font-bold mb-3">
        ✓ Selected
      </p>
      <div className="space-y-2.5">
        {result.analysis.selected_columns.map((col: any, i: number) => (
          <div key={i} className="flex items-center gap-2">
            <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase ${
              col.role === "measure" ? "bg-blue-500/10 text-blue-400 border border-blue-500/20" :
              col.role === "dimension" ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" :
              "bg-amber-500/10 text-amber-400 border border-amber-500/20"
            }`}>
              {col.role}
            </span>
            <span className="text-xs text-gray-300">{col.name}</span>
          </div>
        ))}
      </div>
    </div>

    {/* Right: Dropped */}
    <div>
      <p className="text-[10px] uppercase tracking-wider text-red-500/70 font-bold mb-3">
        ✕ Dropped
      </p>
      <div className="space-y-2.5">
        {result.analysis.dropped_columns.length === 0 ? (
          <p className="text-xs text-gray-600 italic">None</p>
        ) : (
          result.analysis.dropped_columns.map((col: any, i: number) => (
            <div key={i}>
              <p className="text-xs text-gray-400 line-through">{col.name}</p>
              <p className="text-[10px] text-gray-600 mt-0.5 leading-snug">{col.reason}</p>
            </div>
          ))
        )}
      </div>
    </div>
  </div>
</div>   