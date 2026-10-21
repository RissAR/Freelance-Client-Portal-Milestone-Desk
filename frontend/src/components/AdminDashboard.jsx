import React, { useState } from 'react';
import { useTelegram } from '../context/TelegramContext';
import {
  ShieldAlert,
  FolderKanban,
  CheckCircle2,
  Clock,
  Play,
  Lock,
  RotateCw,
  AlertCircle,
  ExternalLink,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

export default function AdminDashboard({
  projects = [],
  isLoading,
  onRefresh,
  onUpdateMilestoneStatus,
  onUpdateTicketStatus,
}) {
  const { haptic, openLink } = useTelegram();
  const [selectedProjectId, setSelectedProjectId] = useState(null);

  // Default to first project if none selected
  const activeProject =
    projects.find((p) => p.id === selectedProjectId) || projects[0] || null;

  const handleMilestoneStatusChange = (milestoneId, newStatus) => {
    haptic('medium');
    onUpdateMilestoneStatus(milestoneId, newStatus);
  };

  const handleTicketResolve = (ticketId) => {
    haptic('success');
    onUpdateTicketStatus(ticketId, 'RESOLVED');
  };

  const handleTicketReview = (ticketId) => {
    haptic('medium');
    onUpdateTicketStatus(ticketId, 'IN_REVIEW');
  };

  return (
    <div className="space-y-4">
      {/* Admin Header */}
      <div className="bg-gradient-to-r from-zinc-900 to-indigo-950 text-white rounded-2xl p-4 sm:p-5 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-indigo-500/30 flex items-center justify-center text-indigo-300">
              <ShieldAlert className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold tracking-wide">Панель розробника</h2>
              <p className="text-[11px] text-zinc-400">Керування проектами та статусами</p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => {
              haptic('light');
              onRefresh();
            }}
            disabled={isLoading}
            className="min-h-[38px] px-3 py-1.5 rounded-xl bg-white/10 hover:bg-white/20 text-xs font-semibold flex items-center gap-1.5 transition-colors"
          >
            <RotateCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Оновити</span>
          </button>
        </div>

        {/* Project Selector if more than 1 */}
        {projects.length > 1 && (
          <div className="pt-2">
            <label className="text-[11px] text-zinc-400 font-medium block mb-1">
              Оберіть проект:
            </label>
            <select
              value={activeProject?.id || ''}
              onChange={(e) => {
                haptic('selection');
                setSelectedProjectId(parseInt(e.target.value, 10));
              }}
              className="w-full min-h-[44px] px-3 py-2 rounded-xl bg-zinc-800 text-white text-xs border border-zinc-700 focus:outline-none"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  #{p.id} {p.title} ({p.status})
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {!activeProject ? (
        <div className="bg-white dark:bg-zinc-900 rounded-2xl p-8 text-center border border-zinc-200 dark:border-zinc-800 text-zinc-400 text-xs">
          <FolderKanban className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p>Немає створених проектів у базі</p>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Active Project Details Card */}
          <div className="bg-white dark:bg-zinc-900 rounded-2xl p-4 border border-zinc-200/80 dark:border-zinc-800 space-y-2 text-xs">
            <div className="flex justify-between items-start">
              <div>
                <span className="text-[11px] font-semibold text-indigo-600 dark:text-indigo-400">
                  ID: #{activeProject.id} | Клієнт ID: {activeProject.client_id}
                </span>
                <h3 className="text-base font-bold text-zinc-900 dark:text-white break-words mt-0.5">
                  {activeProject.title}
                </h3>
              </div>
              <span className="px-2 py-0.5 rounded-md text-[11px] font-bold bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300">
                {activeProject.status}
              </span>
            </div>
            <div className="flex justify-between text-zinc-500 pt-1 border-t border-zinc-100 dark:border-zinc-800">
              <span>Бюджет: <strong>${activeProject.budget} {activeProject.currency}</strong></span>
              <span>Прогрес: <strong>{activeProject.progress_percentage}%</strong></span>
            </div>
          </div>

          {/* Milestones Management */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
              Управління етапами робіт
            </h4>

            <div className="space-y-2">
              {(activeProject.milestones || []).map((m) => (
                <div
                  key={m.id}
                  className="bg-white dark:bg-zinc-900 rounded-2xl p-3.5 border border-zinc-200/80 dark:border-zinc-800 space-y-3"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="text-[11px] font-bold text-zinc-500">
                        Етап #{m.order_index}
                      </span>
                      <h5 className="text-xs font-bold text-zinc-900 dark:text-white break-words">
                        {m.title}
                      </h5>
                    </div>
                    <span className="text-xs font-bold text-zinc-900 dark:text-white">
                      ${m.amount}
                    </span>
                  </div>

                  {/* Status pills selector */}
                  <div className="pt-1">
                    <label className="text-[10px] font-semibold text-zinc-400 block mb-1.5">
                      Поточний статус: <span className="text-zinc-700 dark:text-zinc-300 font-bold">{m.status}</span>
                    </label>
                    <div className="grid grid-cols-2 gap-1.5 sm:grid-cols-4">
                      <button
                        type="button"
                        onClick={() => handleMilestoneStatusChange(m.id, 'LOCKED')}
                        className={`min-h-[38px] px-2 py-1.5 rounded-lg text-[11px] font-semibold border transition-all ${
                          m.status === 'LOCKED'
                            ? 'bg-zinc-200 dark:bg-zinc-700 text-zinc-900 dark:text-white border-zinc-400'
                            : 'border-zinc-200 dark:border-zinc-800 text-zinc-500 hover:bg-zinc-50 dark:hover:bg-zinc-800'
                        }`}
                      >
                        🔒 LOCKED
                      </button>

                      <button
                        type="button"
                        onClick={() => handleMilestoneStatusChange(m.id, 'IN_PROGRESS')}
                        className={`min-h-[38px] px-2 py-1.5 rounded-lg text-[11px] font-semibold border transition-all ${
                          m.status === 'IN_PROGRESS'
                            ? 'bg-blue-100 dark:bg-blue-900/60 text-blue-800 dark:text-blue-300 border-blue-400'
                            : 'border-zinc-200 dark:border-zinc-800 text-zinc-500 hover:bg-zinc-50 dark:hover:bg-zinc-800'
                        }`}
                      >
                        ▶️ IN_PROGRESS
                      </button>

                      <button
                        type="button"
                        onClick={() => handleMilestoneStatusChange(m.id, 'WAITING_APPROVAL')}
                        className={`min-h-[38px] px-2 py-1.5 rounded-lg text-[11px] font-semibold border transition-all ${
                          m.status === 'WAITING_APPROVAL'
                            ? 'bg-amber-100 dark:bg-amber-900/60 text-amber-800 dark:text-amber-300 border-amber-400'
                            : 'border-zinc-200 dark:border-zinc-800 text-zinc-500 hover:bg-zinc-50 dark:hover:bg-zinc-800'
                        }`}
                      >
                        ⏳ WAITING
                      </button>

                      <button
                        type="button"
                        onClick={() => handleMilestoneStatusChange(m.id, 'APPROVED')}
                        className={`min-h-[38px] px-2 py-1.5 rounded-lg text-[11px] font-semibold border transition-all ${
                          m.status === 'APPROVED'
                            ? 'bg-emerald-100 dark:bg-emerald-900/60 text-emerald-800 dark:text-emerald-300 border-emerald-400'
                            : 'border-zinc-200 dark:border-zinc-800 text-zinc-500 hover:bg-zinc-50 dark:hover:bg-zinc-800'
                        }`}
                      >
                        ✅ APPROVED
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Tickets Management */}
          <div className="space-y-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
              Всі тікети клієнта ({activeProject.tickets?.length || 0})
            </h4>

            {(!activeProject.tickets || activeProject.tickets.length === 0) ? (
              <p className="text-xs text-zinc-400 italic bg-white dark:bg-zinc-900 p-4 rounded-xl text-center border border-zinc-200 dark:border-zinc-800">
                Тікетів за цим проектом немає
              </p>
            ) : (
              <div className="space-y-2">
                {activeProject.tickets.map((t) => (
                  <div
                    key={t.id}
                    className="bg-white dark:bg-zinc-900 rounded-2xl p-3.5 border border-zinc-200/80 dark:border-zinc-800 space-y-2 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        <span className="font-bold text-zinc-900 dark:text-white">#{t.id}</span>
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300">
                          {t.type}
                        </span>
                        <span
                          className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                            t.status === 'RESOLVED'
                              ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                              : t.status === 'IN_REVIEW'
                              ? 'bg-indigo-100 text-indigo-800 dark:bg-indigo-950 dark:text-indigo-300'
                              : 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
                          }`}
                        >
                          {t.status}
                        </span>
                      </div>
                    </div>

                    <p className="text-zinc-700 dark:text-zinc-300 break-words">
                      {t.message}
                    </p>

                    {/* Quick status actions */}
                    {t.status !== 'RESOLVED' && (
                      <div className="flex gap-2 pt-1 border-t border-zinc-100 dark:border-zinc-800">
                        {t.status !== 'IN_REVIEW' && (
                          <button
                            type="button"
                            onClick={() => handleTicketReview(t.id)}
                            className="min-h-[38px] px-3 py-1 rounded-lg bg-indigo-50 hover:bg-indigo-100 dark:bg-indigo-950 dark:hover:bg-indigo-900 text-indigo-600 dark:text-indigo-400 text-xs font-semibold transition-colors"
                          >
                            Взяти в роботу
                          </button>
                        )}
                        <button
                          type="button"
                          onClick={() => handleTicketResolve(t.id)}
                          className="min-h-[38px] px-3 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-sm transition-colors flex items-center gap-1"
                        >
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Позначити як Вирішено</span>
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
