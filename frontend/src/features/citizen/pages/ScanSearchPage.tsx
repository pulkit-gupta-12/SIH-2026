import React, { useCallback, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { scanOrLookupProduct, searchProducts, type ComplianceSnapshot } from "../api";
import CameraCaptureView from "../../../components/camera/CameraCaptureView";
import type { CapturedFrame } from "../../../components/camera/useCamera";

const POPULAR_DEMO_BARCODES = [
  { barcode: "8901030865412", name: "Amul Butter 500g", category: "food" },
  { barcode: "8901234567890", name: "Heritage Tea 500g", category: "food" },
  { barcode: "8904004400123", name: "Dabur Honey 250g", category: "food" },
];

export default function ScanSearchPage() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<"camera" | "barcode">("camera");
  const [barcode, setBarcode] = useState("");
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("general");
  const [capturedFrame, setCapturedFrame] = useState<CapturedFrame | null>(null);
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
        setActiveTab("camera");
        setErrorMessage(
          "First-time scan: This product hasn't been scanned yet. Please snap a photo of the label declarations using the live camera."
        );
      } else {
        const detail = err?.response?.data?.detail || "Unable to look up product. Please try again.";
        setErrorMessage(detail);
      }
    },
  });

  const handleBarcodeDetected = useCallback((detectedBarcode: string) => {
    setBarcode(detectedBarcode);
    setErrorMessage(null);
    scanMutation.mutate({ barcode: detectedBarcode, category });
  }, [category, scanMutation]);

  // React Query for live text search
  const { data: searchResults, isFetching: isSearching } = useQuery({
    queryKey: ["product-search", query],
    queryFn: () => searchProducts(query),
    enabled: query.trim().length >= 2,
    staleTime: 10_000,
  });

  // Handle barcode verification
  const handleBarcodeSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!barcode.trim()) return;
    setErrorMessage(null);
    scanMutation.mutate({ barcode: barcode.trim(), category });
  };

  // Handle frame capture from live camera or file fallback
  const handleCameraCapture = (frame: CapturedFrame) => {
    setCapturedFrame(frame);
    setErrorMessage(null);
  };

  // Submit captured camera photo to scan pipeline
  const handleSubmitPhotoScan = () => {
    if (!capturedFrame) return;
    setErrorMessage(null);
    scanMutation.mutate({
      barcode: barcode.trim() || undefined,
      imageUrl: capturedFrame.dataUrl,
      category,
    });
  };

  const inputClasses = "w-full rounded-lg bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] px-4 py-2.5 text-[var(--color-text-primary)] placeholder:text-[var(--color-text-muted)] text-sm focus:outline-none focus:border-[var(--color-accent)] transition-colors";

  return (
    <div className="max-w-2xl mx-auto p-4 md:p-6 space-y-6 animate-fade-in">
      {/* Header Banner */}
      <div className="glass-card card-accent-left p-6">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-[var(--color-accent-subtle)] text-[var(--color-accent)]">
            <span>🛡️ Legal Metrology Verified</span>
          </div>
          <h1 className="text-2xl md:text-3xl font-bold text-[var(--color-text-primary)] tracking-tight">
            Scan and verify product
          </h1>
          <p className="text-sm text-[var(--color-text-secondary)] max-w-lg">
            Instant compliance check on MRP, Net Quantity, Expiry, Manufacturer info, and Consumer Care details under the Legal Metrology Rules.
          </p>
        </div>
      </div>

      {/* Mode Selector Tabs */}
      <div className="grid grid-cols-2 p-1.5 rounded-lg bg-[var(--color-surface-tertiary)] border border-[var(--color-border)]">
        <button
          type="button"
          onClick={() => {
            setActiveTab("camera");
            setErrorMessage(null);
          }}
          className={`py-2.5 px-4 rounded-md text-sm font-semibold transition-colors flex items-center justify-center gap-2 ${
            activeTab === "camera"
              ? "bg-[var(--color-accent)] text-[var(--color-text-primary)] shadow-sm"
              : "text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]"
          }`}
        >
          <span>📸</span>
          <span>Live camera scan</span>
        </button>

        <button
          type="button"
          onClick={() => {
            setActiveTab("barcode");
            setErrorMessage(null);
          }}
          className={`py-2.5 px-4 rounded-md text-sm font-semibold transition-colors flex items-center justify-center gap-2 ${
            activeTab === "barcode"
              ? "bg-[var(--color-accent)] text-[var(--color-text-primary)] shadow-sm"
              : "text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]"
          }`}
        >
          <span>🔢</span>
          <span>Barcode / GTIN lookup</span>
        </button>
      </div>

      {/* Main Scan Card */}
      <div className="glass-card p-6 space-y-6">
        {/* Category selector */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[var(--color-border)] pb-4">
          <label className="text-xs font-semibold text-[var(--color-text-secondary)]">
            Commodity category
          </label>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="rounded-lg bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] px-3 py-1.5 text-[var(--color-text-primary)] text-xs focus:outline-none focus:border-[var(--color-accent)]"
          >
            <option value="general">General Commodities</option>
            <option value="food">Food & Beverages</option>
            <option value="electronics">Electronics</option>
            <option value="medical_device">Medical Devices</option>
            <option value="import">Imported Goods</option>
          </select>
        </div>

        {/* TAB 1: LIVE CAMERA CAPTURE */}
        {activeTab === "camera" && (
          <div className="space-y-5 animate-fade-in">
            {needsPhoto && (
              <div className="p-3.5 rounded-lg bg-[var(--color-accent-subtle)] border border-[var(--color-accent)] space-y-1">
                <div className="flex items-center gap-2 text-[var(--color-accent)] font-semibold text-xs">
                  <span>📸 First-time scan required</span>
                </div>
                <p className="text-xs text-[var(--color-text-secondary)]">
                  Barcode <span className="font-mono text-[var(--color-text-primary)]">{barcode}</span> has not been scanned yet. Snap a clear photo of the declaration panel to analyze.
                </p>
              </div>
            )}

            {/* Live Camera Viewfinder */}
            <CameraCaptureView
              title="Declaration Panel"
              instruction="Point rear camera at MRP, Net Qty & Manufacturer info"
              capturedImage={capturedFrame?.dataUrl || null}
              onCapture={handleCameraCapture}
              onRetake={() => setCapturedFrame(null)}
              isProcessing={scanMutation.isPending}
              reticleType="declarations"
              autoStart={true}
              defaultFacingMode="environment"
            />

            {/* Optional Barcode association field */}
            <div>
              <label className="block text-xs font-medium text-[var(--color-text-muted)] mb-1">
                Barcode number (optional, if visible on package)
              </label>
              <input
                type="text"
                value={barcode}
                onChange={(e) => setBarcode(e.target.value)}
                placeholder="e.g. 8901030865412 (optional)"
                className={`${inputClasses} font-mono text-xs`}
              />
            </div>

            {/* Action Submit Button */}
            {capturedFrame && (
              <button
                type="button"
                onClick={handleSubmitPhotoScan}
                disabled={scanMutation.isPending}
                className="w-full py-3.5 px-4 rounded-lg font-semibold text-[var(--color-text-primary)] disabled:opacity-50 flex items-center justify-center gap-2 transition-colors"
                style={{ background: 'linear-gradient(135deg, #e8730c, #d4670a)' }}
              >
                {scanMutation.isPending ? (
                  <>
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Running OCR and rules engine...</span>
                  </>
                ) : (
                  <span>⚡ Analyze label photo and verify compliance</span>
                )}
              </button>
            )}
          </div>
        )}

        {/* TAB 2: BARCODE & GTIN LOOKUP */}
        {activeTab === "barcode" && (
          <div className="space-y-4 animate-fade-in">
            <CameraCaptureView
              title="Barcode"
              instruction="Align the barcode inside the box"
              onCapture={() => undefined}
              onBarcodeDetected={handleBarcodeDetected}
              isProcessing={scanMutation.isPending}
              reticleType="barcode"
              autoStart={true}
              defaultFacingMode="environment"
            />

            <div className="text-center text-xs text-[var(--color-text-muted)]">
              The product record and compliance result will load automatically when the barcode is detected.
            </div>

            <form onSubmit={handleBarcodeSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-[var(--color-text-secondary)] mb-1.5">
                Scan or enter barcode (GTIN)
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={barcode}
                  onChange={(e) => setBarcode(e.target.value)}
                  placeholder="e.g. 8901234567890"
                  className={`${inputClasses} font-mono text-base py-3`}
                  required
                />
                <button
                  type="button"
                  onClick={() => setBarcode("8901030865412")}
                  className="absolute right-2 top-2 px-3 py-1.5 rounded-md text-xs font-medium bg-[var(--color-surface-tertiary)] hover:bg-gray-200 text-[var(--color-accent)] border border-[var(--color-border)] transition-colors"
                >
                  Fill sample
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={scanMutation.isPending || !barcode.trim()}
              className="w-full py-3 px-4 rounded-lg font-semibold text-[var(--color-text-primary)] disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-150 flex items-center justify-center gap-2"
              style={{ background: 'linear-gradient(135deg, #e8730c, #d4670a)' }}
            >
              {scanMutation.isPending ? (
                <>
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Checking compliance database...</span>
                </>
              ) : (
                <>
                  <span>🔍 Verify barcode</span>
                </>
              )}
            </button>
            </form>
          </div>
        )}

        {errorMessage && (
          <div className="p-3.5 rounded-lg text-sm bg-red-50 border border-red-200 text-red-700">
            {errorMessage}
          </div>
        )}

        {/* Quick Sample Barcodes */}
        <div className="pt-2">
          <p className="text-xs font-semibold text-[var(--color-text-muted)] mb-2">
            Try demo barcodes
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
                className="text-left p-2.5 rounded-lg bg-[var(--color-surface-tertiary)] hover:bg-gray-200 border border-[var(--color-border)] hover:border-[var(--color-accent)] transition-all text-xs group"
              >
                <div className="font-semibold text-[var(--color-text-primary)] group-hover:text-[var(--color-accent)] truncate">
                  {item.name}
                </div>
                <div className="font-mono text-[var(--color-text-muted)] text-[11px]">{item.barcode}</div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Manual Search Fallback */}
      <div className="glass-card p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-[var(--color-text-primary)]">
            Or search product directory
          </h2>
          <span className="text-xs text-[var(--color-text-muted)]">By name, brand, or manufacturer</span>
        </div>

        <div className="relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type brand or product name (e.g. Amul, Tata, Dabur)..."
            className={inputClasses}
          />
          {isSearching && (
            <div className="absolute right-3 top-3 w-4 h-4 border-2 border-[var(--color-accent)]/30 border-t-[var(--color-accent)] rounded-full animate-spin" />
          )}
        </div>

        {searchResults && searchResults.length > 0 && (
          <div className="space-y-2 mt-3 max-h-64 overflow-y-auto">
            {searchResults.map((p) => (
              <div
                key={p.id}
                onClick={() => navigate(`/citizen/product/${p.id}/snapshot`)}
                className="flex items-center justify-between p-3 rounded-lg bg-[var(--color-surface-tertiary)] hover:bg-gray-200 border border-[var(--color-border)] hover:border-[var(--color-accent)] cursor-pointer transition-all"
              >
                <div className="space-y-0.5">
                  <div className="font-medium text-sm text-[var(--color-text-primary)]">{p.product_name}</div>
                  <div className="text-xs text-[var(--color-text-muted)] flex gap-2">
                    <span className="text-[var(--color-accent)] font-medium">{p.brand_name}</span>
                    <span>·</span>
                    <span className="font-mono">{p.gtin_barcode || "No barcode"}</span>
                  </div>
                </div>
                <span className="text-xs px-2.5 py-1 rounded-md bg-[var(--color-accent-subtle)] text-[var(--color-accent)]">
                  View snapshot →
                </span>
              </div>
            ))}
          </div>
        )}

        {query.trim().length >= 2 && searchResults && searchResults.length === 0 && !isSearching && (
          <div className="text-center py-4 text-xs text-[var(--color-text-muted)]">
            No products found matching &ldquo;{query}&rdquo;. Try entering the barcode directly above.
          </div>
        )}
      </div>
    </div>
  );
}
