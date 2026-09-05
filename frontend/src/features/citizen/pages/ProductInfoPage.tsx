import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getProduct } from "../api";

export default function ProductInfoPage() {
  const { productId } = useParams<{ productId: string }>();
  const navigate = useNavigate();

  const {
    data: product,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["product-detail", productId],
    queryFn: () => getProduct(Number(productId)),
    enabled: !!productId,
  });

  if (isLoading) {
    return (
      <div className="max-w-2xl mx-auto p-6 space-y-4 text-center py-20 animate-fade-in">
        <div className="w-10 h-10 border-3 border-green-200 border-t-emerald-500 rounded-full animate-spin mx-auto" />
        <p className="text-sm text-[var(--color-text-muted)]">Loading product information...</p>
      </div>
    );
  }

  if (isError || !product) {
    return (
      <div className="max-w-2xl mx-auto p-6 space-y-4">
        <div className="glass-card p-6 rounded-2xl text-center space-y-3">
          <div className="text-4xl">⚠️</div>
          <h2 className="text-lg font-semibold text-[var(--color-text-primary)]">Product Not Found</h2>
          <p className="text-sm text-[var(--color-text-muted)]">Unable to retrieve product master records.</p>
          <button
            onClick={() => navigate("/citizen/scan")}
            className="px-4 py-2 rounded-xl bg-[var(--color-accent)] text-[var(--color-text-primary)] text-sm font-semibold"
          >
            Back to Scanner
          </button>
        </div>
      </div>
    );
  }

  const detailRows = [
    { label: "Product Name", value: product.product_name },
    { label: "Brand Name", value: product.brand_name },
    { label: "Barcode / GTIN", value: product.gtin_barcode || "Not Assigned", mono: true },
    { label: "Commodity Category", value: product.category ? product.category.replace(/_/g, " ") : "General" },
    { label: "Manufacturer Name", value: product.manufacturer_name },
    { label: "Manufacturer Address", value: product.manufacturer_address },
    {
      label: "Registered in Portal",
      value: product.created_at
        ? new Date(product.created_at).toLocaleDateString("en-IN", {
            day: "numeric",
            month: "short",
            year: "numeric",
          })
        : "—",
    },
  ];

  return (
    <div className="max-w-2xl mx-auto p-4 md:p-6 space-y-6 animate-fade-in">
      {/* Top Header */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate(`/citizen/product/${product.id}/snapshot`)}
          className="flex items-center gap-1.5 text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors"
        >
          <span>←</span>
          <span>Back to Snapshot</span>
        </button>
        <button
          onClick={() =>
            navigate("/citizen/complaint/new", {
              state: {
                productId: product.id,
                productName: product.product_name,
                brandName: product.brand_name,
                barcode: product.gtin_barcode,
              },
            })
          }
          className="text-xs px-3 py-1.5 rounded-lg bg-red-50 text-red-600 border border-red-200 hover:bg-rose-500/30 transition-all font-medium"
        >
          Report Issue
        </button>
      </div>

      {/* Product Title Card */}
      <div className="glass-card p-6 rounded-2xl border border-[var(--color-border)] space-y-2">
        <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[var(--color-surface-tertiary)] text-[var(--color-accent)] border border-[var(--color-border)]">
          <span>🏛️ National Product Registry</span>
        </div>
        <h1 className="text-xl md:text-2xl font-bold text-[var(--color-text-primary)] tracking-tight">
          {product.product_name}
        </h1>
        <p className="text-sm text-[var(--color-text-muted)]">
          Official manufacturer registration details verified under Legal Metrology portal.
        </p>
      </div>

      {/* Specifications Table */}
      <div className="glass-card rounded-2xl border border-[var(--color-border)] overflow-hidden divide-y divide-[var(--color-border)]">
        {detailRows.map((row, idx) => (
          <div
            key={idx}
            className="flex flex-col sm:flex-row sm:items-center justify-between p-4 text-sm gap-1 hover:bg-[var(--color-surface-tertiary)] transition-colors"
          >
            <span className="text-xs sm:text-sm font-medium text-[var(--color-text-muted)] w-44">
              {row.label}
            </span>
            <span
              className={`text-[var(--color-text-primary)] font-semibold sm:text-right ${
                row.mono ? "font-mono text-[var(--color-accent)] text-xs sm:text-sm" : ""
              }`}
            >
              {row.value || "—"}
            </span>
          </div>
        ))}
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <button
          onClick={() => navigate(`/citizen/product/${product.id}/snapshot`)}
          className="flex-1 py-3 rounded-xl font-semibold text-[var(--color-text-primary)] bg-[var(--color-accent)] hover:bg-[var(--color-accent)] shadow-lg shadow-sm transition-all text-sm text-center"
        >
          View Compliance Verdict →
        </button>
      </div>
    </div>
  );
}
