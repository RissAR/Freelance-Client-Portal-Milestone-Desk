import React from 'react';
import { useTelegram } from '../context/TelegramContext';
import { ExternalLink, Layers, CheckCircle2, User, ShieldCheck } from 'lucide-react';

export default function Header({ project, activeRole, onRoleChange }) {
  const { openLink, haptic } = useTelegram();

  // Calculate statistics safely
  const milestones = project?.milestones || [];
  const totalMilestones = milestones.length;
  const approvedMilestones = milestones.filter((m) => m.status === 'APPROVED');
  const approvedCount = approvedMilestones.length;
  const approvedAmount = approvedMilestones.reduce((acc, m) => acc + (Number(m.amount) || 0), 0);
  const totalBudget = Number(project?.budget) || 0;
  const currency = project?.currency || 'USD';
  const progress = project?.progress_percentage ?? (totalMilestones > 0 ? Math.round((approvedCount / totalMilestones) * 100) : 0);

  const handleRoleToggle = (role) => {
    if (role !== activeRole) {
      haptic('selection');
      onRoleChange(role);
    }
  };

  return (
    <header className="space-y-4">
      {/* Top Bar: Role Switcher & Brand */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-xs font-semibold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
              Milestone Desk
            </h1>
            <p className="text-xs text-zinc-400 dark:text-zinc-500 font-medium">
              Freelance Portal
            </p>
          </div>
        </div>

        {/* Role Switcher Pill */}
        <div className="inline-flex p-1 bg-zinc-200/80 dark:bg-zinc-800/80 rounded-xl border border-zinc-300/60 dark:border-zinc-700/60 backdrop-blur-sm">
          <button
            type="button"
            onClick={() => handleRoleToggle('client')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 min-h-[36px] ${
              activeRole === 'client'
                ? 'bg-white dark:bg-zinc-900 text-indigo-600 dark:text-indigo-400 shadow-sm'
                : 'text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200'
            }`}
          >
            <User className="w-3.5 h-3.5" />
            <span>Клієнт</span>
          </button>
          <button
            type="button"
            onClick={() => handleRoleToggle('admin')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all duration-200 min-h-[36px] ${
              activeRole === 'admin'
                ? 'bg-white dark:bg-zinc-900 text-indigo-600 dark:text-indigo-400 shadow-sm'
                : 'text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Адмін</span>
          </button>
        </div>
      </div>

      {/* Project Overview Card (Only in client role or when project exists) */}
      {project && (
        <div className="bg-white dark:bg-zinc-900 rounded-2xl p-4 sm:p-5 shadow-sm border border-zinc-200/80 dark:border-zinc-800 space-y-4">
          {/* Project Title and Status */}
          <div className="flex items-start justify-between gap-3">
            <div className="space-y-1">
              <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] font-medium bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400 border border-emerald-200/60 dark:border-emerald-800/40">
                ● В роботі
              </span>
              <h2 className="text-lg sm:text-xl font-bold text-zinc-900 dark:text-white leading-tight break-words">
                {project.title}
              </h2>
            </div>
          </div>

          {/* Budget & Stats Grid */}
          <div className="grid grid-cols-2 gap-3 pt-1 border-t border-zinc-100 dark:border-zinc-800">
            <div>
              <p className="text-[11px] font-medium text-zinc-500 dark:text-zinc-400">
                Загальний бюджет
              </p>
              <p className="text-base sm:text-lg font-bold text-zinc-900 dark:text-white mt-0.5">
                ${totalBudget.toLocaleString()} <span className="text-xs font-semibold text-zinc-500">{currency}</span>
              </p>
            </div>
            <div>
              <p className="text-[11px] font-medium text-zinc-500 dark:text-zinc-400">
                Затверджено ({approvedCount}/{totalMilestones})
              </p>
              <p className="text-base sm:text-lg font-bold text-emerald-600 dark:text-emerald-400 mt-0.5 flex items-center gap-1">
                <span>${approvedAmount.toLocaleString()}</span>
                {approvedCount === totalMilestones && totalMilestones > 0 && (
                  <CheckCircle2 className="w-4 h-4 text-emerald-500 inline" />
                )}
              </p>
            </div>
          </div>

          {/* Animated Progress Bar */}
          <div className="space-y-1.5 pt-1">
            <div className="flex justify-between items-center text-xs font-semibold">
              <span className="text-zinc-600 dark:text-zinc-400">Прогрес проекту</span>
              <span className="text-indigo-600 dark:text-indigo-400 font-bold">{progress}%</span>
            </div>
            <div className="w-full h-2.5 bg-zinc-100 dark:bg-zinc-800 rounded-full overflow-hidden p-0.5">
              <div
                className="h-full bg-gradient-to-r from-indigo-500 to-emerald-500 rounded-full transition-all duration-700 ease-out"
                style={{ width: `${Math.min(Math.max(progress, 0), 100)}%` }}
              />
            </div>
          </div>

          {/* Quick Action Links: Figma & Staging */}
          {(project.figma_url || project.staging_url) && (
            <div className="flex flex-wrap gap-2 pt-2 border-t border-zinc-100 dark:border-zinc-800">
              {project.figma_url && (
                <button
                  type="button"
                  onClick={() => openLink(project.figma_url)}
                  className="flex-1 min-h-[44px] inline-flex items-center justify-center gap-2 px-3 py-2 text-xs font-semibold rounded-xl bg-zinc-100 hover:bg-zinc-200/80 dark:bg-zinc-800 dark:hover:bg-zinc-700/80 text-zinc-800 dark:text-zinc-200 transition-colors"
                >
                  <span>🎨 Figma</span>
                  <ExternalLink className="w-3.5 h-3.5 opacity-60" />
                </button>
              )}
              {project.staging_url && (
                <button
                  type="button"
                  onClick={() => openLink(project.staging_url)}
                  className="flex-1 min-h-[44px] inline-flex items-center justify-center gap-2 px-3 py-2 text-xs font-semibold rounded-xl bg-zinc-100 hover:bg-zinc-200/80 dark:bg-zinc-800 dark:hover:bg-zinc-700/80 text-zinc-800 dark:text-zinc-200 transition-colors"
                >
                  <span>🌐 Тестовий стенд</span>
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
