import React from 'react';
import { X, Check, FileCheck, ShieldCheck } from 'lucide-react';

export default function SignedActModal({ isOpen, onClose, milestone, project }) {
  if (!isOpen || !milestone) return null;

  const formatDate = (dateStr) => {
    if (!dateStr) return new Date().toLocaleDateString('uk-UA', { day: 'numeric', month: 'long', year: 'numeric' });
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString('uk-UA', { day: 'numeric', month: 'long', year: 'numeric' });
    } catch {
      return dateStr;
    }
  };

  const currency = project?.currency || 'USD';
  const approvalDate = formatDate(milestone.updated_at || milestone.created_at);

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 bg-black/50 backdrop-blur-sm transition-opacity">
      <div
        className="w-full max-w-md bg-white dark:bg-zinc-900 rounded-t-3xl sm:rounded-3xl shadow-xl border border-zinc-200/80 dark:border-zinc-800 p-5 space-y-4 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-zinc-100 dark:border-zinc-800">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
              <FileCheck className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-zinc-900 dark:text-white leading-tight">
                Акт приймання етапу #{milestone.order_index}
              </h3>
              <p className="text-[11px] text-zinc-400">
                Офіційний цифровий документ
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="w-8 h-8 rounded-full flex items-center justify-center text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Details Card */}
        <div className="bg-zinc-50 dark:bg-zinc-800/50 rounded-2xl p-4 border border-zinc-200/60 dark:border-zinc-800 space-y-2.5 text-xs">
          <div className="flex justify-between items-start gap-2">
            <span className="text-zinc-500 dark:text-zinc-400">Проект:</span>
            <span className="font-semibold text-zinc-900 dark:text-white text-right break-words flex-1">
              {project?.title || 'Активний проект'}
            </span>
          </div>

          <div className="flex justify-between items-start gap-2 pt-1 border-t border-zinc-200/40 dark:border-zinc-700/40">
            <span className="text-zinc-500 dark:text-zinc-400">Найменування робіт:</span>
            <span className="font-semibold text-zinc-900 dark:text-white text-right break-words flex-1">
              {milestone.title}
            </span>
          </div>

          <div className="flex justify-between items-center pt-1 border-t border-zinc-200/40 dark:border-zinc-700/40">
            <span className="text-zinc-500 dark:text-zinc-400">Сума етапу:</span>
            <span className="text-sm font-bold text-zinc-900 dark:text-white">
              ${Number(milestone.amount).toLocaleString()} {currency}
            </span>
          </div>

          <div className="flex justify-between items-center pt-1 border-t border-zinc-200/40 dark:border-zinc-700/40">
            <span className="text-zinc-500 dark:text-zinc-400">Статус прийому:</span>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400">
              <Check className="w-3 h-3" />
              Затверджено та підписано
            </span>
          </div>

          <div className="flex justify-between items-center pt-1 border-t border-zinc-200/40 dark:border-zinc-700/40">
            <span className="text-zinc-500 dark:text-zinc-400">Дата підписання:</span>
            <span className="font-medium text-zinc-700 dark:text-zinc-300">
              {approvalDate}
            </span>
          </div>
        </div>

        {/* Signature Box */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="font-medium text-zinc-700 dark:text-zinc-300">
              Цифровий підпис замовника:
            </span>
            <span className="inline-flex items-center gap-1 text-[11px] text-zinc-400">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
              Верифіковано
            </span>
          </div>

          <div className="bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-4 flex flex-col items-center justify-center min-h-[120px]">
            {milestone.signature_data ? (
              <img
                src={milestone.signature_data}
                alt="Підпис клієнта"
                className="h-24 w-auto max-w-full object-contain invert-0 dark:invert"
              />
            ) : (
              <span className="text-xs text-zinc-400 italic">
                Підпис зафіксовано в системі
              </span>
            )}
            <p className="text-[10px] text-zinc-400 mt-2">
              Засвідчено через Canvas • Telegram Mini App ID #{milestone.id}
            </p>
          </div>
        </div>

        {/* Action Button */}
        <div className="pt-1">
          <button
            type="button"
            onClick={onClose}
            className="w-full min-h-[44px] px-4 py-2.5 rounded-xl bg-zinc-900 hover:bg-black dark:bg-zinc-100 dark:hover:bg-white text-white dark:text-zinc-900 text-xs font-semibold shadow-sm transition-colors"
          >
            Закрити
          </button>
        </div>
      </div>
    </div>
  );
}
