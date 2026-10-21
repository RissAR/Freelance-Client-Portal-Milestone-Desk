import React, { useState } from 'react';
import { useTelegram } from '../context/TelegramContext';
import {
  FolderKanban,
  Check,
  RotateCcw,
} from 'lucide-react';

export default function AdminDashboard({
  projects = [],
  isLoading,
  onRefresh,
  onUpdateMilestoneStatus,
  onUpdateTicketStatus,
}) {
  const { haptic } = useTelegram();
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
      {/* Project Selector if multiple */}
      {projects.length > 1 && (
        <div className="bg-white dark:bg-zinc-900 rounded-2xl p-3 border border-zinc-200/80 dark:border-zinc-800">
          <label className="text-[11px] text-zinc-400 font-medium block mb-1">
            Активний проект:
          </label>
          <select
            value={activeProject?.id || ''}
            onChange={(e) => {
              haptic('selection');
              setSelectedProjectId(parseInt(e.target.value, 10));
            }}
            className="w-full min-h-[44px] px-3 py-2 rounded-xl bg-zinc-50 dark:bg-zinc-800 text-zinc-900 dark:text-white text-xs border border-zinc-200 dark:border-zinc-700 focus:outline-none"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                #{p.id} {p.title} ({p.status})
              </option>
            ))}
          </select>
        </div>
      )}

      {!activeProject ? (
        <div className="bg-white dark:bg-zinc-900 rounded-2xl p-8 text-center border border-zinc-200/80 dark:border-zinc-800 text-zinc-400 text-xs">
          <FolderKanban className="w-8 h-8 mx-auto mb-2 opacity-40 text-zinc-400" />
          <p>Немає створених проектів у базі даних</p>
        </div>
      ) : (
        <div className="space-y-4">
          {/* Active Project Card */}
          <div className="bg-white dark:bg-zinc-900 rounded-2xl p-4 border border-zinc-200/80 dark:border-zinc-800 space-y-2 text-xs">
            <div className="flex justify-between items-start gap-2">
              <div className="flex-1">
                <span className="text-[11px] font-medium text-zinc-400">
                  Проект #{activeProject.id} • Клієнт ID: {activeProject.client_id}
                </span>
                <h3 className="text-sm font-bold text-zinc-900 dark:text-white break-words mt-0.5">
                  {activeProject.title}
                </h3>
              </div>
              <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300">
                {activeProject.status}
              </span>
            </div>
            <div className="flex justify-between text-zinc-500 pt-2 border-t border-zinc-100 dark:border-zinc-800">
              <span>Бюджет: <strong className="text-zinc-800 dark:text-zinc-200">${activeProject.budget} {activeProject.currency}</strong></span>
              <span>Прогрес: <strong className="text-zinc-800 dark:text-zinc-200">{activeProject.progress_percentage}%</strong></span>
            </div>
          </div>

          {/* Milestones Management */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 dark:text-zinc-500">
              Керування етапами
            </h4>

            <div className="space-y-2">
              {(activeProject.milestones || []).map((m) => (
                <div
                  key={m.id}
                  className="bg-white dark:bg-zinc-900 rounded-2xl p-3.5 border border-zinc-200/80 dark:border-zinc-800 space-y-2.5"
                >
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <span className="text-[11px] font-semibold text-zinc-400">
                        Етап #{m.order_index}
                      </span>
                      <h5 className="text-xs font-semibold text-zinc-900 dark:text-white break-words">
                        {m.title}
                      </h5>
                    </div>
                    <span className="text-xs font-bold text-zinc-900 dark:text-white">
                      ${m.amount}
                    </span>
                  </div>

                  {/* Status buttons without emojis */}
                  <div className="pt-1">
                    <div className="grid grid-cols-2 gap-1.5 sm:grid-cols-4">
                      <button
                        type="button"
                        onClick={() => handleMilestoneStatusChange(m.id, 'LOCKED')}
                        className={`min-h-[36px] px-2 py-1.5 rounded-xl text-[11px] font-semibold border transition-all ${
                          m.status === 'LOCKED'
                            ? 'bg-zinc-900 text-white dark:bg-zinc-100 dark:text-zinc-900 border-zinc-900 dark:border-zinc-100'
                            : 'border-zinc-200 dark:border-zinc-800 text-zinc-500 hover:bg-zinc-50 dark:hover:bg-zinc-800'
                        }`}
                      >
                        Черга
                      </button>

                      <button
                        type="button"
                        onClick={() => handleMilestoneStatusChange(m.id, 'IN_PROGRESS')}
                        className={`min-h-[36px] px-2 py-1.5 rounded-xl text-[11px] font-semibold border transition-all ${
                          m.status === 'IN_PROGRESS'
                            ? 'bg-blue-600 text-white border-blue-600'
                            : 'border-zinc-200 dark:border-zinc-800 text-zinc-500 hover:bg-zinc-50 dark:hover:bg-zinc-800'
                        }`}
                      >
                        В роботі
                      </button>

                      <button
                        type="button"
                        onClick={() => handleMilestoneStatusChange(m.id, 'WAITING_APPROVAL')}
                        className={`min-h-[36px] px-2 py-1.5 rounded-xl text-[11px] font-semibold border transition-all ${
                          m.status === 'WAITING_APPROVAL'
                            ? 'bg-amber-600 text-white border-amber-600'
                            : 'border-zinc-200 dark:border-zinc-800 text-zinc-500 hover:bg-zinc-50 dark:hover:bg-zinc-800'
                        }`}
                      >
                        Очікує
                      </button>

                      <button
                        type="button"
                        onClick={() => handleMilestoneStatusChange(m.id, 'APPROVED')}
                        className={`min-h-[36px] px-2 py-1.5 rounded-xl text-[11px] font-semibold border transition-all ${
                          m.status === 'APPROVED'
                            ? 'bg-emerald-600 text-white border-emerald-600'
                            : 'border-zinc-200 dark:border-zinc-800 text-zinc-500 hover:bg-zinc-50 dark:hover:bg-zinc-800'
                        }`}
                      >
                        Затверджено
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Tickets Management */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 dark:text-zinc-500">
              Тікети клієнта ({activeProject.tickets?.length || 0})
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
                              ? 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300'
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
                            className="min-h-[38px] px-3 py-1 rounded-xl bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-800 dark:text-zinc-200 text-xs font-semibold transition-colors"
                          >
                            Взяти в роботу
                          </button>
                        )}
                        <button
                          type="button"
                          onClick={() => handleTicketResolve(t.id)}
                          className="min-h-[38px] px-3 py-1 rounded-xl bg-zinc-900 hover:bg-black dark:bg-zinc-100 dark:hover:bg-white text-white dark:text-zinc-900 text-xs font-semibold shadow-sm transition-colors flex items-center gap-1"
                        >
                          <Check className="w-3.5 h-3.5" />
                          <span>Позначити як вирішено</span>
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
