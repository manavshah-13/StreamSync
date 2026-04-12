import { Link, NavLink, useNavigate } from 'react-router-dom'
import { ShoppingCart, Zap, User, Search, Menu, X, Mic } from 'lucide-react'
import { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import useCart from '../hooks/useCart'
import { searchProducts } from '../services/api'
import useDebounce from '../hooks/useDebounce'

const navLinks = [
  { to: '/products',  label: 'Shop' },
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/cart',      label: 'Cart' },
]

export default function Navbar() {
  const { totalItems } = useCart()
  const [scrolled, setScrolled]           = useState(false)
  const [open, setOpen]                   = useState(false)
  const [searchFocused, setSearchFocused] = useState(false)
  const [searchQuery, setSearchQuery]     = useState('')
  const [suggestions, setSuggestions]     = useState([])
  const [showDrop, setShowDrop]           = useState(false)
  const navigate   = useNavigate()
  const dropRef    = useRef(null)
  const debouncedQ = useDebounce(searchQuery, 300)

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 40)
    window.addEventListener('scroll', handler, { passive: true })
    return () => window.removeEventListener('scroll', handler)
  }, [])

  // Live suggestions while typing
  useEffect(() => {
    if (debouncedQ.trim().length < 2) {
      setSuggestions([])
      setShowDrop(false)
      return
    }
    searchProducts(debouncedQ.trim(), 5).then(res => {
      setSuggestions(res.products ?? [])
      setShowDrop(true)
    }).catch(() => setSuggestions([]))
  }, [debouncedQ])

  // Close dropdown when clicking outside
  useEffect(() => {
    const handler = (e) => {
      if (dropRef.current && !dropRef.current.contains(e.target)) {
        setShowDrop(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleSearch = useCallback((q) => {
    const query = (q ?? searchQuery).trim()
    if (!query) return
    setShowDrop(false)
    setSearchQuery('')
    navigate(`/products?q=${encodeURIComponent(query)}`)
  }, [searchQuery, navigate])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleSearch()
  }

  return (
    <header className="fixed top-0 inset-x-0 z-50 bg-[#0D0D0D] border-b border-white/8 shadow-xl shadow-black/40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center gap-4">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 shrink-0 group">
          <div className="w-8 h-8 rounded-lg bg-accent-green flex items-center justify-center shadow-lg shadow-accent-green/30 group-hover:scale-110 transition-transform">
            <Zap size={15} className="text-navy-950" fill="currentColor" />
          </div>
          <span className="font-extrabold text-lg tracking-tight text-white">
            Stream<span className="text-accent-green">Sync</span>
          </span>
        </Link>

        {/* Search with suggestions dropdown */}
        <div
          ref={dropRef}
          className={`hidden md:flex flex-1 max-w-xl mx-auto relative transition-all duration-300 ${searchFocused ? 'max-w-2xl' : ''}`}
        >
          <div className={`w-full flex items-center gap-2 rounded-2xl border px-4 py-2.5 transition-all duration-300 ${
            searchFocused
              ? 'bg-white/8 border-[#16A34A]/60 shadow-lg shadow-[#16A34A]/10'
              : 'bg-white/5 border-white/10 hover:border-white/20'
          }`}>
            <Search size={14} className="text-slate-400 shrink-0" />
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              onFocus={() => setSearchFocused(true)}
              onBlur={() => setSearchFocused(false)}
              placeholder="Search products, brands, categories…"
              className="flex-1 bg-transparent text-sm text-white placeholder-slate-500 outline-none"
            />
            <div className="flex items-center gap-1.5 shrink-0">
              <span className="text-[9px] font-semibold text-[#16A34A] bg-[#16A34A]/10 border border-[#16A34A]/30 px-1.5 py-0.5 rounded-md">AI</span>
              <Mic size={13} className="text-slate-500 hover:text-[#16A34A] transition-colors cursor-pointer" />
            </div>
          </div>

          {/* Suggestions dropdown */}
          <AnimatePresence>
            {showDrop && suggestions.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: -6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                transition={{ duration: 0.15 }}
                className="absolute top-full left-0 right-0 mt-2 bg-[#111] border border-white/10 rounded-2xl overflow-hidden shadow-2xl z-50"
              >
                {suggestions.map((p, i) => (
                  <button
                    key={p.id}
                    onMouseDown={() => {
                      setShowDrop(false)
                      setSearchQuery('')
                      navigate(`/products/${p.id}`)
                    }}
                    className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-white/5 transition-colors text-left group"
                  >
                    {p.image ? (
                      <img src={p.image} alt="" className="w-9 h-9 rounded-lg object-cover shrink-0" />
                    ) : (
                      <div className="w-9 h-9 rounded-lg bg-white/5 shrink-0" />
                    )}
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold text-white truncate">{p.name}</p>
                      <p className="text-[10px] text-slate-500 truncate">{p.category}</p>
                    </div>
                    {p.matchScore && (
                      <span className="text-[9px] font-bold text-[#16A34A] bg-[#16A34A]/10 px-1.5 py-0.5 rounded-full shrink-0">
                        {Math.round(p.matchScore * 10) / 10}
                      </span>
                    )}
                  </button>
                ))}
                <button
                  onMouseDown={() => handleSearch()}
                  className="w-full px-4 py-2 text-xs text-[#16A34A] hover:bg-[#16A34A]/5 transition-colors text-center border-t border-white/5"
                >
                  See all results for "{searchQuery}"
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Desktop right */}
        <nav className="hidden md:flex items-center gap-1 shrink-0">
          {navLinks.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  isActive ? 'text-[#16A34A] bg-[#16A34A]/10' : 'text-slate-300 hover:text-white hover:bg-white/5'
                }`
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="flex items-center gap-2 ml-auto md:ml-0 shrink-0">
          <button
            onClick={() => {
              localStorage.removeItem('user');
              navigate('/login');
            }}
            className="p-2.5 rounded-xl text-slate-300 hover:text-white hover:bg-white/8 transition-all" aria-label="Profile">
            <User size={18} />
          </button>
          <button
            onClick={() => navigate('/cart')}
            className="relative p-2.5 rounded-xl text-slate-300 hover:text-white hover:bg-white/8 transition-all"
            aria-label="Cart"
          >
            <ShoppingCart size={18} />
            <AnimatePresence>
              {totalItems > 0 && (
                <motion.span
                  key={totalItems}
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  exit={{ scale: 0 }}
                  className="absolute -top-0.5 -right-0.5 w-4.5 h-4.5 min-w-[18px] text-[10px] font-bold rounded-full bg-[#16A34A] text-white flex items-center justify-center px-1"
                >
                  {totalItems}
                </motion.span>
              )}
            </AnimatePresence>
          </button>
          <button
            className="md:hidden p-2.5 rounded-xl text-slate-300 hover:text-white hover:bg-white/8 transition-all"
            onClick={() => setOpen(v => !v)}
          >
            {open ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden bg-[#05070A]/98 border-t border-white/8 overflow-hidden"
          >
            <div className="px-4 py-3 space-y-1">
              <div className="flex items-center gap-2 bg-white/5 border border-white/10 rounded-xl px-3 py-2.5 mb-3">
                <Search size={14} className="text-slate-400" />
                <input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && searchQuery.trim()) {
                      handleSearch()
                      setOpen(false)
                    }
                  }}
                  placeholder="Search…"
                  className="flex-1 bg-transparent text-sm text-white placeholder-slate-500 outline-none"
                />
              </div>
              {navLinks.map(({ to, label }) => (
                <NavLink key={to} to={to} onClick={() => setOpen(false)}
                  className={({ isActive }) =>
                    `block px-4 py-3 rounded-xl text-sm font-medium transition-all ${isActive ? 'text-accent-green bg-accent-green/10' : 'text-slate-300 hover:text-white hover:bg-white/5'}`
                  }
                >{label}</NavLink>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  )
}
