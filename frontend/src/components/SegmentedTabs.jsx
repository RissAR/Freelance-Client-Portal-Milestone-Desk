import React from 'react';
import { useTelegram } from '../context/TelegramContext';

export default function SegmentedTabs({ tabs = [], activeTab, onChange }) {
  const { haptic } = useTelegram();

  const handleTabClick = (tabId) => {
    if (tabId !== activeTab) {
      haptic('selection');
      onChange(tabId);
    }
  };

  return (
    <div className="w-full bg-zinc-100 dark:bg-zinc-800/80 p-1 rounded-2xl flex gap-1 border border-zinc-200/60 dark:border-zinc-700/60">
      {tabs.map((tab) => {
        const isActive = tab.id === activeTab;
        return (
          <button
            key={tab.id}
            type="button"
            onClick={() => handleTabClick(tab.id)}
            className={`flex-1 min-h-[40px] flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-xl text-xs transition-all duration-200 ${
              isActive
                ? 'bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 shadow-sm font-semibold'
                : 'text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-200 font-medium'
            }`}
          >
            <span>{tab.label}</span>
            {tab.count !== undefined && (
              <span
                className={`px-1.5 py-0.2 rounded-full text-[10px] font-semibold ${
                  isActive
                    ? 'bg-zinc-100 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-200'
                    : 'bg-zinc-200/70 dark:bg-zinc-700/70 text-zinc-600 dark:text-zinc-400'
                }`}
              >
                {tab.count}
              </span>
            )}
            {tab.hasBadge && (
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
            )}
          </button>
        );
      })}
    </div>
  );
}
