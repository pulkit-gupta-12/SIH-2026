import React, { useEffect, useRef, useState } from 'react';
import { useCamera, type CapturedFrame, type FacingMode } from './useCamera';

interface CameraCaptureViewProps {
  title?: string;
  instruction?: string;
  capturedImage?: string | null;
  onCapture: (frame: CapturedFrame) => void;
  onRetake?: () => void;
  isProcessing?: boolean;
  reticleType?: 'general' | 'pdp' | 'declarations' | 'mrp' | 'barcode' | 'seal';
  autoStart?: boolean;
  defaultFacingMode?: FacingMode;
  onBarcodeDetected?: (barcode: string) => void;
  className?: string;
}

type BarcodeDetectorLike = {
  detect: (source: HTMLVideoElement) => Promise<Array<{ rawValue?: string }>>;
};

type BarcodeDetectorConstructor = new (options?: { formats?: string[] }) => BarcodeDetectorLike;

export default function CameraCaptureView({
  title,
  instruction,
  capturedImage,
  onCapture,
  onRetake,
  isProcessing = false,
  reticleType = 'general',
  autoStart = true,
  defaultFacingMode = 'environment',
  onBarcodeDetected,
  className = '',
}: CameraCaptureViewProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [isCapturing, setIsCapturing] = useState(false);

  const {
    videoRef,
    canvasRef,
    cameraStatus,
    facingMode,
    errorMessage,
    hasMultipleCameras,
    isSecureContext,
    startCamera,
    toggleFacingMode,
    captureFrame,
    processUploadedFile,
  } = useCamera({ autoStart, defaultFacingMode });

  useEffect(() => {
    if (reticleType !== 'barcode' || !onBarcodeDetected || cameraStatus !== 'active') return;

    const detectorConstructor = (window as Window & { BarcodeDetector?: BarcodeDetectorConstructor }).BarcodeDetector;
    if (!detectorConstructor) return;

    const detector = new detectorConstructor({ formats: ['ean_13', 'ean_8', 'upc_a', 'upc_e', 'code_128', 'qr_code'] });
    let stopped = false;
    let timer: number | undefined;

    const scan = async () => {
      if (stopped || !videoRef.current) return;
      try {
        const detections = await detector.detect(videoRef.current);
        const barcode = detections.find((item) => item.rawValue?.trim())?.rawValue?.trim();
        if (barcode) {
          onBarcodeDetected(barcode);
          stopped = true;
          return;
        }
      } catch {
        // The browser may reject frames while the camera is changing state.
      }
      if (!stopped) timer = window.setTimeout(scan, 250);
    };

    timer = window.setTimeout(scan, 250);
    return () => {
      stopped = true;
      if (timer) window.clearTimeout(timer);
    };
  }, [cameraStatus, onBarcodeDetected, reticleType, videoRef]);

  // Handle capture button click
  const handleCaptureClick = async () => {
    if (isCapturing || cameraStatus !== 'active') return;
    setIsCapturing(true);
    try {
      const frame = await captureFrame();
      if (frame) {
        onCapture(frame);
      }
    } catch (err) {
      console.error('Failed to capture frame from video:', err);
    } finally {
      setIsCapturing(false);
    }
  };

  // Handle secondary gallery fallback selection
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const frame = await processUploadedFile(file);
      onCapture(frame);
    } catch (err) {
      console.error('Failed to process selected file:', err);
    } finally {
      // Reset input value so same file can be chosen again if needed
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleRetake = () => {
    if (onRetake) {
      onRetake();
    }
    // Ensure camera is active
    if (cameraStatus !== 'active' && cameraStatus !== 'initializing') {
      startCamera(facingMode);
    }
  };

  // Determine reticle appearance based on active inspection type
  const renderReticle = () => {
    if (reticleType === 'barcode') {
      return (
        <div className="absolute inset-8 md:inset-12 border-2 border-emerald-400/80 rounded-lg pointer-events-none flex flex-col justify-between p-3 bg-[var(--color-accent)]/5 shadow-[0_0_20px_rgba(16,185,129,0.2)]">
          <div className="flex justify-between text-[11px] font-mono text-[var(--color-accent)] font-bold tracking-wider">
            <span>[BARCODE SCANNER]</span>
            <span>GS1 ALIGN</span>
          </div>
          {/* Laser scanning beam line */}
          <div className="w-full h-0.5 bg-gradient-to-r from-transparent via-emerald-400 to-transparent shadow-[0_0_8px_#34d399] animate-pulse" />
          <div className="flex justify-between text-[10px] font-mono text-[var(--color-accent)]/80">
            <span>FIT 1D/2D CODE IN BOX</span>
            <span>AUTO-FOCUS</span>
          </div>
        </div>
      );
    }

    if (reticleType === 'mrp') {
      return (
        <div className="absolute inset-6 md:inset-10 border-2 border-dashed border-amber-400/80 rounded-xl pointer-events-none flex flex-col justify-between p-3 bg-amber-500/5">
          <div className="flex justify-between text-[11px] font-mono text-amber-600 font-bold">
            <span>[MRP & NET QTY TARGET]</span>
            <span>OCR MACRO</span>
          </div>
          <div className="flex justify-between text-[10px] font-mono text-amber-600/80">
            <span>RULE 5 & 6 COMPLIANCE</span>
            <span>FONT-SIZE CHECK</span>
          </div>
        </div>
      );
    }

    return (
      <div className="absolute inset-4 md:inset-6 border-2 border-dashed border-emerald-400/60 rounded-xl pointer-events-none flex flex-col justify-between p-3 bg-[var(--color-accent)]/5">
        <div className="flex justify-between text-[11px] font-mono text-[var(--color-accent)]">
          <span className="font-semibold">{title ? `[TARGET: ${title.toUpperCase()}]` : '[CAMERA VIEWFINDER]'}</span>
          <span>HIGH-RES CAPTURE</span>
        </div>

        {/* Viewfinder corner brackets */}
        <div className="flex justify-center items-center opacity-40">
          <div className="w-12 h-12 border-t border-l border-white/50" />
          <div className="w-8 h-8 rounded-full border border-white/30 flex items-center justify-center">
            <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full" />
          </div>
          <div className="w-12 h-12 border-b border-r border-white/50" />
        </div>

        <div className="flex justify-between text-[10px] font-mono text-[var(--color-accent)]/80">
          <span>LEGAL METROLOGY CV</span>
          <span>{instruction || 'Align label clearly'}</span>
        </div>
      </div>
    );
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Hidden File Input for fallback */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        className="hidden"
        aria-hidden="true"
      />

      {/* Hidden Canvas for Frame Capture */}
      <canvas ref={canvasRef} className="hidden" aria-hidden="true" />

      {/* Main Viewfinder Frame */}
      <div className="relative aspect-4/3 md:aspect-16/10 rounded-2xl overflow-hidden bg-[var(--color-surface-primary)] border border-[var(--color-border)]/80 shadow-lg flex items-center justify-center">
        {/* State A: Captured Image Preview */}
        {capturedImage ? (
          <div className="relative w-full h-full bg-[var(--color-surface-tertiary)] flex items-center justify-center">
            <img
              src={capturedImage}
              alt="Captured Frame Preview"
              className="w-full h-full object-contain"
            />
            {/* Captured Badge Overlay */}
            <div className="absolute top-3 left-3 px-3 py-1 rounded-full text-xs font-semibold bg-[var(--color-accent)]/90 text-[var(--color-text-primary)] shadow-lg backdrop-blur-md flex items-center gap-1.5 border border-emerald-400/40">
              <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
              <span>Snapshot Captured</span>
            </div>

            {/* Retake Button on preview */}
            <button
              type="button"
              onClick={handleRetake}
              className="absolute top-3 right-3 px-3 py-1.5 rounded-xl text-xs font-semibold bg-[var(--color-surface-tertiary)] hover:bg-[var(--color-surface-tertiary)] text-[var(--color-text-primary)] border border-[var(--color-border)]/80 shadow-lg backdrop-blur-md transition-all flex items-center gap-1.5"
            >
              <span>🔄 Retake</span>
            </button>
          </div>
        ) : cameraStatus === 'active' || cameraStatus === 'initializing' ? (
          /* State B: Live Active Video Stream */
          <div className="relative w-full h-full bg-[var(--color-surface-tertiary)]">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover"
            />

            {/* Live Camera Indicators & Controls */}
            <div className="absolute top-3 left-3 flex items-center gap-2">
              <div className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-[var(--color-surface-tertiary)]/60 backdrop-blur-md text-[var(--color-accent)] border border-green-200 flex items-center gap-1.5 shadow-md">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                <span>{facingMode === 'environment' ? '● REAR CAMERA' : '● FRONT CAMERA'}</span>
              </div>
            </div>

            {hasMultipleCameras && (
              <button
                type="button"
                onClick={toggleFacingMode}
                title="Flip Camera"
                className="absolute top-3 right-3 p-2 rounded-full bg-[var(--color-surface-tertiary)]/60 hover:bg-[var(--color-surface-tertiary)]/80 text-[var(--color-text-primary)] border border-[var(--color-border)] backdrop-blur-md transition-all shadow-md"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>
            )}

            {/* Viewfinder Reticle */}
            {renderReticle()}
          </div>
        ) : cameraStatus === 'denied' || cameraStatus === 'unsupported' || cameraStatus === 'error' ? (
          /* State C: Permission Denied or Error State */
          <div className="p-6 text-center space-y-4 max-w-md animate-fade-in">
            <div className="w-14 h-14 mx-auto rounded-2xl bg-amber-50 text-amber-600 border border-amber-200 flex items-center justify-center text-2xl">
              {cameraStatus === 'denied' ? '🔒' : '⚠️'}
            </div>

            <div className="space-y-1.5">
              <h3 className="text-base font-bold text-[var(--color-text-primary)]">
                {cameraStatus === 'denied'
                  ? 'Camera Permission Required'
                  : cameraStatus === 'unsupported' && !isSecureContext
                  ? 'HTTPS Required for Camera'
                  : 'Camera Feed Unavailable'}
              </h3>
              <p className="text-xs text-[var(--color-text-secondary)] leading-relaxed">
                {errorMessage ||
                  'Camera access was blocked or is unavailable in this environment. You can retry with permission or choose an image directly from your gallery.'}
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-2.5 justify-center pt-2">
              <button
                type="button"
                onClick={() => startCamera(facingMode)}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-[var(--color-accent)] hover:bg-[var(--color-accent)] text-[var(--color-text-primary)] shadow-md transition-all flex items-center justify-center gap-1.5"
              >
                <span>🔄</span>
                <span>Try Camera Again</span>
              </button>

              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-[var(--color-surface-tertiary)] hover:bg-gray-100 text-[var(--color-text-primary)] border border-[var(--color-border)] transition-all flex items-center justify-center gap-1.5"
              >
                <span>📁</span>
                <span>Select from Gallery</span>
              </button>
            </div>
          </div>
        ) : (
          /* State D: Initializing / Starting */
          <div className="text-center p-6 space-y-3">
            <div className="w-8 h-8 border-3 border-green-200 border-t-emerald-400 rounded-full animate-spin mx-auto" />
            <p className="text-xs font-medium text-[var(--color-text-muted)]">Starting camera preview...</p>
          </div>
        )}
      </div>

      {/* Action Controls Bar */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        {!capturedImage ? (
          <>
            {/* Primary Live Capture Button */}
            <button
              type="button"
              disabled={cameraStatus !== 'active' || isCapturing || isProcessing}
              onClick={handleCaptureClick}
              className="flex-1 w-full py-3.5 px-5 rounded-xl font-bold text-[var(--color-text-primary)] bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 active:scale-[0.99] shadow-lg shadow-sm disabled:opacity-40 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2.5 text-sm"
            >
              {isCapturing ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Capturing Frame...</span>
                </>
              ) : (
                <>
                  <span className="text-lg">📸</span>
                  <span>{title ? `Capture ${title}` : 'Capture Photo from Camera'}</span>
                </>
              )}
            </button>

            {/* Secondary Option: Choose from Gallery / Files */}
            <button
              type="button"
              disabled={isProcessing}
              onClick={() => fileInputRef.current?.click()}
              className="w-full sm:w-auto py-3 px-4 rounded-xl text-xs font-semibold bg-[var(--color-surface-tertiary)]/90 hover:bg-gray-100 text-[var(--color-text-secondary)] border border-[var(--color-border)]/80 transition-all flex items-center justify-center gap-2 shrink-0"
              title="Upload photo from disk or gallery"
            >
              <span>📁</span>
              <span>Upload File</span>
            </button>
          </>
        ) : (
          /* When captured: Option to Retake or Select different file */
          <div className="w-full flex items-center justify-between gap-3">
            <button
              type="button"
              onClick={handleRetake}
              className="py-2.5 px-4 rounded-xl text-xs font-semibold bg-[var(--color-surface-tertiary)] hover:bg-gray-100 text-[var(--color-text-primary)] border border-[var(--color-border)] transition-all flex items-center gap-1.5"
            >
              <span>🔄 Retake Camera Photo</span>
            </button>

            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="py-2.5 px-4 rounded-xl text-xs font-semibold bg-[var(--color-surface-tertiary)] hover:bg-[var(--color-surface-tertiary)] text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] border border-[var(--color-border)] transition-all flex items-center gap-1.5"
            >
              <span>📁 Pick Different File</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
