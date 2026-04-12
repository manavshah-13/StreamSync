import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';

const AdminPanel = () => {
  const { user } = useAuth();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editProduct, setEditProduct] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [message, setMessage] = useState({ text: '', type: '' });

  const [isAdding, setIsAdding] = useState(false);
  const [newProduct, setNewProduct] = useState({
    id: '', name: '', category: '', current_price: 0, brand: '', image: '', description: '', base_price: 0
  });

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/admin/products`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` 
        },
        body: JSON.stringify({
          ...newProduct,
          id: newProduct.id || `prod-${Date.now()}`,
          base_price: parseFloat(newProduct.current_price),
          current_price: parseFloat(newProduct.current_price)
        })
      });

      if (response.ok) {
        const created = await response.json();
        setProducts([created, ...products]);
        setIsAdding(false);
        setNewProduct({ id: '', name: '', category: '', current_price: 0, brand: '', image: '', description: '', base_price: 0 });
        showMessage('Product created successfully', 'success');
      } else {
        const err = await response.json();
        showMessage(err.detail || 'Failed to create product', 'error');
      }
    } catch (error) {
      showMessage('Network error', 'error');
    }
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/products?limit=100');
      const data = await response.json();
      setProducts(data.products || []);
    } catch (error) {
      console.error('Error fetching products:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this product?')) return;
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/admin/products/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        setProducts(products.filter(p => p.id !== id));
        showMessage('Product deleted successfully', 'success');
      } else {
        const err = await response.json();
        showMessage(err.detail || 'Failed to delete product', 'error');
      }
    } catch (error) {
      showMessage('Network error', 'error');
    }
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/admin/products/${editProduct.id}`, {
        method: 'PUT',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` 
        },
        body: JSON.stringify({
          name: editProduct.name,
          current_price: parseFloat(editProduct.current_price),
          category: editProduct.category,
          brand: editProduct.brand
        })
      });

      if (response.ok) {
        const updated = await response.json();
        setProducts(products.map(p => p.id === updated.id ? updated : p));
        setIsModalOpen(false);
        showMessage('Product updated successfully', 'success');
      } else {
        showMessage('Failed to update product', 'error');
      }
    } catch (error) {
      showMessage('Network error', 'error');
    }
  };

  const showMessage = (text, type) => {
    setMessage({ text, type });
    setTimeout(() => setMessage({ text: '', type: '' }), 3000);
  };

  if (loading) return (
    <div className="min-h-screen bg-[var(--color-bg)] flex items-center justify-center">
      <div className="w-12 h-12 border-4 border-[#16A34A] border-t-transparent rounded-full animate-spin"></div>
    </div>
  );

  return (
    <div className="min-h-screen bg-[var(--color-bg)] p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-10">
          <div>
            <h1 className="text-4xl font-extrabold text-[var(--color-heading)] tracking-tight">Admin Dashboard</h1>
            <p className="text-[var(--color-text-secondary)] mt-2 font-medium">Manage your product catalog and inventory</p>
          </div>
          <div className="flex gap-4">
            <button 
              onClick={() => setIsAdding(true)}
              className="px-6 py-2.5 rounded-xl bg-[#16A34A] font-bold text-white hover:bg-[#15803D] transition-all shadow-lg"
            >
              + Add Product
            </button>
            <Link to="/" className="px-6 py-2.5 rounded-xl border-2 border-[var(--color-border)] font-bold text-[var(--color-text-primary)] hover:bg-[var(--color-surface)] transition-all">
              Back to Store
            </Link>
          </div>
        </div>

        {message.text && (
          <div className={`mb-6 p-4 rounded-xl border-2 font-bold ${message.type === 'success' ? 'bg-green-500/10 border-green-500 text-green-500' : 'bg-red-500/10 border-red-500 text-red-500'}`}>
            {message.text}
          </div>
        )}

        <div className="bg-[var(--color-surface)] rounded-2xl border border-[var(--color-border)] overflow-hidden shadow-xl">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[var(--color-bg)] border-b border-[var(--color-border)]">
                <th className="px-6 py-4 font-bold text-[var(--color-text-secondary)] text-sm uppercase">Product</th>
                <th className="px-6 py-4 font-bold text-[var(--color-text-secondary)] text-sm uppercase">Category</th>
                <th className="px-6 py-4 font-bold text-[var(--color-text-secondary)] text-sm uppercase">Price</th>
                <th className="px-6 py-4 font-bold text-[var(--color-text-secondary)] text-sm uppercase">Actions</th>
              </tr>
            </thead>
            <tbody>
              {products.map((product) => (
                <tr key={product.id} className="border-b border-[var(--color-border)] hover:bg-[var(--color-bg)] transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-4">
                      <img src={product.image} alt="" className="w-12 h-12 rounded-lg object-cover bg-white p-1 border border-[var(--color-border)]" />
                      <div>
                        <div className="font-bold text-[var(--color-text-primary)]">{product.name}</div>
                        <div className="text-xs text-[var(--color-text-secondary)] font-medium">{product.id}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-[var(--color-text-primary)] font-medium">{product.category}</td>
                  <td className="px-6 py-4 font-bold text-[#16A34A]">${product.current_price}</td>
                  <td className="px-6 py-4">
                    <div className="flex gap-2">
                      <button 
                        onClick={() => { setEditProduct(product); setIsModalOpen(true); }}
                        className="p-2 rounded-lg hover:bg-black/5 text-blue-500 transition-colors"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                      </button>
                      <button 
                        onClick={() => handleDelete(product.id)}
                        className="p-2 rounded-lg hover:bg-black/5 text-red-500 transition-colors"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm px-4" onClick={() => setIsModalOpen(false)}></div>
          <div className="relative bg-[var(--color-surface)] w-full max-w-md rounded-2xl p-8 shadow-2xl border border-[var(--color-border)] animate-in fade-in zoom-in duration-300">
            <h2 className="text-2xl font-extrabold mb-6">Edit Product</h2>
            <form onSubmit={handleUpdate} className="flex flex-col gap-4">
              <div>
                <label className="block text-sm font-bold text-[var(--color-text-secondary)] mb-1 uppercase tracking-wider">Product Name</label>
                <input 
                  className="w-full bg-[var(--color-bg)] border-2 border-[var(--color-border)] rounded-xl py-3 px-4 font-bold outline-none focus:border-[#16A34A] transition-all"
                  value={editProduct.name}
                  onChange={(e) => setEditProduct({...editProduct, name: e.target.value})}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-bold text-[var(--color-text-secondary)] mb-1 uppercase tracking-wider">Price ($)</label>
                  <input 
                    type="number" step="0.01"
                    className="w-full bg-[var(--color-bg)] border-2 border-[var(--color-border)] rounded-xl py-3 px-4 font-bold outline-none focus:border-[#16A34A] transition-all"
                    value={editProduct.current_price}
                    onChange={(e) => setEditProduct({...editProduct, current_price: e.target.value})}
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-[var(--color-text-secondary)] mb-1 uppercase tracking-wider">Brand</label>
                  <input 
                    className="w-full bg-[var(--color-bg)] border-2 border-[var(--color-border)] rounded-xl py-3 px-4 font-bold outline-none focus:border-[#16A34A] transition-all"
                    value={editProduct.brand}
                    onChange={(e) => setEditProduct({...editProduct, brand: e.target.value})}
                  />
                </div>
              </div>
              <div className="mt-4 flex gap-3">
                <button type="button" onClick={() => setIsModalOpen(false)} className="flex-1 py-3.5 rounded-xl font-bold bg-[var(--color-bg)] border-2 border-[var(--color-border)] hover:bg-[var(--color-surface)] transition-all">Cancel</button>
                <button type="submit" className="flex-1 py-3.5 rounded-xl font-bold bg-[#1A2E1A] text-white hover:bg-black transition-all shadow-lg">Save Changes</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {isAdding && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/60 backdrop-blur-sm px-4" onClick={() => setIsAdding(false)}></div>
          <div className="relative bg-[var(--color-surface)] w-full max-w-md rounded-2xl p-8 shadow-2xl border border-[var(--color-border)] animate-in fade-in zoom-in duration-300">
            <h2 className="text-2xl font-extrabold mb-6">Add New Product</h2>
            <form onSubmit={handleCreate} className="flex flex-col gap-4">
              <div>
                <label className="block text-sm font-bold text-[var(--color-text-secondary)] mb-1 uppercase tracking-wider">Product Name</label>
                <input 
                  required
                  placeholder="e.g. Nike Air Max"
                  className="w-full bg-[var(--color-bg)] border-2 border-[var(--color-border)] rounded-xl py-3 px-4 font-bold outline-none focus:border-[#16A34A] transition-all"
                  value={newProduct.name}
                  onChange={(e) => setNewProduct({...newProduct, name: e.target.value})}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-bold text-[var(--color-text-secondary)] mb-1 uppercase tracking-wider">Category</label>
                  <input 
                    required
                    placeholder="e.g. Footwear"
                    className="w-full bg-[var(--color-bg)] border-2 border-[var(--color-border)] rounded-xl py-3 px-4 font-bold outline-none focus:border-[#16A34A] transition-all"
                    value={newProduct.category}
                    onChange={(e) => setNewProduct({...newProduct, category: e.target.value})}
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-[var(--color-text-secondary)] mb-1 uppercase tracking-wider">Price ($)</label>
                  <input 
                    type="number" step="0.01" required
                    className="w-full bg-[var(--color-bg)] border-2 border-[var(--color-border)] rounded-xl py-3 px-4 font-bold outline-none focus:border-[#16A34A] transition-all"
                    value={newProduct.current_price}
                    onChange={(e) => setNewProduct({...newProduct, current_price: e.target.value})}
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-bold text-[var(--color-text-secondary)] mb-1 uppercase tracking-wider">Brand</label>
                  <input 
                    required
                    className="w-full bg-[var(--color-bg)] border-2 border-[var(--color-border)] rounded-xl py-3 px-4 font-bold outline-none focus:border-[#16A34A] transition-all"
                    value={newProduct.brand}
                    onChange={(e) => setNewProduct({...newProduct, brand: e.target.value})}
                  />
                </div>
                <div>
                  <label className="block text-sm font-bold text-[var(--color-text-secondary)] mb-1 uppercase tracking-wider">Image URL</label>
                  <input 
                    className="w-full bg-[var(--color-bg)] border-2 border-[var(--color-border)] rounded-xl py-3 px-4 font-bold outline-none focus:border-[#16A34A] transition-all"
                    value={newProduct.image}
                    onChange={(e) => setNewProduct({...newProduct, image: e.target.value})}
                  />
                </div>
              </div>
              <div className="mt-4 flex gap-3">
                <button type="button" onClick={() => setIsAdding(false)} className="flex-1 py-3.5 rounded-xl font-bold bg-[var(--color-bg)] border-2 border-[var(--color-border)] hover:bg-[var(--color-surface)] transition-all">Cancel</button>
                <button type="submit" className="flex-1 py-3.5 rounded-xl font-bold bg-[#16A34A] text-white hover:bg-black transition-all shadow-lg">Create Product</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminPanel;
