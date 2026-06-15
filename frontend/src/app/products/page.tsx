import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

interface Product {
  id: string;
  name: string;
  category?: string;
  description?: string;
  image?: string;
  base_price?: number;
  original_price?: number;
  current_price?: number;
  price_change_percentage?: number;
  change_reason?: string;
}

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAllProducts = async () => {
      try {
        const url = (typeof process !== 'undefined' && process.env && process.env.NEXT_PUBLIC_API_URL)
          ? `${process.env.NEXT_PUBLIC_API_URL}/api/v1/products`
          : 'http://localhost:8000/api/v1/products';
        const response = await fetch(url);
        if (!response.ok) {
          console.error(`Error status code: ${response.status}`);
          throw new Error(`Failed to fetch product catalog: ${response.status}`);
        }
        const data = await response.json();
        setProducts(data.products || (Array.isArray(data) ? data : []));
      } catch (err: any) {
        console.error(err instanceof Error ? err.stack : err);
        setError(err.message || 'Something went wrong');
      } finally {
        setLoading(false);
      }
    };

    fetchAllProducts();
  }, []);

  return (
    <div className="min-h-screen w-full bg-[#0B1020] text-[#F9FAFB] px-6 py-12 md:px-12 lg:px-24">
      <div className="max-w-7xl mx-auto space-y-10">
        
        {/* Header Section */}
        <div className="space-y-2">
          <h1 className="text-4xl font-extrabold tracking-tight bg-gradient-to-r from-[#6D5DFC] to-[#22D3EE] bg-clip-text text-transparent">
            Storefront Catalog
          </h1>
          <p className="text-[#9CA3AF] text-sm max-w-lg">
            Explore our curated list of available items optimized by dynamic intelligence.
          </p>
        </div>

        {/* Loader State */}
        {loading && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {[...Array(8)].map((_, i) => (
              <div
                key={i}
                className="bg-[#111827]/70 backdrop-blur-md border border-white/10 rounded-2xl p-4 h-96 animate-pulse space-y-4"
              >
                <div className="bg-white/10 w-full h-40 rounded-xl" />
                <div className="h-6 bg-white/10 rounded w-3/4" />
                <div className="h-4 bg-white/10 rounded w-5/6" />
                <div className="h-10 bg-white/10 rounded-xl w-full" />
              </div>
            ))}
          </div>
        )}

        {/* Error State */}
        {!loading && error && (
          <div className="flex flex-col items-center justify-center py-20 text-center space-y-4">
            <div className="w-12 h-12 rounded-full bg-[#EF4444]/20 border border-[#EF4444]/40 flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#EF4444" strokeWidth="2.5">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
            </div>
            <h3 className="text-xl font-bold">Failed to load catalog</h3>
            <p className="text-[#9CA3AF] text-sm">{error}</p>
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && products.length === 0 && (
          <div className="text-center py-20">
            <p className="text-[#9CA3AF] text-base">No products available in the catalog—please run the database seed script.</p>
          </div>
        )}

        {/* Catalog Grid */}
        {!loading && !error && products.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {products.map((product, index) => (
              <motion.div
                key={product.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: index * 0.05 }}
                className="bg-[#111827]/70 backdrop-blur-md border border-white/10 rounded-2xl p-4 transition-all duration-300 hover:scale-[1.02] hover:border-[#6D5DFC]/50 flex flex-col justify-between min-h-[420px]"
              >
                <div className="space-y-4">
                  {/* Product Image */}
                  <div className="w-full h-40 bg-white/5 rounded-xl overflow-hidden flex items-center justify-center relative">
                    {product.image ? (
                      <img
                        src={product.image}
                        alt={product.name}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <svg
                        className="w-12 h-12 text-[#9CA3AF]/40"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="1.5"
                          d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
                        />
                      </svg>
                    )}
                  </div>

                  {/* Info */}
                  <div className="space-y-1.5">
                    <h3 className="font-bold text-lg text-[#F9FAFB] line-clamp-1">{product.name}</h3>
                    <p className="text-[#9CA3AF] text-xs line-clamp-2 leading-relaxed">
                      {product.description || "High-quality engineered option designed for peak performance and daily reliability."}
                    </p>
                  </div>

                  {/* Real-time Pricing Info */}
                  <div className="space-y-1.5 pt-3 border-t border-white/5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-baseline gap-2">
                        <span className="text-[#F9FAFB] font-extrabold text-lg">
                          ₹{product.current_price ? Math.floor(product.current_price).toLocaleString('en-IN') : '0'}
                        </span>
                        {product.current_price && product.original_price && product.current_price !== product.original_price && (
                          <span className="text-[#9CA3AF] line-through text-xs">
                            ₹{Math.floor(product.original_price).toLocaleString('en-IN')}
                          </span>
                        )}
                      </div>

                      {/* Dynamic Price Change Badge */}
                      {product.price_change_percentage !== undefined && product.price_change_percentage !== 0 && (
                        <span className={`text-[10px] font-black px-2.5 py-1 rounded-full ${
                          product.price_change_percentage > 0
                            ? 'bg-[#10B981]/10 text-[#10B981]'
                            : 'bg-[#EF4444]/10 text-[#EF4444]'
                        }`}>
                          {product.price_change_percentage > 0 ? `▲ ${product.price_change_percentage}%` : `▼ ${Math.abs(product.price_change_percentage)}%`}
                        </span>
                      )}
                    </div>

                    {/* Change Reason Explainer */}
                    {product.change_reason && (
                      <p className="text-[10px] text-[#22D3EE] font-medium italic truncate" title={product.change_reason}>
                        {product.change_reason}
                      </p>
                    )}
                  </div>
                </div>

                {/* Call To Action */}
                <a
                  href={`/products/${product.id}`}
                  className="mt-4 w-full py-2.5 rounded-xl bg-gradient-to-r from-[#6D5DFC] to-[#22D3EE] text-center font-bold text-sm text-[#0B1020] hover:opacity-90 transition-opacity"
                >
                  View Details
                </a>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
