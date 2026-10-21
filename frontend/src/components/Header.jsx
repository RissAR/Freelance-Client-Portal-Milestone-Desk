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
    <header className="space-y-2.5">
      {/* Apple / Samsung Minimalist Top Bar */}
      <div className="flex items-center justify-between pb-2 border-b border-zinc-200/80 dark:border-zinc-800/80">
        <span className="text-sm font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">
          {isAdmin ? 'Панель розробника' : 'Панель клієнта'}
        </span>
        <button
          type="button"
          onClick={handleRefreshClick}
          disabled={isLoading}
          aria-label="Оновити"
          className="w-8 h-8 rounded-xl flex items-center justify-center text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors disabled:opacity-50"
        >
          <RotateCcw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Compact Project Overview Card (Client View) */}
      {project && !isAdmin && (
        <div className="bg-white dark:bg-zinc-900 rounded-2xl p-3.5 shadow-sm border border-zinc-200/80 dark:border-zinc-800 space-y-2.5">
          {/* Row 1: Title and Status badge */}
          <div className="flex items-center justify-between gap-2">
            <h2 className="text-sm sm:text-base font-bold text-zinc-900 dark:text-white truncate flex-1">
              {project.title}
            </h2>
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300 flex-shrink-0">
              В роботі
            </span>
          </div>

          {/* Row 2: Budget details and Quick micro-chips */}
          <div className="flex items-center justify-between gap-2 flex-wrap text-xs">
            <div className="flex items-center gap-1.5 text-zinc-500 dark:text-zinc-400 text-[11px]">
              <span>Бюджет: <strong className="text-zinc-900 dark:text-white font-semibold">${totalBudget.toLocaleString()}</strong></span>
              <span>•</span>
              <span>Затверджено: <strong className="text-emerald-600 dark:text-emerald-400 font-semibold">${approvedAmount.toLocaleString()}</strong> ({approvedCount}/{totalMilestones})</span>
            </div>

            {/* Quick Micro-Chips for Figma / Staging */}
            {(project.figma_url || project.staging_url) && (
              <div className="flex items-center gap-1.5">
                {project.figma_url && (
                  <button
                    type="button"
                    onClick={() => openLink(project.figma_url)}
                    className="h-7 inline-flex items-center gap-1 px-2.5 rounded-lg text-[11px] font-semibold bg-zinc-100 hover:bg-zinc-200/80 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-200 transition-colors"
                  >
                    <span>Figma</span>
                    <ExternalLink className="w-2.5 h-2.5 opacity-60" />
                  </button>
                )}
                {project.staging_url && (
                  <button
                    type="button"
                    onClick={() => openLink(project.staging_url)}
                    className="h-7 inline-flex items-center gap-1 px-2.5 rounded-lg text-[11px] font-semibold bg-zinc-100 hover:bg-zinc-200/80 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-200 transition-colors"
                  >
                    <span>Стенд</span>
                    <ExternalLink className="w-2.5 h-2.5 opacity-60" />
                  </button>
                )}
              </div>
            )}
          </div>

          {/* Row 3: Thin Elegant Progress Bar */}
          <div className="flex items-center gap-2 pt-0.5">
            <div className="flex-1 h-1.5 bg-zinc-100 dark:bg-zinc-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-zinc-900 dark:bg-zinc-100 rounded-full transition-all duration-500 ease-out"
                style={{ width: `${Math.min(Math.max(progress, 0), 100)}%` }}
              />
            </div>
            <span className="text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 w-8 text-right">
              {progress}%
            </span>
          </div>
        </div>
      )}
    </header>
  );
}
