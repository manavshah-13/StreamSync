import { Loader2, AlertCircle, PackageOpen } from 'lucide-react'

// ─── Spinner (inline) ─────────────────────────────────────────────────────────
export function Spinner({ size = 20, className = '' }) {
  return <Loader2 size={size} className={`animate-spin text-accent-green ${className}`} />
}

// ─── PageLoader (full-page) ───────────────────────────────────────────────────
export function PageLoader() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
      <div className="relative">
        <div className="w-16 h-16 rounded-full border-2 border-accent-green/20 border-t-accent-green animate-spin" />
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-6 h-6 rounded-full bg-accent-green/20 animate-pulse" />
        </div>
      </div>
      <p className="text-slate-400 text-sm font-medium animate-pulse">Loading StreamSync data…</p>
    </div>
  )
}

// ─── SkeletonCard ─────────────────────────────────────────────────────────────
export function SkeletonCard() {
  return (
    <div className="card overflow-hidden">
      <div className="skeleton h-48 w-full rounded-xl mb-4" />
      <div className="space-y-3">
        <div className="skeleton h-4 w-3/4 rounded-full" />
        <div className="skeleton h-3 w-1/2 rounded-full" />
        <div className="flex justify-between items-center pt-2">
          <div className="skeleton h-6 w-24 rounded-lg" />
          <div className="skeleton h-9 w-28 rounded-lg" />
        </div>
      </div>
    </div>
  )
}

// ─── SkeletonGrid ─────────────────────────────────────────────────────────────
export function SkeletonGrid({ count = 8 }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  )
}

// ─── ErrorState ───────────────────────────────────────────────────────────────
export function ErrorState({ message = 'Something went wrong.', onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[40vh] gap-4 text-center px-4">
      <div className="w-16 h-16 rounded-2xl bg-warn-red/10 border border-warn-red/20 flex items-center justify-center">
        <AlertCircle size={28} className="text-warn-red" />
      </div>
      <div>
        <p className="text-white font-semibold mb-1">Failed to load data</p>
        <p className="text-slate-400 text-sm max-w-xs">{message}</p>
      </div>
      {onRetry && (
        <button onClick={onRetry} className="btn-primary">
          Retry
        </button>
      )}
    </div>
  )
}

// ─── EmptyState ───────────────────────────────────────────────────────────────
export function EmptyState({ title = 'Nothing here', message = '', action }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[40vh] gap-4 text-center px-4">
      <div className="w-16 h-16 rounded-2xl bg-navy-800 border border-white/5 flex items-center justify-center">
        <PackageOpen size={28} className="text-slate-500" />
      </div>
      <div>
        <p className="text-white font-semibold mb-1">{title}</p>
        {message && <p className="text-slate-400 text-sm max-w-xs">{message}</p>}
      </div>
      {action}
    </div>
  )
}

export default Spinner
