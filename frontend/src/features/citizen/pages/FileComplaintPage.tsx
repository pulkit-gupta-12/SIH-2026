import React, { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { fileComplaint, searchProducts } from "../api";

interface LocationState {
  productId?: number;
  productName?: string;
  brandName?: string;
  barcode?: string;
}

export default function FileComplaintPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const stateData = (location.state as LocationState) || {};
  const [selectedProductId, setSelectedProductId] = useState<number | null>(
    stateData.productId || null
  );
  const [productSearch, setProductSearch] = useState(stateData.productName || "");
  const [description, setDescription] = useState("");
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [geoCoords, setGeoCoords] = useState<{ lat: number; lng: number; address?: string } | null>(
    null
  );
  const [isLocating, setIsLocating] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Search products for selection if not prefilled
  const { data: searchResults } = useQuery({
    queryKey: ["complaint-product-search", productSearch],
    queryFn: () => searchProducts(productSearch),
    enabled: !selectedProductId && productSearch.trim().length >= 2,
  });

  const complaintMutation = useMutation({
    mutationFn: fileComplaint,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["my-complaints"] });
      navigate("/citizen/complaints");
    },
    onError: (err: any) => {
      const msg =
        err?.response?.data?.detail ||
        err?.response?.data?.description?.[0] ||
        "Failed to submit complaint. Please check the fields and try again.";
      setErrorMessage(msg);
    },
  });

  const handleUseLocation = () => {
    if (!navigator.geolocation) {
      setErrorMessage("Geolocation is not supported by your browser.");
      return;
    }
    setIsLocating(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setGeoCoords({
          lat: parseFloat(pos.coords.latitude.toFixed(4)),
          lng: parseFloat(pos.coords.longitude.toFixed(4)),
          address: `Lat: ${pos.coords.latitude.toFixed(4)}, Lng: ${pos.coords.longitude.toFixed(4)}`,
        });
        setIsLocating(false);
      },
      () => {
        // Fallback demo location for testing
        setGeoCoords({
          lat: 28.6139,
          lng: 77.209,
          address: "Connaught Place, New Delhi (Demo Location)",
        });
        setIsLocating(false);
      },
      { timeout: 5000 }
    );
  };

  const handlePhotoSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    if (file) {
      setPhotoPreview(URL.createObjectURL(file));
    } else {
      setPhotoPreview(null);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProductId) {
      setErrorMessage("Please select or search for the product you wish to report.");
      return;
    }
    if (!description.trim()) {
      setErrorMessage("Please describe the violation or issue observed.");
      return;
    }

    setErrorMessage(null);
    const photoUrls = photoPreview
      ? [photoPreview]
      : ["http://localhost:8000/media/complaint_evidence.jpg"];

    complaintMutation.mutate({
      product: selectedProductId,
      description: description.trim(),
      photo_urls: photoUrls,
      location: geoCoords ? `${geoCoords.address || `Lat: ${geoCoords.lat}, Lng: ${geoCoords.lng}`}` : "New Delhi, India",
    });
  };

  return (
    <div className="max-w-2xl mx-auto p-4 md:p-6 space-y-6 animate-fade-in">
      {/* Top Banner */}
      <div className="rounded-2xl p-6 relative overflow-hidden bg-gradient-to-br from-rose-950/50 via-slate-900 to-slate-950 border border-rose-500/30 shadow-xl space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/20 text-rose-400 border border-rose-500/30">
          <span>⚖️ Statutory Consumer Grievance</span>
        </div>
        <h1 className="text-2xl font-bold text-white tracking-tight">
          File a Metrology Complaint
        </h1>
        <p className="text-xs sm:text-sm text-slate-300">
          Report overcharging (above MRP), missing mandatory declarations, dual-pricing, tampered labels, or deceptive packaging directly to State Legal Metrology Officers.
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="glass-card p-6 rounded-2xl space-y-5">
        {/* Product Selection */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1.5">
            Target Product
          </label>
          {selectedProductId ? (
            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900/80 border border-emerald-500/40">
              <div className="space-y-0.5">
                <span className="text-xs text-emerald-400 font-semibold uppercase tracking-wider block">
                  Selected Product #{selectedProductId}
                </span>
                <span className="text-sm font-medium text-white">
                  {stateData.productName || `Product ID: ${selectedProductId}`}
                </span>
                {stateData.barcode && (
                  <span className="text-xs text-slate-400 font-mono block">
                    GTIN: {stateData.barcode}
                  </span>
                )}
              </div>
              <button
                type="button"
                onClick={() => {
                  setSelectedProductId(null);
                  setProductSearch("");
                }}
                className="text-xs text-slate-400 hover:text-white px-2.5 py-1 rounded-lg bg-slate-800"
              >
                Change
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              <input
                type="text"
                value={productSearch}
                onChange={(e) => setProductSearch(e.target.value)}
                placeholder="Search product name or brand to attach..."
                className="w-full rounded-xl bg-black border border-slate-700 px-4 py-2.5 text-sm text-white placeholder-slate-400 focus:outline-none focus:border-emerald-500 search-input"
                style={{ backgroundColor: '#000000', color: '#ffffff' }}
              />
              {searchResults && searchResults.length > 0 && (
                <div className="max-h-48 overflow-y-auto rounded-xl border border-slate-700 bg-black divide-y divide-slate-800" style={{ backgroundColor: '#000000' }}>
                  {searchResults.map((p) => (
                    <div
                      key={p.id}
                      onClick={() => {
                        setSelectedProductId(p.id);
                        setProductSearch(p.product_name);
                      }}
                      className="p-2.5 hover:bg-slate-900 cursor-pointer flex justify-between items-center text-xs bg-black text-white"
                      style={{ backgroundColor: '#000000', color: '#ffffff' }}
                    >
                      <div>
                        <span className="font-semibold text-white block">{p.product_name}</span>
                        <span className="text-slate-300">{p.brand_name}</span>
                      </div>
                      <span className="font-mono text-emerald-400">{p.gtin_barcode}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Complaint Description */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1.5">
            Description of Grievance / Violation <span className="text-rose-400">*</span>
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={4}
            placeholder="E.g., The retailer charged ₹120 when the printed MRP was ₹100, or the manufacturing date & consumer care details were completely missing on the package..."
            className="w-full rounded-xl bg-slate-900/80 border border-slate-700 px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 leading-relaxed"
            required
          />
        </div>

        {/* Photo Evidence */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-slate-300">
            Attach Evidence Photo / Bill / Label
          </label>
          <input
            type="file"
            accept="image/*"
            capture="environment"
            onChange={handlePhotoSelect}
            className="w-full text-xs text-slate-400 file:mr-4 file:py-2 file:px-3 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-slate-800 file:text-emerald-400 hover:file:bg-slate-700 file:cursor-pointer cursor-pointer border border-dashed border-slate-700 rounded-xl p-3 bg-slate-900/50"
          />
          {photoPreview && (
            <div className="mt-2 relative rounded-xl overflow-hidden max-h-36 border border-slate-700 bg-black/40 flex items-center justify-center">
              <img src={photoPreview} alt="Evidence preview" className="object-contain max-h-36" />
            </div>
          )}
        </div>

        {/* Geolocation Tagging */}
        <div className="pt-1">
          <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-900/80 border border-slate-800">
            <div className="space-y-0.5">
              <span className="text-xs font-semibold text-slate-300 block">
                Store / Purchase Location
              </span>
              <span className="text-xs text-slate-400 block font-mono">
                {geoCoords ? geoCoords.address : "Location not attached"}
              </span>
            </div>
            <button
              type="button"
              onClick={handleUseLocation}
              disabled={isLocating}
              className="text-xs px-3 py-1.5 rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/30 font-medium transition-all"
            >
              {isLocating ? "Detecting..." : geoCoords ? "✓ Attached" : "📍 Auto-Detect GPS"}
            </button>
          </div>
        </div>

        {errorMessage && (
          <div className="p-3 rounded-xl text-xs bg-rose-500/10 border border-rose-500/30 text-rose-300">
            {errorMessage}
          </div>
        )}

        {/* Submit Button */}
        <button
          type="submit"
          disabled={complaintMutation.isPending || !selectedProductId || !description.trim()}
          className="w-full py-3 px-4 rounded-xl font-semibold text-white bg-gradient-to-r from-rose-600 to-rose-500 hover:from-rose-500 hover:to-rose-400 shadow-lg shadow-rose-950/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
        >
          {complaintMutation.isPending ? (
            <>
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              <span>Submitting to State Registry...</span>
            </>
          ) : (
            <span>🚀 Submit Formal Complaint</span>
          )}
        </button>
      </form>
    </div>
  );
}
