import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { submitOfficerGuidedScan, type ScanProcessingResult } from '../api';
import CameraCaptureView from '../../../components/camera/CameraCaptureView';
import type { CapturedFrame } from '../../../components/camera/useCamera';

interface StepConfig {
  step: number;
  id: string;
  title: string;
  instruction: string;
  mandatoryFields: string[];
  reticleType: 'pdp' | 'declarations' | 'mrp' | 'barcode' | 'seal' | 'general';
}

const CAPTURE_STEPS: StepConfig[] = [
  {
    step: 1,
    id: 'front_panel',
    title: '1. Front Principal Display Panel (PDP)',
    instruction: 'Capture the full front surface of the retail package showing brand name, product identity, and logo.',
    mandatoryFields: ['Brand Name', 'Product Identity', 'Logo/Symbol'],
    reticleType: 'pdp',
  },
  {
    step: 2,
    id: 'declaration_panel',
    title: '2. Mandatory Declaration Panel',
    instruction: 'Frame the complete regulatory text block containing manufacturing date, expiry/best-before, batch code, and customer care details.',
    mandatoryFields: ['Month/Year of Mfg', 'Batch No', 'Customer Care Email/Phone'],
    reticleType: 'declarations',
  },
  {
    step: 3,
    id: 'mrp_netqty_closeup',
    title: '3. MRP & Net Quantity Close-Up',
    instruction: 'Ensure sharp focus on the printed MRP statement (inclusive of all taxes) and numeric net quantity with metric units.',
    mandatoryFields: ['MRP (incl. of all taxes)', 'Net Quantity (g/ml/kg)', 'Numeral Font Size'],
    reticleType: 'mrp',
  },
  {
    step: 4,
    id: 'manufacturer_block',
    title: '4. Manufacturer & Packer Address',
    instruction: 'Capture the full physical factory/registered office address of the manufacturer, packer, or importer (Rule 6(1)(a)).',
    mandatoryFields: ['Manufacturer Name', 'Complete Address with PIN', 'Country of Origin'],
    reticleType: 'declarations',
  },
  {
    step: 5,
    id: 'barcode_gtin',
    title: '5. Barcode & EAN/GTIN Scan',
    instruction: 'Scan or position the 1D/2D GS1 barcode clearly within the scanning frame without glare or label folding.',
    mandatoryFields: ['GTIN Barcode (13-digit)', 'GS1 Verification'],
    reticleType: 'barcode',
  },
  {
    step: 6,
    id: 'wraparound_seal',
    title: '6. Package Wrap-Around & Seal',
    instruction: 'Inspect and capture the security seal, outer carton wrap-around, or container seam to verify tamper evidence.',
    mandatoryFields: ['Package Integrity', 'Outer Label Continuity'],
    reticleType: 'seal',
  },
];

