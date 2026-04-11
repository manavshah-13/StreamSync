import { createContext, useReducer, useCallback } from 'react'

export const CartContext = createContext(null)

// ─── Reducer ──────────────────────────────────────────────────────────────────
function cartReducer(state, action) {
  switch (action.type) {
    case 'ADD': {
      const existing = state.items.find((i) => i.id === action.product.id)
      if (existing) {
        return {
          ...state,
          items: state.items.map((i) =>
            i.id === action.product.id
              ? { ...i, qty: i.qty + (action.qty ?? 1) }
              : i
          ),
        }
      }
      return {
        ...state,
        items: [...state.items, { ...action.product, qty: action.qty ?? 1 }],
      }
    }

    case 'REMOVE':
      return { ...state, items: state.items.filter((i) => i.id !== action.id) }

    case 'UPDATE_QTY': {
      if (action.qty <= 0) {
        return { ...state, items: state.items.filter((i) => i.id !== action.id) }
      }
      return {
        ...state,
        items: state.items.map((i) =>
          i.id === action.id ? { ...i, qty: action.qty } : i
        ),
      }
    }

    case 'CLEAR':
      return { items: [] }

    default:
      return state
  }
}

// ─── Provider ─────────────────────────────────────────────────────────────────
export function CartProvider({ children }) {
  const [state, dispatch] = useReducer(cartReducer, { items: [] })

  const addToCart     = useCallback((product, qty = 1) => dispatch({ type: 'ADD', product, qty }), [])
  const removeFromCart= useCallback((id) => dispatch({ type: 'REMOVE', id }), [])
  const updateQty     = useCallback((id, qty) => dispatch({ type: 'UPDATE_QTY', id, qty }), [])
  const clearCart     = useCallback(() => dispatch({ type: 'CLEAR' }), [])

  const totalItems    = state.items.reduce((s, i) => s + i.qty, 0)
  const totalPrice    = state.items.reduce((s, i) => s + i.price * i.qty, 0)

  return (
    <CartContext.Provider value={{ items: state.items, totalItems, totalPrice, addToCart, removeFromCart, updateQty, clearCart }}>
      {children}
    </CartContext.Provider>
  )
}
