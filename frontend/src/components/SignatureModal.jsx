import React, { useRef, useState, useEffect, useCallback } from 'react';
import { useTelegram } from '../context/TelegramContext';
import { X, RotateCcw, Check, PenTool, Loader2 } from 'lucide-react';

export default function SignatureModal({ isOpen, onClose, milestone, onConfirm, isSubmitting }) {
  const { haptic } = useTelegram();
  const canvasRef = useRef(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [hasDrawn, setHasDrawn] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  // Initialize and resize canvas
  useEffect(() => {
    if (!isOpen) {
      setHasDrawn(false);
      setIsDrawing(false);
      setErrorMsg('');
      return;
    }

    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();

    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    ctx.strokeStyle = '#18181b'; // zinc-900 or dark tone
    ctx.lineWidth = 2.5;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
  }, [isOpen]);

  const getPos = useCallback((e) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };
    const rect = canvas.getBoundingClientRect();
    const clientX = e.touches && e.touches[0] ? e.touches[0].clientX : e.clientX;
    const clientY = e.touches && e.touches[0] ? e.touches[0].clientY : e.clientY;
    return {
      x: clientX - rect.left,
      y: clientY - rect.top,
    };
  }, []);

  const startDrawing = useCallback(
    (e) => {
      e.preventDefault();
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      const pos = getPos(e);
      ctx.beginPath();
      ctx.moveTo(pos.x, pos.y);
      setIsDrawing(true);
      setHasDrawn(true);
      setErrorMsg('');
      haptic('light');
    },
    [getPos, haptic]
  );

  const draw = useCallback(
    (e) => {
      e.preventDefault();
      if (!isDrawing) return;
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      const pos = getPos(e);
      ctx.lineTo(pos.x, pos.y);
      ctx.stroke();
    },
    [isDrawing, getPos]
  );

  const stopDrawing = useCallback(
    (e) => {
      if (!isDrawing) return;
      if (e) e.preventDefault();
      setIsDrawing(false);
    },
    [isDrawing]
  );

  const handleClear = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    setHasDrawn(false);
    setErrorMsg('');
    haptic('light');
  }, [haptic]);

  const handleSubmit = useCallback(async () => {
    if (!hasDrawn) {
      setErrorMsg('Будь ласка, поставте свій підпис перед підтвердженням');
      haptic('error');
      return;
    }

    const canvas = canvasRef.current;
    if (!canvas) return;

    try {
      const signatureData = canvas.toDataURL('image/png');
      haptic('medium');
      await onConfirm(signatureData);
    } catch (err) {
      setErrorMsg(err.message || 'Помилка збереження підпису');
      haptic('error');
    }
  }, [hasDrawn, onConfirm, haptic]);

  if (!isOpen || !milestone) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 bg-black/50 backdrop-blur-sm transition-opacity">
      <div
        className="w-full max-w-md bg-white dark:bg-zinc-900 rounded-t-3xl sm:rounded-3xl shadow-xl border border-zinc-200/80 dark:border-zinc-800 p-5 space-y-4 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-zinc-100 dark:border-zinc-800">
          <div>
            <h3 className="text-sm font-bold text-zinc-900 dark:text-white leading-tight">
              Затвердження етапу
            </h3>
            <p className="text-xs text-zinc-500 dark:text-zinc-400">
              Цифровий підпис акту прийому
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            className="w-8 h-8 rounded-full flex items-center justify-center text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Milestone summary */}
        <div className="bg-zinc-50 dark:bg-zinc-800/50 rounded-xl p-3 border border-zinc-200/60 dark:border-zinc-800 text-xs space-y-1">
          <div className="flex justify-between font-semibold text-zinc-800 dark:text-zinc-200">
            <span>Етап #{milestone.order_index}: {milestone.title}</span>
            <span className="font-bold">${milestone.amount}</span>
          </div>
          <p className="text-zinc-500 dark:text-zinc-400 line-clamp-2">
            {milestone.description || 'Прийом виконаних робіт згідно з технічним описом.'}
          </p>
        </div>

        {/* Canvas Pad with Baseline */}
        <div className="space-y-2">
          <div className="flex justify-between items-center text-xs">
            <span className="font-medium text-zinc-700 dark:text-zinc-300">
              Поле для розпису:
            </span>
            <button
              type="button"
              onClick={handleClear}
              disabled={isSubmitting || !hasDrawn}
              className="inline-flex items-center gap-1 text-[11px] font-medium text-zinc-500 hover:text-zinc-900 dark:hover:text-zinc-200 transition-colors disabled:opacity-40"
            >
              <RotateCcw className="w-3 h-3" />
              Очистити
            </button>
          </div>

          <div className="relative border border-zinc-200 dark:border-zinc-700 rounded-2xl overflow-hidden bg-white dark:bg-zinc-950 h-44 sm:h-48 touch-none">
            <canvas
              ref={canvasRef}
              className="w-full h-full cursor-crosshair block relative z-10"
              onMouseDown={startDrawing}
              onMouseMove={draw}
              onMouseUp={stopDrawing}
              onMouseLeave={stopDrawing}
              onTouchStart={startDrawing}
              onTouchMove={draw}
              onTouchEnd={stopDrawing}
              onTouchCancel={stopDrawing}
            />
            {/* Minimalist dashed baseline */}
            <div className="absolute left-6 right-6 bottom-10 border-b border-dashed border-zinc-200 dark:border-zinc-800 pointer-events-none" />
            
            {!hasDrawn && (
              <div className="absolute inset-0 pointer-events-none flex flex-col items-center justify-center text-zinc-400 dark:text-zinc-600 text-xs z-0">
                <span>Розпишіться пальцем або стилусом</span>
              </div>
            )}
          </div>
        </div>

        {errorMsg && (
          <p className="text-xs text-rose-600 dark:text-rose-400 font-medium text-center">
            {errorMsg}
          </p>
        )}

        {/* Actions */}
        <div className="flex gap-2 pt-1">
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            className="flex-1 min-h-[44px] px-4 py-2.5 rounded-xl border border-zinc-200 dark:border-zinc-700 text-xs font-semibold text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors"
          >
            Скасувати
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={isSubmitting || !hasDrawn}
            className="flex-1 min-h-[44px] px-4 py-2.5 rounded-xl bg-zinc-900 hover:bg-black dark:bg-zinc-100 dark:hover:bg-white text-white dark:text-zinc-900 text-xs font-semibold shadow-sm transition-all disabled:opacity-40 flex items-center justify-center gap-1.5"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Збереження...</span>
              </>
            ) : (
              <>
                <Check className="w-4 h-4" />
                <span>Затвердити етап</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
