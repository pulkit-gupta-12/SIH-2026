import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { scanOrLookupProduct, searchProducts, type ComplianceSnapshot } from "../api";

const POPULAR_DEMO_BARCODES = [
  { barcode: "8901030865412", name: "Amul Butter 500g", category: "food" },
  { barcode: "8901234567890", name: "Heritage Tea 500g", category: "food" },
  { barcode: "8904004400123", name: "Dabur Honey 250g", category: "food" },
];

export default function ScanSearchPage() {
  const navigate = useNavigate();
  const [barcode, setBarcode] = useState("");
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("general");
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [needsPhoto, setNeedsPhoto] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // React Query mutation for scanning/lookup
  const scanMutation = useMutation({
    mutationFn: scanOrLookupProduct,
    onSuccess: (snapshot: ComplianceSnapshot) => {
      navigate(`/citizen/product/${snapshot.product_id}/snapshot`, { state: snapshot });
    },
    onError: (err: any) => {
      if (err?.response?.status === 400 && err?.response?.data?.needs_photo) {
        setNeedsPhoto(true);
        setErrorMessage(
          "First-time scan: This product hasn't been scanned yet. Please upload a photo of the label declarations."
        );
      } else {
        const detail = err?.response?.data?.detail || "Unable to look up product. Please try again.";
        setErrorMessage(detail);
      }
    },
  });

  // React Query for live text search
  const { data: searchResults, isFetching: isSearching } = useQuery({
    queryKey: ["product-search", query],
    queryFn: () => searchProducts(query),
    enabled: query.trim().length >= 2,
    staleTime: 10_000,
  });

  const handleBarcodeSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!barcode.trim()) return;
    setErrorMessage(null);
    scanMutation.mutate({ barcode: barcode.trim(), category });
  };

  const handlePhotoSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    if (file) {
      setPhotoPreview(URL.createObjectURL(file));
    } else {
      setPhotoPreview(null);
    }
  };

  const handlePhotoSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!photoPreview) return;
    setErrorMessage(null);
    // In production or demo, use object URL or media URL
    const imageUrl = photoPreview || "http://localhost:8000/media/sample_label.jpg";
    scanMutation.mutate({
      barcode: barcode.trim() || undefined,
      imageUrl,
      category,
    });
  };

  return (
    <div className="max-w-2xl mx-auto p-4 md:p-6 space-y-8 animate-fade-in">
      {/* Header Banner */}
      <div className="rounded-2xl p-6 relative overflow-hidden bg-gradient-to-br from-emerald-950/70 via-slate-900 to-slate-950 border border-emerald-500/20 shadow-xl">
        <div className="absolute top-0 right-0 p-8 opacity-10 pointer-events-none">
          <span className="text-8xl">📷</span>
        </div>
        <div className="relative z-10 space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
            <span>🛡️ Legal Metrology Verified</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-white tracking-tight">
            Scan & Verify Product
          </h1>
          <p className="text-sm text-slate-300 max-w-lg">
            Instant compliance check on MRP, Net Quantity, Expiry, Manufacturer info, and Consumer Care details under the Legal Metrology Rules.
          </p>
        </div>
      </div>

      {/* Main Scan Form */}
      <div className="glass-card p-6 rounded-2xl space-y-6">
        {!needsPhoto ? (
          <form onSubmit={handleBarcodeSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">
                Scan or Enter Barcode (GTIN)
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={barcode}
                  onChange={(e) => setBarcode(e.target.value)}
                  placeholder="e.g. 8901234567890"
                  className="w-full rounded-xl bg-slate-900/80 border border-slate-700/80 px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 transition-all font-mono text-base"
                  required
                />
                <button
                  type="button"
                  onClick={() => setBarcode("8901030865412")}
                  className="absolute right-2 top-2 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800 hover:bg-slate-700 text-emerald-400 border border-slate-700 transition-colors"
                >
                  Fill Sample
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1.5">
                Category (optional)
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full rounded-xl bg-slate-900/80 border border-slate-700/80 px-4 py-2.5 text-white text-sm focus:outline-none focus:border-emerald-500"
              >
                <option value="general">General Commodities</option>
                <option value="food">Food & Beverages</option>
                <option value="electronics">Electronics</option>
                <option value="medical_device">Medical Devices</option>
                <option value="import">Imported Goods</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={scanMutation.isPending || !barcode.trim()}
              className="w-full py-3 px-4 rounded-xl font-semibold text-white bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 shadow-lg shadow-emerald-950/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center justify-center gap-2"
            >
              {scanMutation.isPending ? (
                <>
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Checking Compliance Database...</span>
                </>
              ) : (
                <>
                  <span>🔍 Verify Barcode</span>
                </>
              )}
            </button>
          </form>
        ) : (
          /* First-Time Scan: Photo Upload Required */
          <form onSubmit={handlePhotoSubmit} className="space-y-4 animate-fade-in">
            <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-500/30 space-y-2">
              <div className="flex items-center gap-2 text-emerald-400 font-semibold text-sm">
                <span>📸 First-Time Scan Required</span>
              </div>
              <p className="text-xs text-slate-300">
                Barcode <span className="font-mono text-white">{barcode}</span> hasn&apos;t been verified yet. Upload a photo of the product package declaration panel to trigger automated verification.
              </p>
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-medium text-slate-300">
                Take or Upload Label Photo
              </label>
              <input
                type="file"
                accept="image/*"
                capture="environment"
                onChange={handlePhotoSelect}
                className="w-full text-sm text-slate-400 file:mr-4 file:py-2.5 file:px-4 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-emerald-500/20 file:text-emerald-400 hover:file:bg-emerald-500/30 file:cursor-pointer cursor-pointer border border-dashed border-slate-700 rounded-xl p-3 bg-slate-900/50"
                required
              />
              {photoPreview && (
                <div className="mt-3 relative rounded-xl overflow-hidden max-h-48 border border-slate-700 bg-black/40 flex items-center justify-center">
                  <img src={photoPreview} alt="Label preview" className="object-contain max-h-48 w-full" />
                </div>
              )}
            </div>

            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => {
                  setNeedsPhoto(false);
                  setErrorMessage(null);
                }}
                className="px-4 py-2.5 rounded-xl text-sm font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700"
              >
                Back
              </button>
              <button
                type="submit"
                disabled={scanMutation.isPending || !photoPreview}
                className="flex-1 py-2.5 px-4 rounded-xl font-semibold text-white bg-gradient-to-r from-emerald-600 to-emerald-500 hover:from-emerald-500 hover:to-emerald-400 shadow-lg disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {scanMutation.isPending ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Running OCR & Rules Engine...</span>
                  </>
                ) : (
                  <span>⚡ Analyze Label Photo</span>
                )}
              </button>
            </div>
          </form>
        )}

        {errorMessage && (
          <div className="p-3.5 rounded-xl text-sm bg-rose-500/10 border border-rose-500/30 text-rose-300">
            {errorMessage}
          </div>
        )}

        {/* Quick Sample Barcodes */}
        <div className="pt-2">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
            Try Demo Barcodes
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            {POPULAR_DEMO_BARCODES.map((item) => (
              <button
                key={item.barcode}
                type="button"
                onClick={() => {
                  setBarcode(item.barcode);
                  setCategory(item.category);
                  setNeedsPhoto(false);
                  setErrorMessage(null);
                }}
                className="text-left p-2.5 rounded-xl bg-slate-900/60 hover:bg-slate-800 border border-slate-800 hover:border-emerald-500/30 transition-all text-xs group"
              >
                <div className="font-semibold text-slate-200 group-hover:text-emerald-400 truncate">
                  {item.name}
                </div>
                <div className="font-mono text-slate-400 text-[11px]">{item.barcode}</div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Manual Search Fallback */}
      <div className="glass-card p-6 rounded-2xl space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-200">
            Or Search Product Directory
          </h2>
          <span className="text-xs text-slate-400">By name, brand, or manufacturer</span>
        </div>

        <div className="relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type brand or product name (e.g. Amul, Tata, Dabur)..."
            className="w-full rounded-xl bg-slate-900/80 border border-slate-700/80 px-4 py-2.5 text-white placeholder-slate-500 text-sm focus:outline-none focus:border-emerald-500"
          />
          {isSearching && (
            <div className="absolute right-3 top-3 w-4 h-4 border-2 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin" />
          )}
        </div>

        {searchResults && searchResults.length > 0 && (
          <div className="space-y-2 mt-3 max-h-64 overflow-y-auto">
            {searchResults.map((p) => (
              <div
                key={p.id}
                onClick={() => navigate(`/citizen/product/${p.id}/snapshot`)}
                className="flex items-center justify-between p-3 rounded-xl bg-slate-900/50 hover:bg-slate-800/80 border border-slate-800/80 hover:border-emerald-500/30 cursor-pointer transition-all"
              >
                <div className="space-y-0.5">
                  <div className="font-medium text-sm text-white">{p.product_name}</div>
                  <div className="text-xs text-slate-400 flex gap-2">
                    <span className="text-emerald-400 font-medium">{p.brand_name}</span>
                    <span>·</span>
                    <span className="font-mono">{p.gtin_barcode || "No barcode"}</span>
                  </div>
                </div>
                <span className="text-xs px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300 group-hover:bg-emerald-500/20 group-hover:text-emerald-300">
                  View Snapshot →
                </span>
              </div>
            ))}
          </div>
        )}

        {query.trim().length >= 2 && searchResults && searchResults.length === 0 && !isSearching && (
          <div className="text-center py-4 text-xs text-slate-400">
            No products found matching &ldquo;{query}&rdquo;. Try entering the barcode directly above.
          </div>
        )}
      </div>
    </div>
  );
}
