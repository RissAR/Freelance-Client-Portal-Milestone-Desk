import React, { useState } from 'react';
import { useTelegram } from '../context/TelegramContext';
import SegmentedTabs from './SegmentedTabs';
import {
  FolderKanban,
  Check,
  Clock,
  Play,
  FileCheck,
  ExternalLink,
  Calendar,
  Lock,
  Bug,
  Edit3,
  HelpCircle,
  AlertCircle,
} from 'lucide-react';

export default function AdminDashboard({
  projects = [],
  isLoading,
  onRefresh,
  onUpdateMilestoneStatus,
  onUpdateTicketStatus,
  onViewAct,
}) {
  const { haptic, openLink } = useTelegram();
  const [selectedProjectId, setSelectedProjectId] = useState(null);
  const [adminTab, setAdminTab] = useState('milestones'); // 'milestones' | 'tickets'

  // Default to first project if none selected
  const activeProject =
    projects.find((p) => p.id === selectedProjectId) || projects[0] || null;

  const milestones = activeProject?.milestones || [];
  const tickets = activeProject?.tickets || [];
  const openTicketsCount = tickets.filter(
    (t) => t.status === 'OPEN' || t.status === 'IN_REVIEW'
  ).length;

  const adminTabs = [
    {
      id: 'milestones',
      label: 'Керування етапами',
      count: milestones.length,
    },
    {
      id: 'tickets',
      label: 'Тікети та правки',
      count: tickets.length,
      hasBadge: openTicketsCount > 0,
    },
  ];

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

  const formatDueDate = (dateStr) => {
    if (!dateStr) return null;
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString('uk-UA', { day: 'numeric', month: 'long' });
    } catch {
      return dateStr;
    }
  };

  const getTypeBadge = (type) => {
    switch (type) {
      case 'BUG':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-400 border border-rose-200/60 dark:border-rose-900">
            <Bug className="w-3 h-3" />
            <span>Баг</span>
          </span>
        );
      case 'QUESTION':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-sky-50 text-sky-700 dark:bg-sky-950/60 dark:text-sky-400 border border-sky-200/60 dark:border-sky-900">
            <HelpCircle className="w-3 h-3" />
            <span>Запитання</span>
          </span>
        );
      case 'REVISION':
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-400 border border-amber-200/60 dark:border-amber-900">
            <Edit3 className="w-3 h-3" />
            <span>Правка</span>
          </span>
        );
    }
  };

  const getTicketStatusBadge = (status) => {
    switch (status) {
      case 'RESOLVED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400">
            <Check className="w-3 h-3" />
            <span>Вирішено</span>
          </span>
        );
      case 'IN_REVIEW':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-400">
            <Clock className="w-3 h-3" />
            <span>В роботі</span>
          </span>
        );
      case 'OPEN':
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
            <AlertCircle className="w-3 h-3" />
            <span>Відкрито</span>
          </span>
        );
    }
  };

  const getMilestoneStatusBadge = (status) => {
    switch (status) {
      case 'APPROVED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400 border border-emerald-200/60 dark:border-emerald-800/50">
            <Check className="w-3 h-3" />
            <span>Затверджено</span>
          </span>
        );
      case 'WAITING_APPROVAL':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-400 border border-amber-200/60 dark:border-amber-800/50">
            <Clock className="w-3 h-3" />
            <span>Очікує підпису</span>
          </span>
        );
      case 'IN_PROGRESS':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-blue-50 text-blue-700 dark:bg-blue-950/60 dark:text-blue-400 border border-blue-200/60 dark:border-blue-800/50">
            <Play className="w-2.5 h-2.5 fill-current" />
            <span>В роботі</span>
          </span>
        );
      case 'LOCKED':
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400 border border-zinc-200/60 dark:border-zinc-700/60">
            <Lock className="w-2.5 h-2.5" />
            <span>Черга</span>
          </span>
        );
    }
  };

  const sortedMilestones = [...milestones].sort(
    (a, b) => (a.order_index || 0) - (b.order_index || 0)
  );

  return (
    <div className="space-y-3.5">
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
        <div className="space-y-3.5">
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
            <div className="flex justify-between text-zinc-500 pt-2 border-t border-zinc-100 dark:border-zinc-800 text-[11px]">
              <span>
                Бюджет:{' '}
                <strong className="text-zinc-800 dark:text-zinc-200">
                  ${Number(activeProject.budget || 0).toLocaleString()} {activeProject.currency || 'USD'}
                </strong>
              </span>
              <span>
                Прогрес:{' '}
                <strong className="text-zinc-800 dark:text-zinc-200">
                  {activeProject.progress_percentage}%
                </strong>
              </span>
            </div>
          </div>

          {/* Segmented Tabs for Admin */}
          <SegmentedTabs
            tabs={adminTabs}
            activeTab={adminTab}
            onChange={setAdminTab}
          />

          {/* Tab 1: Milestones Management with Linear Action Control */}
          {adminTab === 'milestones' && (
            <div className="space-y-2.5">
              {sortedMilestones.length === 0 ? (
                <div className="bg-white dark:bg-zinc-900 rounded-2xl p-6 text-center border border-zinc-200/80 dark:border-zinc-800 text-zinc-400 text-xs">
                  <p>Немає етапів у цьому проекті</p>
                </div>
              ) : (
                sortedMilestones.map((m) => {
                  const dueDateText = formatDueDate(m.due_date);

                  return (
                    <div
                      key={m.id}
                      className="bg-white dark:bg-zinc-900 rounded-2xl p-4 border border-zinc-200/80 dark:border-zinc-800 space-y-3 shadow-sm"
                    >
                      {/* Top row: Title, status, and price */}
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <span className="text-xs font-bold text-zinc-900 dark:text-white">
                              Етап #{m.order_index}
                            </span>
                            {getMilestoneStatusBadge(m.status)}
                          </div>
                          <h4 className="text-xs font-semibold text-zinc-800 dark:text-zinc-200 break-words mt-1">
                            {m.title}
                          </h4>
                          {m.description && (
                            <p className="text-[11px] text-zinc-500 dark:text-zinc-400 mt-0.5 leading-relaxed break-words">
                              {m.description}
                            </p>
                          )}
                          {dueDateText && (
                            <div className="flex items-center gap-1 text-[11px] text-zinc-400 mt-1">
                              <Calendar className="w-3 h-3 opacity-70" />
                              <span>Термін: до {dueDateText}</span>
                            </div>
                          )}
                        </div>

                        <div className="text-right flex-shrink-0">
                          <span className="text-xs font-bold text-zinc-900 dark:text-white">
                            ${Number(m.amount).toLocaleString()}
                          </span>
                        </div>
                      </div>

                      {/* Linear Contextual Action Button */}
                      <div className="pt-1 border-t border-zinc-100 dark:border-zinc-800/80">
                        {m.status === 'LOCKED' && (
                          <button
                            type="button"
                            onClick={() => handleMilestoneStatusChange(m.id, 'IN_PROGRESS')}
                            className="w-full min-h-[42px] flex items-center justify-center gap-2 px-3 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-sm transition-colors"
                          >
                            <Play className="w-3.5 h-3.5 fill-current" />
                            <span>Розпочати етап</span>
                          </button>
                        )}

                        {m.status === 'IN_PROGRESS' && (
                          <button
                            type="button"
                            onClick={() => handleMilestoneStatusChange(m.id, 'WAITING_APPROVAL')}
                            className="w-full min-h-[42px] flex items-center justify-center gap-2 px-3 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold shadow-sm transition-colors"
                          >
                            <Clock className="w-3.5 h-3.5" />
                            <span>Передати на затвердження</span>
                          </button>
                        )}

                        {m.status === 'WAITING_APPROVAL' && (
                          <div className="w-full min-h-[42px] flex items-center justify-center gap-2 px-3 py-2 rounded-xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-900 text-amber-700 dark:text-amber-300 text-xs font-medium">
                            <Clock className="w-3.5 h-3.5" />
                            <span>Очікує підпису клієнта</span>
                          </div>
                        )}

                        {m.status === 'APPROVED' && (
                          <button
                            type="button"
                            onClick={() => onViewAct && onViewAct(m)}
                            className="w-full min-h-[42px] flex items-center justify-center gap-2 px-3 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-sm transition-colors"
                          >
                            <FileCheck className="w-4 h-4" />
                            <span>Переглянути акт</span>
                          </button>
                        )}

                        {/* Discreet Manual Override Selector */}
                        <div className="flex items-center justify-between pt-2 text-[11px] text-zinc-400">
                          <span>Ручна зміна статусу:</span>
                          <select
                            value={m.status}
                            onChange={(e) => handleMilestoneStatusChange(m.id, e.target.value)}
                            aria-label="Примусово змінити статус етапу"
                            className="text-[11px] bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 border border-zinc-200 dark:border-zinc-700 rounded-lg px-2 py-1 focus:outline-none"
                          >
                            <option value="LOCKED">Черга</option>
                            <option value="IN_PROGRESS">В роботі</option>
                            <option value="WAITING_APPROVAL">Очікує</option>
                            <option value="APPROVED">Затверджено</option>
                          </select>
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          )}

          {/* Tab 2: Tickets Management */}
          {adminTab === 'tickets' && (
            <div className="space-y-2.5">
              {tickets.length === 0 ? (
                <div className="bg-white dark:bg-zinc-900 rounded-2xl p-6 text-center border border-zinc-200/80 dark:border-zinc-800 text-zinc-400 text-xs">
                  <p>Немає створених тікетів за цим проектом</p>
                </div>
              ) : (
                tickets.map((t) => {
                  const linkedMilestone = t.milestone_id
                    ? milestones.find((m) => m.id === t.milestone_id)
                    : null;

                  return (
                    <div
                      key={t.id}
                      className="bg-white dark:bg-zinc-900 rounded-2xl p-4 border border-zinc-200/80 dark:border-zinc-800 space-y-2.5 text-xs shadow-sm"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span className="font-bold text-zinc-900 dark:text-white">
                            #{t.id}
                          </span>
                          {getTypeBadge(t.type)}
                          {getTicketStatusBadge(t.status)}
                          {linkedMilestone && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-semibold bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 border border-zinc-200/60 dark:border-zinc-700/60">
                              Етап #{linkedMilestone.order_index}
                            </span>
                          )}
                        </div>
                      </div>

                      <p className="text-zinc-800 dark:text-zinc-200 leading-relaxed break-words">
                        {t.message}
                      </p>

                      {t.attachment_url && (
                        <div>
                          <button
                            type="button"
                            onClick={() => openLink(t.attachment_url)}
                            className="inline-flex items-center gap-1 text-[11px] font-medium text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-white min-h-[32px]"
                          >
                            <span>Переглянути вкладення</span>
                            <ExternalLink className="w-3 h-3 opacity-60" />
                          </button>
                        </div>
                      )}

                      {/* Quick status actions */}
                      {t.status !== 'RESOLVED' && (
                        <div className="flex gap-2 pt-2 border-t border-zinc-100 dark:border-zinc-800">
                          {t.status !== 'IN_REVIEW' && (
                            <button
                              type="button"
                              onClick={() => handleTicketReview(t.id)}
                              className="min-h-[38px] px-3 py-1 rounded-xl bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-800 dark:text-zinc-200 text-xs font-semibold transition-colors flex-1"
                            >
                              Взяти в роботу
                            </button>
                          )}
                          <button
                            type="button"
                            onClick={() => handleTicketResolve(t.id)}
                            className="min-h-[38px] px-3 py-1 rounded-xl bg-zinc-900 hover:bg-black dark:bg-zinc-100 dark:hover:bg-white text-white dark:text-zinc-900 text-xs font-semibold shadow-sm transition-colors flex items-center justify-center gap-1.5 flex-1"
                          >
                            <Check className="w-3.5 h-3.5" />
                            <span>Позначити як вирішено</span>
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