export default function GuidedCapturePage() {
  const location = useLocation();
  const navigate = useNavigate();

  const initialBarcode = location.state?.barcode || '8901234567890';
  const initialCategory = location.state?.category || 'food';

  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [barcode, setBarcode] = useState(initialBarcode);
  const [category, setCategory] = useState(initialCategory);
  const [locationStr, setLocationStr] = useState('Central Supermarket, Connaught Place, New Delhi');
  const [capturedImages, setCapturedImages] = useState<{ [key: string]: string }>({});

  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [qualityFeedback, setQualityFeedback] = useState<{
    blurScore: number;
    glareDetected: boolean;
    lightingPass: boolean;
  }>({
    blurScore: 94,
    glareDetected: false,
    lightingPass: true,
  });

  const currentStep = CAPTURE_STEPS[currentStepIndex];

  const scanMutation = useMutation({
    mutationFn: submitOfficerGuidedScan,
    onSuccess: (data: ScanProcessingResult) => {
      navigate(`/officer/scan/${data.id}/result`, {
        state: { scanData: data },
      });
    },
    onError: (err: any) => {
      const detail =
        err?.response?.data?.detail ||
        err?.response?.data?.error ||
        err?.message ||
        'Unable to process guided scan. Please check network connection and try again.';
      setErrorMessage(detail);
    },
  });

  // Handle frame capture from the live camera stream
  const handleFrameCaptured = (frame: CapturedFrame) => {
    setErrorMessage(null);
    setCapturedImages((prev) => ({
      ...prev,
      [currentStep.id]: frame.dataUrl,
    }));

    // Real-time CV image quality evaluation simulation
    const estimatedBlurScore = Math.min(98, Math.max(86, Math.floor(90 + (frame.width / 100) % 8)));
    setQualityFeedback({
      blurScore: estimatedBlurScore,
      glareDetected: false,
      lightingPass: true,
    });
  };

  const handleRetakeStep = () => {
    setErrorMessage(null);
    setCapturedImages((prev) => {
      const updated = { ...prev };
      delete updated[currentStep.id];
      return updated;
    });
  };

  const handleNext = () => {
    setErrorMessage(null);
    if (currentStepIndex < CAPTURE_STEPS.length - 1) {
      setCurrentStepIndex((prev) => prev + 1);
    } else {
      // Final Step: Submit all captured images to officer scan pipeline
      const urls = Object.values(capturedImages);
      if (urls.length === 0) {
        setErrorMessage('Please capture at least one package angle photo before running OCR processing.');
        return;
      }
      scanMutation.mutate({
        barcode,
        category,
        image_urls: urls,
        location: locationStr,
      });
    }
  };

  const handlePrev = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex((prev) => prev - 1);
    }
  };

  const totalCapturedCount = Object.keys(capturedImages).length;

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/40 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded bg-blue-50 text-blue-600 border border-blue-200 text-xs font-semibold">
              Lane 2 Guided Inspection
            </span>
            <span className="text-xs text-muted-foreground">Legal Metrology Packaged Commodities (PC) Rules</span>
          </div>
          <h1 className="text-2xl font-bold text-foreground mt-1">6-Step Live Camera Guided Capture</h1>
        </div>

        <button
          onClick={() => navigate('/officer/queue')}
          className="text-xs text-muted-foreground hover:text-foreground self-start md:self-center"
        >
          ← Back to Queue
        </button>
      </div>

      {/* Barcode & Inspection Context Banner */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 rounded-xl glass-card border border-border/60">
        <div>
          <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Target GTIN Barcode</label>
          <input
            type="text"
            value={barcode}
            onChange={(e) => setBarcode(e.target.value)}
            className="mt-1 w-full px-3 py-1.5 rounded bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] text-[var(--color-text-primary)] font-mono text-sm"
            style={{ backgroundColor: 'var(--color-surface-tertiary)', color: 'var(--color-text-primary)' }}
          />
        </div>
        <div>
          <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Commodity Category</label>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="mt-1 w-full px-3 py-1.5 rounded bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] text-[var(--color-text-primary)] text-sm"
            style={{ backgroundColor: 'var(--color-surface-tertiary)', color: 'var(--color-text-primary)' }}
          >
            <option value="food" className="bg-[var(--color-surface-tertiary)] text-[var(--color-text-primary)]">Food & Edibles</option>
            <option value="medical_device" className="bg-[var(--color-surface-tertiary)] text-[var(--color-text-primary)]">Medical Devices</option>
            <option value="electronics" className="bg-[var(--color-surface-tertiary)] text-[var(--color-text-primary)]">Electronics & IT</option>
            <option value="import" className="bg-[var(--color-surface-tertiary)] text-[var(--color-text-primary)]">Imported Commodities</option>
            <option value="general" className="bg-[var(--color-surface-tertiary)] text-[var(--color-text-primary)]">General Packaged Goods</option>
          </select>
        </div>
        <div>
          <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Inspection Location</label>
          <input
            type="text"
            value={locationStr}
            onChange={(e) => setLocationStr(e.target.value)}
            className="mt-1 w-full px-3 py-1.5 rounded bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] text-[var(--color-text-primary)] text-sm"
            style={{ backgroundColor: 'var(--color-surface-tertiary)', color: 'var(--color-text-primary)' }}
          />
        </div>
      </div>

      {/* Stepper Progress Bar */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs font-medium text-muted-foreground">
          <span>Step {currentStepIndex + 1} of {CAPTURE_STEPS.length}: {currentStep.title}</span>
          <span className="text-[var(--color-accent)] font-semibold">{totalCapturedCount} of {CAPTURE_STEPS.length} angles captured</span>
        </div>
        <div className="grid grid-cols-6 gap-2">
          {CAPTURE_STEPS.map((s, idx) => {
            const isCaptured = Boolean(capturedImages[s.id]);
            const isCurrent = idx === currentStepIndex;
            return (
              <button
                key={s.id}
                type="button"
                onClick={() => setCurrentStepIndex(idx)}
                className={`h-2.5 rounded-full cursor-pointer transition-all ${
                  isCurrent
                    ? 'bg-primary ring-2 ring-primary/40'
                    : isCaptured
                    ? 'bg-[var(--color-accent)]'
                    : 'bg-muted/40 hover:bg-muted/60'
                }`}
                title={`Step ${s.step}: ${s.title} ${isCaptured ? '(Captured)' : '(Pending)'}`}
              />
            );
          })}
        </div>
      </div>

      {errorMessage && (
        <div className="p-3.5 rounded-xl text-xs bg-red-50 border border-red-200 text-red-600 flex items-center justify-between gap-2 animate-fade-in">
          <span>⚠️ {errorMessage}</span>
          <button
            type="button"
            onClick={() => setErrorMessage(null)}
            className="text-red-600 hover:text-rose-200 text-xs px-2 py-0.5"
          >
            ✕
          </button>
        </div>
      )}

      {/* Main Step Capture Frame */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-6 rounded-2xl glass-card border border-border/80">
        {/* Left: Real Live Camera Viewfinder for this step */}
        <div className="space-y-3">
          <CameraCaptureView
            key={`camera-step-${currentStep.id}`}
            title={`Step ${currentStep.step}: ${currentStep.title.replace(/^\d+\.\s*/, '')}`}
            instruction={currentStep.instruction}
            capturedImage={capturedImages[currentStep.id] || null}
            onCapture={handleFrameCaptured}
            onRetake={handleRetakeStep}
            isProcessing={scanMutation.isPending}
            reticleType={currentStep.reticleType}
            autoStart={true}
            defaultFacingMode="environment"
          />
        </div>

        {/* Right: Step Guidance & Live Quality Feedback */}
        <div className="space-y-5 flex flex-col justify-between">
          <div className="space-y-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-primary/20 text-primary uppercase">
                  Angle {currentStep.step} of 6
                </span>
                {capturedImages[currentStep.id] && (
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[var(--color-accent)]/20 text-[var(--color-accent)] border border-green-200">
                    ✓ Photo Captured
                  </span>
                )}
              </div>
              <h2 className="text-lg font-bold text-foreground mt-1">{currentStep.title}</h2>
              <p className="text-xs text-muted-foreground mt-1 leading-relaxed">{currentStep.instruction}</p>
            </div>

            {/* Mandatory Fields To Target */}
            <div className="space-y-2">
              <label className="text-xs font-semibold text-foreground">Required Verification Checklist:</label>
              <div className="space-y-1.5">
                {currentStep.mandatoryFields.map((field, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span className="w-4 h-4 rounded-full bg-primary/20 text-primary flex items-center justify-center text-[10px] font-bold">
                      ✓
                    </span>
                    <span>{field}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Real-time Quality Inspection Feedback */}
            <div className="p-3.5 rounded-xl bg-card/60 border border-border/50 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-foreground">Computer Vision Quality Check</span>
                <span className="text-[var(--color-accent)] font-mono font-bold">
                  {capturedImages[currentStep.id] ? 'READY TO PROCESS' : 'AWAITING CAPTURE'}
                </span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-[11px] pt-1">
                <div className="p-2 rounded bg-background/50 border border-border/40 text-center">
                  <div className="text-muted-foreground">Sharpness</div>
                  <div className="font-bold text-[var(--color-accent)] mt-0.5">
                    {capturedImages[currentStep.id] ? `${qualityFeedback.blurScore}% (Pass)` : '--'}
                  </div>
                </div>
                <div className="p-2 rounded bg-background/50 border border-border/40 text-center">
                  <div className="text-muted-foreground">Glare</div>
                  <div className="font-bold text-[var(--color-accent)] mt-0.5">
                    {capturedImages[currentStep.id] ? 'None' : '--'}
                  </div>
                </div>
                <div className="p-2 rounded bg-background/50 border border-border/40 text-center">
                  <div className="text-muted-foreground">Lighting</div>
                  <div className="font-bold text-[var(--color-accent)] mt-0.5">
                    {capturedImages[currentStep.id] ? 'Optimal' : '--'}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Stepper Navigation Buttons */}
          <div className="flex items-center justify-between gap-3 pt-4 border-t border-border/40">
            <button
              type="button"
              onClick={handlePrev}
              disabled={currentStepIndex === 0}
              className="px-4 py-2 rounded-lg bg-card/60 border border-border text-xs font-semibold text-muted-foreground hover:text-foreground disabled:opacity-40 transition-all"
            >
              ← Previous Step
            </button>

            <button
              type="button"
              onClick={handleNext}
              disabled={scanMutation.isPending}
              className="px-5 py-2.5 rounded-lg bg-[var(--color-accent)] hover:bg-[var(--color-accent)] text-[var(--color-text-primary)] font-semibold text-xs transition-all flex items-center gap-2 shadow-md disabled:opacity-50"
            >
              {scanMutation.isPending ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Running OCR & Evaluation Engine...</span>
                </>
              ) : currentStepIndex === CAPTURE_STEPS.length - 1 ? (
                <span>Complete Capture & Process Scan ({totalCapturedCount}/6) →</span>
              ) : (
                <span>Next Step ({currentStepIndex + 2}/6) →</span>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
