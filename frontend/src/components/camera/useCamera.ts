import { useState, useRef, useEffect, useCallback } from 'react';

export type CameraStatus = 'idle' | 'initializing' | 'active' | 'denied' | 'unsupported' | 'error';
export type FacingMode = 'environment' | 'user';

export interface CapturedFrame {
  blob: Blob;
  dataUrl: string;
  objectUrl: string;
  width: number;
  height: number;
}

export interface UseCameraOptions {
  autoStart?: boolean;
  defaultFacingMode?: FacingMode;
}

export function useCamera(options: UseCameraOptions = {}) {
  const { autoStart = true, defaultFacingMode = 'environment' } = options;

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const [cameraStatus, setCameraStatus] = useState<CameraStatus>('idle');
  const [facingMode, setFacingMode] = useState<FacingMode>(defaultFacingMode);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [hasMultipleCameras, setHasMultipleCameras] = useState<boolean>(false);
  const [isSecureContext, setIsSecureContext] = useState<boolean>(true);

  // Check secure context and device enumeration on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const secure = window.isSecureContext ?? (window.location.protocol === 'https:' || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');
      setIsSecureContext(secure);
    }
  }, []);

  // Stop active media stream tracks
  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => {
        try {
          track.stop();
        } catch {
          // ignore error during track stop
        }
      });
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setCameraStatus('idle');
  }, []);

  // Start camera stream
  const startCamera = useCallback(async (targetFacing: FacingMode = facingMode) => {
    // Check browser support
    if (typeof navigator === 'undefined' || !navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      const secure = typeof window !== 'undefined' ? window.isSecureContext : true;
      if (!secure) {
        setCameraStatus('unsupported');
        setErrorMessage(
          'Insecure Context: Camera access (getUserMedia) is blocked by the browser on non-HTTPS origins (e.g. http://<local-ip>). Use localhost or HTTPS.'
        );
      } else {
        setCameraStatus('unsupported');
        setErrorMessage('Camera API (getUserMedia) is not supported in this browser.');
      }
      return;
    }

    setCameraStatus('initializing');
    setErrorMessage(null);

    // Stop existing stream before starting a new one
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }

    try {
      // Primary constraint: requested facingMode (defaults to "environment" for rear camera)
      const primaryConstraints: MediaStreamConstraints = {
        audio: false,
        video: {
          facingMode: { ideal: targetFacing },
          width: { ideal: 1920, min: 640 },
          height: { ideal: 1080, min: 480 },
        },
      };

      let stream: MediaStream;
      try {
        stream = await navigator.mediaDevices.getUserMedia(primaryConstraints);
      } catch (err: any) {
        // Fallback constraint if high-res / ideal facing mode was overconstrained
        if (err.name === 'OverconstrainedError' || err.name === 'ConstraintNotSatisfiedError') {
          console.warn('[useCamera] Ideal constraints failed, falling back to simple facingMode:', targetFacing);
          stream = await navigator.mediaDevices.getUserMedia({
            audio: false,
            video: { facingMode: targetFacing },
          });
        } else {
          throw err;
        }
      }

      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        // On iOS Safari / mobile, play() must be explicitly awaited or handled
        try {
          await videoRef.current.play();
        } catch {
          // play() might require user gesture in some browsers, but video has playsInline & muted
        }
      }

      setFacingMode(targetFacing);
      setCameraStatus('active');

      // Check if device has multiple video cameras
      try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const videoInputs = devices.filter((d) => d.kind === 'videoinput');
        setHasMultipleCameras(videoInputs.length > 1);
      } catch {
        // Ignore enumerateDevices failure
      }
    } catch (err: any) {
      console.error('[useCamera] getUserMedia failed:', err);
      stopCamera();

      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setCameraStatus('denied');
        setErrorMessage('Camera access was denied. Please allow camera permissions in your browser or address bar settings to use live capture.');
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        setCameraStatus('error');
        setErrorMessage('No camera device detected on this hardware. You can use the gallery file upload option below.');
      } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
        setCameraStatus('error');
        setErrorMessage('Camera is currently busy or in use by another application. Please close other camera apps and try again.');
      } else {
        setCameraStatus('error');
        setErrorMessage(err.message || 'Unable to open camera feed. Please check your camera permissions.');
      }
    }
  }, [facingMode, stopCamera]);

  // Toggle between rear ('environment') and front ('user') camera
  const toggleFacingMode = useCallback(async () => {
    const nextMode: FacingMode = facingMode === 'environment' ? 'user' : 'environment';
    await startCamera(nextMode);
  }, [facingMode, startCamera]);

  // Capture frame from active video element to canvas and export Blob & DataURL
  const captureFrame = useCallback((): Promise<CapturedFrame | null> => {
    return new Promise((resolve) => {
      const video = videoRef.current;
      if (!video || cameraStatus !== 'active') {
        console.warn('[useCamera] Cannot capture frame: camera is not active or video ref missing');
        resolve(null);
        return;
      }

      const width = video.videoWidth || video.clientWidth || 1280;
      const height = video.videoHeight || video.clientHeight || 720;

      let canvas = canvasRef.current;
      if (!canvas) {
        canvas = document.createElement('canvas');
      }

      canvas.width = width;
      canvas.height = height;

      const ctx = canvas.getContext('2d');
      if (!ctx) {
        console.error('[useCamera] Failed to get 2D canvas rendering context');
        resolve(null);
        return;
      }

      // Draw current video frame to canvas
      ctx.drawImage(video, 0, 0, width, height);

      // Convert canvas to base64 Data URL
      const dataUrl = canvas.toDataURL('image/jpeg', 0.92);

      // Convert to Blob
      canvas.toBlob(
        (blob) => {
          if (!blob) {
            console.error('[useCamera] Canvas toBlob returned null');
            resolve(null);
            return;
          }
          const objectUrl = URL.createObjectURL(blob);
          resolve({
            blob,
            dataUrl,
            objectUrl,
            width,
            height,
          });
        },
        'image/jpeg',
        0.92
      );
    });
  }, [cameraStatus]);

  // Fallback file handler (for gallery/file picker selection)
  const processUploadedFile = useCallback((file: File): Promise<CapturedFrame> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        const dataUrl = reader.result as string;
        const objectUrl = URL.createObjectURL(file);
        const img = new Image();
        img.onload = () => {
          resolve({
            blob: file,
            dataUrl,
            objectUrl,
            width: img.naturalWidth || 800,
            height: img.naturalHeight || 600,
          });
        };
        img.onerror = () => {
          resolve({
            blob: file,
            dataUrl,
            objectUrl,
            width: 800,
            height: 600,
          });
        };
        img.src = dataUrl;
      };
      reader.onerror = (e) => reject(e);
      reader.readAsDataURL(file);
    });
  }, []);

  // Auto-start on mount if requested
  useEffect(() => {
    if (autoStart) {
      startCamera(defaultFacingMode);
    }
    return () => {
      // Cleanup all camera tracks when component unmounts
      stopCamera();
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    videoRef,
    canvasRef,
    cameraStatus,
    facingMode,
    errorMessage,
    hasMultipleCameras,
    isSecureContext,
    startCamera,
    stopCamera,
    toggleFacingMode,
    captureFrame,
    processUploadedFile,
  };
}
