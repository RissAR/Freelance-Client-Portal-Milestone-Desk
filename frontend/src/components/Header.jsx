import React from 'react';
import { useTelegram } from '../context/TelegramContext';
import { ExternalLink, RotateCcw } from 'lucide-react';

export default function Header({ project, onRefresh, isLoading }) {
  const { openLink, isAdmin, haptic } = useTelegram();

  // Safe statistics calculations
  const milestones = project?.milestones || [];
  const totalMilestones = milestones.length;
  const approvedMilestones = milestones.filter((m) => m.status === 'APPROVED');
  const approvedCount = approvedMilestones.length;
  const approvedAmount = approvedMilestones.reduce((acc, m) => acc + (Number(m.amount) || 0), 0);
  const totalBudget = Number(project?.budget) || 0;
  const currency = project?.currency || 'USD';
  const progress = project?.progress_percentage ?? (totalMilestones > 0 ? Math.round((approvedCount / totalMilestones) * 100) : 0);

  const handleRefreshClick = () => {
    haptic('light');
    onRefresh();
  };

  return (
    <header className="space-y-3">
      {/* Apple / Samsung Minimalist Top Bar */}
      <div className="flex items-center justify-between pb-2.5 border-b border-zinc-200/80 dark:border-zinc-800/80">
        <span className="text-sm font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
          {isAdmin ? 'Панель розробника' : 'Панель клієнта'}
        </span>
        <button
          type="button"
          onClick={handleRefreshClick}
          disabled={isLoading}
          aria-label="Оновити"
          className="w-9 h-9 rounded-xl flex items-center justify-center text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors disabled:opacity-50"
        >
          <RotateCcw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Project Overview Card (Only for client or when project exists) */}
      {project && !isAdmin && (
        <div className="bg-white dark:bg-zinc-900 rounded-2xl p-4 sm:p-5 shadow-sm border border-zinc-200/80 dark:border-zinc-800 space-y-4">
          {/* Project Title and Status */}
          <div className="flex items-start justify-between gap-3">
            <div className="space-y-1.5 flex-1">
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-zinc-100 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300">
                В роботі
              </span>
              <h2 className="text-base sm:text-lg font-bold text-zinc-900 dark:text-white leading-tight break-words">
                {project.title}
              </h2>
            </div>
          </div>

          {/* Budget & Stats */}
          <div className="grid grid-cols-2 gap-3 pt-2 border-t border-zinc-100 dark:border-zinc-800/80">
            <div>
              <p className="text-[11px] font-medium text-zinc-500 dark:text-zinc-400">
                Загальний бюджет
              </p>
              <p className="text-sm sm:text-base font-bold text-zinc-900 dark:text-white mt-0.5">
                ${totalBudget.toLocaleString()} <span className="text-xs font-normal text-zinc-400">{currency}</span>
              </p>
            </div>
            <div>
              <p className="text-[11px] font-medium text-zinc-500 dark:text-zinc-400">
                Затверджено ({approvedCount}/{totalMilestones})
              </p>
              <p className="text-sm sm:text-base font-bold text-zinc-900 dark:text-white mt-0.5">
                ${approvedAmount.toLocaleString()} <span className="text-xs font-normal text-zinc-400">{currency}</span>
              </p>
            </div>
          </div>

          {/* iOS-Style Clean Progress Bar */}
          <div className="space-y-1.5 pt-1">
            <div className="flex justify-between items-center text-xs font-medium">
              <span className="text-zinc-500 dark:text-zinc-400">Прогрес проекту</span>
              <span className="text-zinc-900 dark:text-zinc-100 font-semibold">{progress}%</span>
            </div>
            <div className="w-full h-2 bg-zinc-100 dark:bg-zinc-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-zinc-900 dark:bg-zinc-100 rounded-full transition-all duration-500 ease-out"
                style={{ width: `${Math.min(Math.max(progress, 0), 100)}%` }}
              />
            </div>
          </div>

          {/* Quick Action Links: Figma & Staging (Zero Emojis) */}
          {(project.figma_url || project.staging_url) && (
            <div className="flex flex-wrap gap-2 pt-2 border-t border-zinc-100 dark:border-zinc-800/80">
              {project.figma_url && (
                <button
                  type="button"
                  onClick={() => openLink(project.figma_url)}
                  className="flex-1 min-h-[44px] inline-flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-xl bg-zinc-100 hover:bg-zinc-200/80 dark:bg-zinc-800 dark:hover:bg-zinc-700/80 text-zinc-800 dark:text-zinc-200 transition-colors"
                >
                  <span>Figma</span>
                  <ExternalLink className="w-3.5 h-3.5 opacity-60" />
                </button>
              )}
              {project.staging_url && (
                <button
                  type="button"
                  onClick={() => openLink(project.staging_url)}
                  className="flex-1 min-h-[44px] inline-flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-semibold rounded-xl bg-zinc-100 hover:bg-zinc-200/80 dark:bg-zinc-800 dark:hover:bg-zinc-700/80 text-zinc-800 dark:text-zinc-200 transition-colors"
                >
                  <span>Тестовий стенд</span>
                  <ExternalLink className="w-3.5 h-3.5 opacity-60" />
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </header>
  );
}
