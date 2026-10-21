import React from 'react';
import { useTelegram } from '../context/TelegramContext';
import { CheckCircle2, Clock, Lock, Play, PenTool, Check } from 'lucide-react';

export default function MilestonesTimeline({ milestones = [], currency = 'USD', onOpenSignature }) {
  const { haptic } = useTelegram();

  // Sort milestones by order_index
  const sortedMilestones = [...milestones].sort((a, b) => (a.order_index || 0) - (b.order_index || 0));

  const handleSignClick = (milestone) => {
    haptic('medium');
    onOpenSignature(milestone);
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'APPROVED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/70 dark:text-emerald-300 border border-emerald-300 dark:border-emerald-800">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
            Затверджено та підписано
          </span>
        );
      case 'WAITING_APPROVAL':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-900 dark:bg-amber-950/70 dark:text-amber-300 border border-amber-300 dark:border-amber-700 animate-pulse">
            <span className="w-2 h-2 rounded-full bg-amber-500 animate-ping" />
            Очікує вашого затвердження
          </span>
        );
      case 'IN_PROGRESS':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 dark:bg-blue-950/70 dark:text-blue-300 border border-blue-300 dark:border-blue-800">
            <Play className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400 fill-current" />
            В роботі у розробника
          </span>
        );
      case 'LOCKED':
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400 border border-zinc-200 dark:border-zinc-700">
            <Lock className="w-3 h-3 text-zinc-400" />
            Черга робіт
          </span>
        );
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
          Етапи реалізації
        </h3>
        <span className="text-xs font-medium text-zinc-400">
          Всього: {sortedMilestones.length}
        </span>
      </div>

      <div className="space-y-3">
        {sortedMilestones.map((m) => {
          const isWaiting = m.status === 'WAITING_APPROVAL';
          const isApproved = m.status === 'APPROVED';
          const isLocked = m.status === 'LOCKED';

          return (
            <div
              key={m.id}
              className={`rounded-2xl p-4 transition-all duration-200 border ${
                isWaiting
                  ? 'bg-amber-50/50 dark:bg-amber-950/20 border-amber-300 dark:border-amber-800/80 shadow-md shadow-amber-500/5 ring-1 ring-amber-400/30'
                  : isApproved
                  ? 'bg-white dark:bg-zinc-900 border-zinc-200/80 dark:border-zinc-800'
                  : isLocked
                  ? 'bg-zinc-50/80 dark:bg-zinc-900/40 border-zinc-200/50 dark:border-zinc-800/50 opacity-75'
                  : 'bg-white dark:bg-zinc-900 border-indigo-200 dark:border-indigo-900/60 shadow-sm'
              }`}
            >
              {/* Card Header: Order and Price */}
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span
                    className={`w-6 h-6 rounded-lg text-xs font-bold flex items-center justify-center ${
                      isApproved
                        ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                        : isWaiting
                        ? 'bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-300'
                        : isLocked
                        ? 'bg-zinc-200 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400'
                        : 'bg-indigo-100 text-indigo-800 dark:bg-indigo-950 dark:text-indigo-300'
                    }`}
                  >
                    {m.order_index}
                  </span>
                  <h4 className="text-sm font-bold text-zinc-900 dark:text-white break-words">
                    {m.title}
                  </h4>
                </div>

                <div className="text-right flex-shrink-0">
                  <span className="text-sm font-bold text-zinc-900 dark:text-white">
                    ${Number(m.amount).toLocaleString()}
                  </span>
                  <span className="text-[11px] font-medium text-zinc-400 ml-1">
                    {currency}
                  </span>
                </div>
              </div>

              {/* Description */}
              {m.description && (
                <p className="text-xs text-zinc-600 dark:text-zinc-400 mt-2 leading-relaxed break-words">
                  {m.description}
                </p>
              )}

              {/* Status Badge */}
              <div className="mt-3 flex items-center justify-between flex-wrap gap-2">
                <div>{getStatusBadge(m.status)}</div>

                {/* Signature Preview if approved */}
                {isApproved && m.signature_data && (
                  <div className="flex items-center gap-1.5 py-0.5 px-2 rounded-lg bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700">
                    <img
                      src={m.signature_data}
                      alt="Signature"
                      className="h-5 w-auto max-w-[80px] object-contain invert-0 dark:invert"
                    />
                    <span className="text-[10px] font-medium text-zinc-500 dark:text-zinc-400">
                      Підписано
                    </span>
                  </div>
                )}
              </div>

              {/* Approve Action Button for WAITING_APPROVAL */}
              {isWaiting && (
                <div className="mt-4 pt-3 border-t border-amber-200/80 dark:border-amber-900/60">
                  <button
                    type="button"
                    onClick={() => handleSignClick(m)}
                    className="w-full min-h-[46px] flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-white text-xs font-bold shadow-md shadow-amber-500/20 active:scale-[0.99] transition-all"
                  >
                    <PenTool className="w-4 h-4" />
                    <span>✍️ Затвердити та підписати етап</span>
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
