import axios from 'axios'

// ─── Axios Instance ───────────────────────────────────────────────────────────
const api = axios.create({
  baseURL: '/api',
  timeout: 4000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    // Suppress console noise for expected proxy failures (no backend)
    if (err.code !== 'ERR_NETWORK' && err.response?.status !== 502) {
      console.warn('[StreamSync API]', err.message)
    }
    return Promise.reject(err)
  }
)

// ─── Mock Data ────────────────────────────────────────────────────────────────
const CATEGORIES = ['Electronics', 'Apparel', 'Home', 'Sports', 'Beauty', 'Toys']
const NAMES = [
  'Surface Pro AI Edition', 'StreamBuds Pro ANC', 'Creator Laptop X1',
  'Artisan Desk Collection', 'Yoga Mat Premium', 'Coffee Maker Deluxe',
  'Gaming Chair X500', 'LED Desk Lamp', 'Bluetooth Speaker',
  'Mechanical Watch', 'Leather Backpack', 'Noise Cancelling Buds',
  'Ultra-Wide Webcam', 'Standing Desk', 'Portable Charger 20K',
  'Silk Pillowcase Set', 'Kitchen Scale Pro', 'Foam Roller Set',
  'Smart Water Bottle', 'Resistance Bands Kit',
]

const IMAGES = [
  '/images/surface_pro.png', '/images/stream_buds.png', '/images/creator_laptop.png', '/images/artisan_desk.png',
  '/images/yoga_mat_premium.png', '/images/coffee_maker_deluxe.png', '/images/gaming_chair_x500.png', '/images/led_desk_lamp.png',
  '/images/bluetooth_speaker.png', '/images/mechanical_watch.png', '/images/leather_backpack.png', '/images/noise_cancelling_buds.png',
  '/images/ultra_wide_webcam.png', '/images/standing_desk.png', '/images/portable_charger_20k.png', '/images/silk_pillowcase_set.png',
  '/images/kitchen_scale_pro.png', '/images/foam_roller_set.png', '/images/smart_water_bottle.png', '/images/resistance_bands_kit.png'
]
const HARDCODED_PRICES = [106500, 14750, 151600, 28700]

function mockProduct(i) {
  const velocity = Math.floor(20 + Math.random() * 80)
  return {
    id: `prod-${i + 1}`,
    name: NAMES[i % NAMES.length],
    category: CATEGORIES[i % CATEGORIES.length],
    price: i < 4 ? HARDCODED_PRICES[i] : Math.floor((19.99 + i * 12.5 + Math.random() * 30) * 82),
    rating: parseFloat((3.5 + Math.random() * 1.5).toFixed(1)),
    reviewCount: Math.floor(50 + Math.random() * 900),
    demandVelocity: velocity,
    brand: ['Sony', 'Samsung', 'Apple', 'Nike', 'Logitech', 'IKEA'][i % 6],
    description: `High-quality ${NAMES[i % NAMES.length].toLowerCase()} engineered for peak performance and daily comfort. StreamSync dynamically adjusts its price based on real-time demand signals.`,
    specs: {
      'Weight': `${(0.3 + Math.random() * 2).toFixed(1)} kg`,
      'Warranty': '2 years',
      'Origin': 'Imported',
    },
    image: IMAGES[i % IMAGES.length],
  }
}

const MOCK_PRODUCTS = Array.from({ length: 20 }, (_, i) => mockProduct(i))

const MOCK_METRICS = {
  p99Latency: 145,
  activeSkus: '10.4M',
  repricingRate: '42,100/s',
  activeSessions: 18340,
  cacheHitRate: 98.7,
  streamLag: '12ms',
}

const MOCK_EVENTS = [
  { id: 1, sku: 'SKU-88241', oldPrice: 49.99, newPrice: 54.99, reason: 'Demand spike +82%', ts: '21:59:01' },
  { id: 2, sku: 'SKU-10453', oldPrice: 129.00, newPrice: 119.00, reason: 'Competitor drop',  ts: '21:58:47' },
  { id: 3, sku: 'SKU-33891', oldPrice: 19.99, newPrice: 24.99, reason: 'Low inventory',     ts: '21:58:22' },
  { id: 4, sku: 'SKU-72810', oldPrice: 89.99, newPrice: 84.99, reason: 'Session decay',     ts: '21:57:55' },
  { id: 5, sku: 'SKU-55623', oldPrice: 34.99, newPrice: 39.99, reason: 'Demand spike +91%', ts: '21:57:31' },
]

