import React from 'react';
import { useTelegram } from '../context/TelegramContext';
import { Check, Clock, Lock, Play, PenLine } from 'lucide-react';

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
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400 border border-emerald-200/60 dark:border-emerald-800/50">
            <Check className="w-3.5 h-3.5" />
            <span>Затверджено</span>
          </span>
        );
      case 'WAITING_APPROVAL':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-400 border border-amber-200/60 dark:border-amber-800/50">
            <Clock className="w-3.5 h-3.5" />
            <span>Очікує затвердження</span>
          </span>
        );
      case 'IN_PROGRESS':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-400 border border-blue-200/60 dark:border-blue-800/50">
            <Play className="w-3 h-3 fill-current" />
            <span>В роботі</span>
          </span>
        );
      case 'LOCKED':
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400 border border-zinc-200/60 dark:border-zinc-700/60">
            <Lock className="w-3 h-3" />
            <span>Черга</span>
          </span>
        );
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 dark:text-zinc-500">
          Етапи реалізації
        </h3>
        <span className="text-xs font-medium text-zinc-400">
          {sortedMilestones.length}
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
                  ? 'bg-white dark:bg-zinc-900 border-amber-300 dark:border-amber-800/80 shadow-sm ring-1 ring-amber-400/20'
                  : isApproved
                  ? 'bg-white dark:bg-zinc-900 border-zinc-200/60 dark:border-zinc-800/80'
                  : isLocked
                  ? 'bg-zinc-50/60 dark:bg-zinc-900/40 border-zinc-200/40 dark:border-zinc-800/40 opacity-70'
                  : 'bg-white dark:bg-zinc-900 border-zinc-200/80 dark:border-zinc-800 shadow-sm'
              }`}
            >
              {/* Order index, Title, and Price */}
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-2.5 flex-1">
                  <span
                    className={`w-6 h-6 rounded-lg text-xs font-semibold flex items-center justify-center flex-shrink-0 mt-0.5 ${
                      isApproved
                        ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                        : isWaiting
                        ? 'bg-amber-100 text-amber-900 dark:bg-amber-950 dark:text-amber-300'
                        : isLocked
                        ? 'bg-zinc-200 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400'
                        : 'bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900'
                    }`}
                  >
                    {m.order_index}
                  </span>
                  <div className="flex-1">
                    <h4 className="text-sm font-semibold text-zinc-900 dark:text-white break-words">
                      {m.title}
                    </h4>
                    {m.description && (
                      <p className="text-xs text-zinc-500 dark:text-zinc-400 mt-1 leading-relaxed break-words">
                        {m.description}
                      </p>
                    )}
                  </div>
                </div>

                <div className="text-right flex-shrink-0">
                  <span className="text-sm font-bold text-zinc-900 dark:text-white">
                    ${Number(m.amount).toLocaleString()}
                  </span>
                  <span className="text-[11px] text-zinc-400 ml-1">
                    {currency}
                  </span>
                </div>
              </div>

              {/* Status & Signature Preview */}
              <div className="mt-3.5 pt-2.5 border-t border-zinc-100 dark:border-zinc-800/60 flex items-center justify-between flex-wrap gap-2">
                <div>{getStatusBadge(m.status)}</div>

                {isApproved && m.signature_data && (
                  <div className="flex items-center gap-1.5 py-0.5 px-2 rounded-lg bg-zinc-100 dark:bg-zinc-800 border border-zinc-200/60 dark:border-zinc-700/60">
                    <img
                      src={m.signature_data}
                      alt="Signature"
                      className="h-4 w-auto max-w-[70px] object-contain invert-0 dark:invert"
                    />
                    <span className="text-[10px] font-medium text-zinc-400">
                      Підпис клієнта
                    </span>
                  </div>
                )}
              </div>

              {/* Apple-style Action Button for WAITING_APPROVAL */}
              {isWaiting && (
                <div className="mt-3 pt-3 border-t border-amber-100 dark:border-amber-950/60">
                  <button
                    type="button"
                    onClick={() => handleSignClick(m)}
                    className="w-full min-h-[44px] flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-zinc-900 hover:bg-black dark:bg-zinc-100 dark:hover:bg-white text-white dark:text-zinc-900 text-xs font-semibold shadow-sm active:scale-[0.99] transition-all"
                  >
                    <PenLine className="w-4 h-4" />
                    <span>Підписати етап</span>
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
