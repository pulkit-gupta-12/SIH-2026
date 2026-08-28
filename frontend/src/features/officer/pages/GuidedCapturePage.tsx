import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { submitOfficerGuidedScan, type ScanProcessingResult } from '../api';

interface StepConfig {
  step: number;
  id: string;
  title: string;
  instruction: string;
  mandatoryFields: string[];
  sampleImage: string;
}

const CAPTURE_STEPS: StepConfig[] = [
  {
    step: 1,
    id: 'front_panel',
    title: '1. Front Principal Display Panel (PDP)',
    instruction: 'Capture the full front surface of the retail package showing brand name, product name, and visual commodity representation.',
    mandatoryFields: ['Brand Name', 'Product Identity', 'Logo/Symbol'],
    sampleImage: 'https://images.unsplash.com/photo-1544787219-7f47ccb76574?w=600',
  },
  {
    step: 2,
    id: 'declaration_panel',
    title: '2. Mandatory Declaration Panel',
    instruction: 'Frame the complete regulatory text block containing manufacturing date, expiry/best-before, batch code, and customer care details.',
    mandatoryFields: ['Month/Year of Mfg', 'Batch No', 'Customer Care Email/Phone'],
    sampleImage: 'https://images.unsplash.com/photo-1527061011665-3652c757a4d4?w=600',
  },
  {
    step: 3,
    id: 'mrp_netqty_closeup',
    title: '3. MRP & Net Quantity Close-Up',
    instruction: 'Ensure sharp focus on the printed MRP statement (inclusive of all taxes) and the numeric net quantity with metric units.',
    mandatoryFields: ['MRP (incl. of all taxes)', 'Net Quantity (g/ml/kg)', 'Numeral Font Size'],
    sampleImage: 'https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=600',
  },
  {
    step: 4,
    id: 'manufacturer_block',
    title: '4. Manufacturer & Packer Address',
    instruction: 'Capture the full physical factory/registered office address of the manufacturer, packer, or importer (Rule 6(1)(a)).',
    mandatoryFields: ['Manufacturer Name', 'Complete Address with PIN', 'Country of Origin'],
    sampleImage: 'https://images.unsplash.com/photo-1589939705384-5185137a7f0f?w=600',
  },
  {
    step: 5,
    id: 'barcode_gtin',
    title: '5. Barcode & EAN/GTIN Scan',
    instruction: 'Scan or position the 1D/2D GS1 barcode clearly within the scanning frame without glare or label folding.',
    mandatoryFields: ['GTIN Barcode (13-digit)', 'GS1 Verification'],
    sampleImage: 'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=600',
  },
  {
    step: 6,
    id: 'wraparound_seal',
    title: '6. Package Wrap-Around & Seal',
    instruction: 'Inspect and capture the security seal, outer carton wrap-around, or container seam to verify tamper evidence.',
    mandatoryFields: ['Package Integrity', 'Outer Label Continuity'],
    sampleImage: 'https://images.unsplash.com/photo-1530587191325-3db32d826c18?w=600',
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
  const [capturedImages, setCapturedImages] = useState<{ [key: string]: string }>({
    front_panel: CAPTURE_STEPS[0].sampleImage,
    declaration_panel: CAPTURE_STEPS[1].sampleImage,
    mrp_netqty_closeup: CAPTURE_STEPS[2].sampleImage,
  });

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
  });

  const handleCaptureCurrentStep = () => {
    // Mock image capture from camera or sample
    setCapturedImages((prev) => ({
      ...prev,
      [currentStep.id]: currentStep.sampleImage,
    }));
    // Simulate real-time CV image quality check
    setQualityFeedback({
      blurScore: Math.floor(88 + Math.random() * 10),
      glareDetected: false,
      lightingPass: true,
    });
  };

  const handleNext = () => {
    if (currentStepIndex < CAPTURE_STEPS.length - 1) {
      setCurrentStepIndex((prev) => prev + 1);
    } else {
      // Submit scan pipeline
      const urls = Object.values(capturedImages);
      scanMutation.mutate({
        barcode,
        category,
        image_urls: urls.length > 0 ? urls : [currentStep.sampleImage],
        location: locationStr,
      });
    }
  };

  const handlePrev = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex((prev) => prev - 1);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border/40 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30 text-xs font-semibold">
              Lane 2 Guided Inspection
            </span>
            <span className="text-xs text-muted-foreground">Legal Metrology Packaged Commodities (PC) Rules</span>
          </div>
          <h1 className="text-2xl font-bold text-foreground mt-1">6-Step Guided Capture Wizard</h1>
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
            className="mt-1 w-full px-3 py-1.5 rounded bg-background/60 border border-border text-foreground font-mono text-sm"
          />
        </div>
        <div>
          <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Commodity Category</label>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="mt-1 w-full px-3 py-1.5 rounded bg-background/60 border border-border text-foreground text-sm"
          >
            <option value="food">Food & Edibles</option>
            <option value="medical_device">Medical Devices</option>
            <option value="electronics">Electronics & IT</option>
            <option value="import">Imported Commodities</option>
            <option value="general">General Packaged Goods</option>
          </select>
        </div>
        <div>
          <label className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">Inspection Location</label>
          <input
            type="text"
            value={locationStr}
            onChange={(e) => setLocationStr(e.target.value)}
            className="mt-1 w-full px-3 py-1.5 rounded bg-background/60 border border-border text-foreground text-sm"
          />
        </div>
      </div>

      {/* Stepper Progress Bar */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs font-medium text-muted-foreground">
          <span>Step {currentStepIndex + 1} of {CAPTURE_STEPS.length}: {currentStep.title}</span>
          <span>{Math.round(((currentStepIndex + 1) / CAPTURE_STEPS.length) * 100)}% Complete</span>
        </div>
        <div className="grid grid-cols-6 gap-2">
          {CAPTURE_STEPS.map((s, idx) => (
            <div
              key={s.id}
              onClick={() => setCurrentStepIndex(idx)}
              className={`h-2 rounded-full cursor-pointer transition-all ${
                idx === currentStepIndex
                  ? 'bg-primary ring-2 ring-primary/40'
                  : idx < currentStepIndex
                  ? 'bg-emerald-500'
                  : 'bg-muted/40'
              }`}
            />
          ))}
        </div>
      </div>

      {/* Main Step Capture Frame */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6 rounded-2xl glass-card border border-border/80">
        {/* Left: Live Viewfinder / Capture Preview */}
        <div className="space-y-4">
          <div className="relative aspect-4/3 rounded-xl overflow-hidden bg-black/40 border border-border/60 flex items-center justify-center group">
            {capturedImages[currentStep.id] ? (
              <img
                src={capturedImages[currentStep.id]}
                alt={currentStep.title}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="text-center p-6 space-y-2">
                <div className="text-4xl text-muted-foreground">📷</div>
                <p className="text-xs text-muted-foreground">Camera feed ready for Step {currentStep.step}</p>
              </div>
            )}

            {/* Viewfinder Reticle Overlay */}
            <div className="absolute inset-4 border-2 border-dashed border-primary/50 rounded-lg pointer-events-none flex flex-col justify-between p-2">
              <div className="flex justify-between text-[10px] font-mono text-primary/80">
                <span>[SCANNER ACTIVE]</span>
                <span>ISO AUTO</span>
              </div>
              <div className="flex justify-between text-[10px] font-mono text-primary/80">
                <span>OCR GRID ON</span>
                <span>F/1.8 1/120s</span>
              </div>
            </div>
          </div>

          {/* Capture Trigger Button */}
          <div className="flex items-center gap-3">
            <button
              onClick={handleCaptureCurrentStep}
              className="flex-1 py-2.5 rounded-xl bg-primary text-primary-foreground font-semibold text-sm hover:bg-primary/90 transition-all flex items-center justify-center gap-2 shadow-lg"
            >
              <span>📸</span>
              <span>Capture Step {currentStep.step} Image</span>
            </button>
          </div>
        </div>

        {/* Right: Step Guidance & Live Quality Feedback */}
        <div className="space-y-5 flex flex-col justify-between">
          <div className="space-y-4">
            <div>
              <h2 className="text-lg font-bold text-foreground">{currentStep.title}</h2>
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
                <span className="text-emerald-400 font-mono font-bold">READY TO PROCESS</span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-[11px] pt-1">
                <div className="p-2 rounded bg-background/50 border border-border/40 text-center">
                  <div className="text-muted-foreground">Sharpness</div>
                  <div className="font-bold text-emerald-400 mt-0.5">{qualityFeedback.blurScore}% (Pass)</div>
                </div>
                <div className="p-2 rounded bg-background/50 border border-border/40 text-center">
                  <div className="text-muted-foreground">Glare</div>
                  <div className="font-bold text-emerald-400 mt-0.5">None</div>
                </div>
                <div className="p-2 rounded bg-background/50 border border-border/40 text-center">
                  <div className="text-muted-foreground">Lighting</div>
                  <div className="font-bold text-emerald-400 mt-0.5">Optimal</div>
                </div>
              </div>
            </div>
          </div>

          {/* Stepper Navigation Buttons */}
          <div className="flex items-center justify-between gap-3 pt-4 border-t border-border/40">
            <button
              onClick={handlePrev}
              disabled={currentStepIndex === 0}
              className="px-4 py-2 rounded-lg bg-card/60 border border-border text-xs font-semibold text-muted-foreground hover:text-foreground disabled:opacity-40 transition-all"
            >
              ← Previous Step
            </button>

            <button
              onClick={handleNext}
              disabled={scanMutation.isPending}
              className="px-5 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs transition-all flex items-center gap-2 shadow-md"
            >
              {scanMutation.isPending ? (
                <span>Running OCR & Evaluation Engine...</span>
              ) : currentStepIndex === CAPTURE_STEPS.length - 1 ? (
                <span>Complete Capture & Process Scan →</span>
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