const genDemandHistory = () =>
  Array.from({ length: 20 }, (_, i) => ({
    t: `${i * 30}s`,
    velocity: Math.floor(30 + Math.random() * 60),
    reprices: Math.floor(100 + Math.random() * 400),
  }))

// ─── Helper: try API, fallback to mock ───────────────────────────────────────
async function tryOrMock(apiFn, mockValue) {
  try {
    return await apiFn()
  } catch {
    return mockValue
  }
}

// ─── Products ────────────────────────────────────────────────────────────────
export const fetchProducts = (params = {}) =>
  tryOrMock(
    () => api.get('/products', { params }).then(r => r.data),
    { products: MOCK_PRODUCTS }
  )

// ─── Semantic Search ─────────────────────────────────────────────────────────
export const searchProducts = (q, limit = 10) =>
  tryOrMock(
    () => api.get('/search', { params: { q, limit } }).then(r => r.data),
    // Client-side fallback: simple name/tag substring filter
    (() => {
      const terms = q.toLowerCase().split(' ')
      const filtered = MOCK_PRODUCTS.filter(p =>
        terms.some(t =>
          p.name.toLowerCase().includes(t) ||
          (p.tags || '').toLowerCase().includes(t) ||
          p.category.toLowerCase().includes(t)
        )
      ).map(p => ({ ...p, matchScore: 1.0 }))
      return {
        products: filtered.length > 0 ? filtered : MOCK_PRODUCTS.slice(0, limit),
        query_parsed: { keywords: terms },
        total: filtered.length,
        status: 'mock',
      }
    })()
  )

export const fetchProductById = (id) =>
  tryOrMock(
    () => api.get(`/products/${id}`).then(r => r.data),
    MOCK_PRODUCTS.find(p => p.id === id) ?? MOCK_PRODUCTS[0]
  )

// Unified recommendation fetch with optional params
export const fetchRecommendations = (productId = 'prod-1', sessionId = 'anon', limit = 4) =>
  tryOrMock(
    () => api.get(`/recommendations`, { params: { product_id: productId, session_id: sessionId, limit } }).then(r => r.data),
    { products: MOCK_PRODUCTS.slice(0, limit) }
  )

// ─── Dashboard Metrics ────────────────────────────────────────────────────────
export const fetchMetrics = () =>
  tryOrMock(
    () => api.get('/metrics').then(r => r.data),
    MOCK_METRICS
  )

export const fetchDemandVelocity = () =>
  tryOrMock(
    () => api.get('/metrics/demand-velocity').then(r => r.data),
    { history: genDemandHistory() }
  )

export const fetchRepricingEvents = () =>
  tryOrMock(
    () => api.get('/metrics/repricing-events').then(r => r.data),
    { events: MOCK_EVENTS }
  )

export const fetchMLInsights = () =>
  tryOrMock(
    () => api.get('/ml/insights').then(r => r.data),
    {
      revenue_uplift: { top_products: [] },
      fairness_audit: { total_alerts: 0, health_score: 100, recent_alerts: [] },
      latency: { overall_p99_ms: 0, by_route: {} },
      model_status: {},
      semantic_search: { status: 'cold' }
    }
  )

// ─── Signal Capture (fire-and-forget — never throws) ─────────────────────────
export const captureSignal = (payload) =>
  api.post('/signals', payload).catch(() => {})  // silently ignore if backend is down

export const captureView = (productId, sessionId) =>
  captureSignal({ type: 'VIEW', productId, sessionId, ts: Date.now() })

export const captureAddToCart = (productId, sessionId, qty = 1) =>
  captureSignal({ type: 'ADD_TO_CART', productId, sessionId, qty, ts: Date.now() })

export default api
