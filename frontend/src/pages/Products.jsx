import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
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
    <div className="bg-[#F0F4F0] min-h-[100vh]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">

        {/* Header */}
        <div className="space-y-1">
          <h1 className="text-3xl font-bold text-[#1A2E1A]">Products</h1>
          <p className="text-[#5A7A5A] text-sm">Live-priced inventory — updates every 30s</p>
        </div>

        {/* Toolbar */}
        <div className="flex flex-col sm:flex-row gap-3">
          {/* Search */}
          <div className="relative flex-1">
            <Search size={15} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[#5A7A5A] pointer-events-none" />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search products… try 'green mat' or 'wireless earbuds'"
              className="w-full bg-[#E4EDE4] border border-[#C8D9C8] rounded-xl pl-10 pr-4 py-2.5 text-sm text-[#1A2E1A] placeholder-[#5A7A5A] focus:outline-none focus:border-[#2D6A2D]/60 focus:ring-1 focus:ring-[#2D6A2D]/60 transition-colors shadow-sm"
            />
            {search && (
              <button onClick={() => setSearch('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-[#5A7A5A] hover:text-[#1A2E1A]">
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
                className="appearance-none bg-[#E4EDE4] border border-[#C8D9C8] rounded-xl px-4 py-2.5 pr-10 text-sm text-[#1A2E1A] focus:outline-none focus:border-[#2D6A2D]/60 focus:ring-1 focus:ring-[#2D6A2D]/60 transition-colors cursor-pointer shadow-sm"
              >
                {SORTS.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
              </select>
              <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-[#5A7A5A] pointer-events-none" />
            </div>
          )}

          <button
            onClick={() => setShowFilters(v => !v)}
            className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-colors border shadow-sm ${showFilters ? 'border-[#2D6A2D]/50 text-[#2D6A2D] bg-[#2D6A2D]/10' : 'border-[#C8D9C8] text-[#5A7A5A] bg-[#E4EDE4] hover:text-[#1A2E1A] hover:bg-[#C8D9C8]/40'}`}
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
              <span className="inline-flex items-center gap-1 text-xs font-bold text-[#2D6A2D]">
                <Sparkles size={11} /> AI understood:
              </span>
              {queryChips.map(chip => (
                <span key={chip}
                  className="px-3 py-1 rounded-full text-xs font-semibold bg-[#2D6A2D]/10 text-[#2D6A2D] border border-[#2D6A2D]/20">
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
                        ? 'bg-[#2D6A2D] border-[#2D6A2D] text-[#F0F4F0]'
                        : 'bg-[#E4EDE4] border-[#C8D9C8] text-[#5A7A5A] hover:text-[#1A2E1A] hover:border-[#5A7A5A]/50'
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
            action={<button onClick={() => { setSearch(''); setCategory('All') }} className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-[#F0F4F0] bg-[#2D6A2D] hover:bg-[#1A2E1A] transition-colors shadow-md">Clear filters</button>}
          />
        )}
        {!loading && !error && products.length > 0 && (
          <AnimatePresence mode="popLayout">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
              {products.map(p => <ProductCard key={p.id} product={p} />)}
            </div>
          </AnimatePresence>
        )}

        {/* Pagination — only in normal browse mode */}
        {!loading && !isSemanticMode && products.length === 20 && (
          <div className="flex justify-center pt-4">
            <button onClick={() => setPage(p => p + 1)} className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl font-bold text-[#2D6A2D] border-2 border-[#2D6A2D]/40 hover:border-[#2D6A2D] hover:bg-[#2D6A2D]/10 transition-colors shadow-sm">
              Load More
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
