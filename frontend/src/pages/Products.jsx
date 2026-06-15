import { useState, useEffect } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, SlidersHorizontal, X, ChevronDown, Sparkles } from 'lucide-react'
import ProductCard from '../components/ProductCard'
import { SkeletonGrid, ErrorState, EmptyState } from '../components/Loader'
import { fetchProducts, searchProducts } from '../services/api'
import useDebounce from '../hooks/useDebounce'

const CATEGORIES = ['All', 'Electronics', 'Apparel', 'Home', 'Sports', 'Beauty', 'Toys']
const SORTS = [
  { label: 'Demand ↑',  value: 'demand_desc' },
  { label: 'Price ↑',   value: 'price_asc'   },
  { label: 'Price ↓',   value: 'price_desc'  },
  { label: 'Newest',    value: 'newest'       },
]

export default function Products() {
  const [searchParams] = useSearchParams()

  const [products, setProducts]       = useState([])
  const [loading, setLoading]         = useState(true)
  const [error, setError]             = useState(null)
  const [search, setSearch]           = useState(searchParams.get('q') || '')
  const [queryParsed, setQueryParsed] = useState(null)   // from semantic search
  const [isSemanticMode, setIsSemanticMode] = useState(false)
  const [category, setCategory]       = useState('All')
  const [sort, setSort]               = useState('demand_desc')
  const [showFilters, setShowFilters] = useState(false)
  const [page, setPage]               = useState(1)

  const debouncedSearch = useDebounce(search, 350)

  // Sync URL ?q= param into search box
  useEffect(() => {
    const q = searchParams.get('q')
    if (q !== null) setSearch(q)
  }, [searchParams])

  const load = () => {
    setLoading(true)
    setError(null)

    const q = debouncedSearch.trim()

    // Use semantic search when there's a query, otherwise use the normal products API
    const fetchFn = q
      ? searchProducts(q, 20).then(res => {
          setQueryParsed(res.query_parsed ?? null)
          setIsSemanticMode(true)
          return { products: res.products ?? [] }
        })
      : fetchProducts({
          category: category !== 'All' ? category : undefined,
          sort,
          page,
          limit: 20,
        }).then(res => {
          setQueryParsed(null)
          setIsSemanticMode(false)
          return res
        })

    fetchFn
      .then(d => setProducts(d.products ?? d ?? []))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }

  useEffect(() => { setPage(1) }, [debouncedSearch, category, sort])
  useEffect(() => { load() },    [debouncedSearch, category, sort, page])

  // Build query-parsed chip text
  const queryChips = []
  if (queryParsed) {
    if (queryParsed.category)             queryChips.push(`Type: ${queryParsed.category}`)
    if (queryParsed.colors?.length)       queryChips.push(`Color: ${queryParsed.colors.join(', ')}`)
    if (queryParsed.materials?.length)    queryChips.push(`Material: ${queryParsed.materials.join(', ')}`)
    if (queryParsed.styles?.length)       queryChips.push(`Style: ${queryParsed.styles.join(', ')}`)
  }

  return (
    <div className="bg-[#0B1020] min-h-[100vh] text-[#F9FAFB]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">

        {/* Header */}
        <div className="space-y-1">
          <h1 className="text-3xl font-extrabold bg-gradient-to-r from-[#6D5DFC] to-[#22D3EE] bg-clip-text text-transparent">Products</h1>
          <p className="text-[#9CA3AF] text-sm">Live-priced inventory — optimized by dynamic intelligence</p>
        </div>

        {/* Toolbar */}
        <div className="flex flex-col sm:flex-row gap-3">
          {/* Search */}
          <div className="relative flex-1">
            <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#9CA3AF] pointer-events-none" />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search products… try 'green mat' or 'wireless earbuds'"
              className="w-full bg-[#111827]/70 border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-sm text-[#F9FAFB] placeholder-[#9CA3AF] focus:outline-none focus:border-[#6D5DFC]/60 focus:ring-1 focus:ring-[#6D5DFC]/60 transition-colors shadow-sm"
            />
            {search && (
              <button onClick={() => setSearch('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-[#9CA3AF] hover:text-[#F9FAFB]">
                <X size={14} />
              </button>
            )}
          </div>

          {/* Sort — hidden in semantic mode */}
          {!isSemanticMode && (
            <div className="relative">
              <select
                value={sort}
                onChange={e => setSort(e.target.value)}
                className="appearance-none bg-[#111827]/70 border border-white/10 rounded-xl px-4 py-2.5 pr-10 text-sm text-[#F9FAFB] focus:outline-none focus:border-[#6D5DFC]/60 focus:ring-1 focus:ring-[#6D5DFC]/60 transition-colors cursor-pointer shadow-sm"
              >
                {SORTS.map(s => <option key={s.value} value={s.value} className="bg-[#111827] text-[#F9FAFB]">{s.label}</option>)}
              </select>
              <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-[#9CA3AF] pointer-events-none" />
            </div>
          )}

          <button
            onClick={() => setShowFilters(v => !v)}
            className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-colors border shadow-sm ${showFilters ? 'border-[#6D5DFC]/50 text-[#6D5DFC] bg-[#6D5DFC]/10' : 'border-white/10 text-[#9CA3AF] bg-[#111827]/70 hover:text-[#F9FAFB] hover:bg-white/5'}`}
          >
            <SlidersHorizontal size={14} /> Filters
          </button>
        </div>

        {/* Semantic query chips */}
        <AnimatePresence>
          {isSemanticMode && queryChips.length > 0 && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="flex flex-wrap gap-2 items-center"
            >
              <span className="inline-flex items-center gap-1 text-xs font-bold text-[#22D3EE]">
                <Sparkles size={11} /> AI understood:
              </span>
              {queryChips.map(chip => (
                <span key={chip}
                  className="px-3 py-1 rounded-full text-xs font-semibold bg-[#22D3EE]/10 text-[#22D3EE] border border-[#22D3EE]/20">
                  {chip}
                </span>
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Category filters */}
        <AnimatePresence>
          {showFilters && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden"
            >
              <div className="flex flex-wrap gap-2 pb-2">
                {CATEGORIES.map(c => (
                  <button
                    key={c}
                    onClick={() => setCategory(c)}
                    className={`px-4 py-1.5 rounded-full text-xs font-bold border transition-all shadow-sm ${
                      category === c
                        ? 'bg-[#6D5DFC] border-[#6D5DFC] text-[#F9FAFB]'
                        : 'bg-[#111827]/70 border-white/10 text-[#9CA3AF] hover:text-[#F9FAFB] hover:border-white/25'
                    }`}
                  >
                    {c}
                  </button>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Results */}
        {loading && <SkeletonGrid count={12} />}
        {!loading && error && <ErrorState message={error} onRetry={load} />}
        {!loading && !error && products.length === 0 && (
          <EmptyState
            title="No products found"
            message="Try adjusting your search. For example: 'blue speaker' or 'leather bag'."
            action={<button onClick={() => { setSearch(''); setCategory('All') }} className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-[#0B1020] bg-gradient-to-r from-[#6D5DFC] to-[#22D3EE] transition-colors shadow-md">Clear filters</button>}
          />
        )}
        {!loading && !error && products.length > 0 && (
          <AnimatePresence mode="popLayout">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {products.map(p => (
                <motion.div
                  key={p.id}
                  layout
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, scale: 0.96 }}
                  transition={{ duration: 0.3 }}
                  className="bg-[#111827]/70 backdrop-blur-md border border-white/10 rounded-2xl p-4 transition-all duration-300 hover:scale-[1.02] hover:border-[#6D5DFC]/50 flex flex-col justify-between min-h-[420px]"
                >
                  <div className="space-y-4">
                    {/* Product Image */}
                    <div className="w-full h-40 bg-white/5 rounded-xl overflow-hidden flex items-center justify-center relative">
                      {p.image ? (
                        <img
                          src={p.image}
                          alt={p.name}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <span className="text-[#9CA3AF]/40 text-xs font-semibold">No Image</span>
                      )}
                    </div>

                    {/* Info */}
                    <div className="space-y-1.5 text-left">
                      <h3 className="font-bold text-base text-[#F9FAFB] line-clamp-1">{p.name}</h3>
                      <p className="text-[#9CA3AF] text-xs line-clamp-2 leading-relaxed">
                        {p.description || "High-quality engineered option designed for peak performance and daily reliability."}
                      </p>
                    </div>

                    {/* Real-time Pricing Info */}
                    <div className="space-y-1.5 pt-3 border-t border-white/5 text-left">
                      <div className="flex items-center justify-between">
                        <div className="flex items-baseline gap-2">
                          <span className="text-[#F9FAFB] font-extrabold text-lg">
                            ₹{p.current_price ? Math.floor(p.current_price).toLocaleString('en-IN') : '0'}
                          </span>
                          {p.current_price && p.original_price && p.current_price !== p.original_price && (
                            <span className="text-[#9CA3AF] line-through text-xs">
                              ₹{Math.floor(p.original_price).toLocaleString('en-IN')}
                            </span>
                          )}
                        </div>

                        {/* Dynamic Price Change Badge */}
                        {p.price_change_percentage !== undefined && p.price_change_percentage !== 0 && (
                          <span className={`text-[10px] font-black px-2.5 py-1 rounded-full ${
                            p.price_change_percentage > 0
                              ? 'bg-[#10B981]/10 text-[#10B981]'
                              : 'bg-[#EF4444]/10 text-[#EF4444]'
                          }`}>
                            {p.price_change_percentage > 0 ? `▲ ${p.price_change_percentage}%` : `▼ ${Math.abs(p.price_change_percentage)}%`}
                          </span>
                        )}
                      </div>

                      {/* Change Reason Explainer */}
                      {p.change_reason && (
                        <p className="text-[10px] text-[#22D3EE] font-medium italic truncate" title={p.change_reason}>
                          {p.change_reason}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Call To Action */}
                  <Link
                    to={`/products/${p.id}`}
                    className="mt-4 w-full py-2.5 rounded-xl bg-gradient-to-r from-[#6D5DFC] to-[#22D3EE] text-center font-bold text-sm text-[#0B1020] hover:opacity-90 transition-opacity block"
                  >
                    View Details
                  </Link>
                </motion.div>
              ))}
            </div>
          </AnimatePresence>
        )}

        {/* Pagination — only in normal browse mode */}
        {!loading && !isSemanticMode && products.length === 20 && (
          <div className="flex justify-center pt-4">
            <button onClick={() => setPage(p => p + 1)} className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl font-bold text-[#6D5DFC] border-2 border-[#6D5DFC]/40 hover:border-[#6D5DFC] hover:bg-[#6D5DFC]/10 transition-colors shadow-sm">
              Load More
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
