import React, { useState } from 'react';
import { useTelegram } from '../context/TelegramContext';
import {
  MessageSquare,
  Plus,
  Bug,
  Edit3,
  HelpCircle,
  ExternalLink,
  CheckCircle2,
  Clock,
  AlertCircle,
  X,
  Loader2,
  Send,
} from 'lucide-react';

export default function TicketsSection({ tickets = [], milestones = [], onCreateTicket, isCreating }) {
  const { haptic, openLink } = useTelegram();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedMilestoneId, setSelectedMilestoneId] = useState('');
  const [ticketType, setTicketType] = useState('REVISION');
  const [message, setMessage] = useState('');
  const [attachmentUrl, setAttachmentUrl] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const handleOpenModal = () => {
    haptic('light');
    setIsModalOpen(true);
    setErrorMsg('');
  };

  const handleCloseModal = () => {
    if (isCreating) return;
    setIsModalOpen(false);
    setMessage('');
    setAttachmentUrl('');
    setSelectedMilestoneId('');
    setErrorMsg('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!message.trim()) {
      setErrorMsg('Будь ласка, вкажіть опис правки чи запитання');
      haptic('error');
      return;
    }

    try {
      haptic('medium');
      await onCreateTicket({
        milestoneId: selectedMilestoneId ? parseInt(selectedMilestoneId, 10) : null,
        type: ticketType,
        message: message.trim(),
        attachmentUrl: attachmentUrl.trim() || null,
      });
      handleCloseModal();
    } catch (err) {
      setErrorMsg(err.message || 'Не вдалося створити тікет');
      haptic('error');
    }
  };

  const getTypeBadge = (type) => {
    switch (type) {
      case 'BUG':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-semibold bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-400 border border-rose-200 dark:border-rose-900">
            <Bug className="w-3 h-3" />
            Баг
          </span>
        );
      case 'QUESTION':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-semibold bg-sky-50 text-sky-700 dark:bg-sky-950/60 dark:text-sky-400 border border-sky-200 dark:border-sky-900">
            <HelpCircle className="w-3 h-3" />
            Запитання
          </span>
        );
      case 'REVISION':
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-semibold bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-400 border border-amber-200 dark:border-amber-900">
            <Edit3 className="w-3 h-3" />
            Правка
          </span>
        );
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'RESOLVED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400">
            <CheckCircle2 className="w-3 h-3" />
            Вирішено
          </span>
        );
      case 'IN_REVIEW':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-indigo-50 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-400">
            <Clock className="w-3 h-3" />
            В обробці
          </span>
        );
      case 'OPEN':
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
            <AlertCircle className="w-3 h-3" />
            Відкрито
          </span>
        );
    }
  };

  // Helper map for milestone titles
  const milestoneMap = React.useMemo(() => {
    const map = {};
    milestones.forEach((m) => {
      map[m.id] = `Етап #${m.order_index}: ${m.title}`;
    });
    return map;
  }, [milestones]);

  return (
    <div className="space-y-3">
      {/* Header and Add button */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-bold uppercase tracking-wider text-zinc-500 dark:text-zinc-400">
            Правки та запитання
          </h3>
          <span className="text-xs px-2 py-0.5 rounded-full bg-zinc-200 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 font-semibold">
            {tickets.length}
          </span>
        </div>

        <button
          type="button"
          onClick={handleOpenModal}
          className="min-h-[44px] inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-50 hover:bg-indigo-100 dark:bg-indigo-950/60 dark:hover:bg-indigo-900/60 text-indigo-600 dark:text-indigo-400 text-xs font-semibold border border-indigo-200/60 dark:border-indigo-800/60 transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Створити тікет</span>
        </button>
      </div>

      {/* Tickets List */}
      {tickets.length === 0 ? (
        <div className="bg-white dark:bg-zinc-900 rounded-2xl p-6 text-center border border-zinc-200/80 dark:border-zinc-800 text-zinc-400 dark:text-zinc-500 text-xs">
          <MessageSquare className="w-8 h-8 mx-auto mb-2 opacity-40 text-zinc-400" />
          <p className="font-medium">Немає активних правок чи запитань</p>
          <p className="text-[11px] text-zinc-400 dark:text-zinc-600 mt-1">
            Натисніть кнопку вище, щоб додати зауваження до етапу робіт.
          </p>
        </div>
      ) : (
        <div className="space-y-2.5">
          {tickets.map((t) => (
            <div
              key={t.id}
              className="bg-white dark:bg-zinc-900 rounded-2xl p-4 border border-zinc-200/80 dark:border-zinc-800 shadow-sm space-y-2.5"
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-1.5 flex-wrap">
                  {getTypeBadge(t.type)}
                  {getStatusBadge(t.status)}
                </div>
                <span className="text-[10px] text-zinc-400">
                  #{t.id}
                </span>
              </div>

              {t.milestone_id && milestoneMap[t.milestone_id] && (
                <p className="text-[11px] font-medium text-zinc-500 dark:text-zinc-400 truncate">
                  📌 {milestoneMap[t.milestone_id]}
                </p>
              )}

              <p className="text-xs text-zinc-800 dark:text-zinc-200 leading-relaxed break-words">
                {t.message}
              </p>

              {t.attachment_url && (
                <div className="pt-1">
                  <button
                    type="button"
                    onClick={() => openLink(t.attachment_url)}
                    className="inline-flex items-center gap-1 text-[11px] font-semibold text-indigo-600 dark:text-indigo-400 hover:underline min-h-[36px]"
                  >
                    <span>📎 Вкладення / Посилання</span>
                    <ExternalLink className="w-3 h-3" />
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Create Ticket Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center p-0 sm:p-4 bg-black/60 backdrop-blur-sm">
          <div
            className="w-full max-w-md bg-white dark:bg-zinc-900 rounded-t-3xl sm:rounded-3xl shadow-2xl border border-zinc-200 dark:border-zinc-800 p-5 space-y-4 max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-3 border-b border-zinc-100 dark:border-zinc-800">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
                  <Plus className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-zinc-900 dark:text-white leading-tight">
                    Новий тікет / правка
                  </h3>
                  <p className="text-xs text-zinc-500 dark:text-zinc-400">
                    Зворотний зв'язок розробнику
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={handleCloseModal}
                disabled={isCreating}
                className="w-8 h-8 rounded-full flex items-center justify-center text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-3.5">
              {/* Type selection */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-zinc-700 dark:text-zinc-300">
                  Тип запиту:
                </label>
                <div className="grid grid-cols-3 gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setTicketType('REVISION');
                      haptic('selection');
                    }}
                    className={`min-h-[44px] flex items-center justify-center gap-1.5 px-2 py-2 rounded-xl text-xs font-semibold border transition-all ${
                      ticketType === 'REVISION'
                        ? 'bg-amber-50 dark:bg-amber-950/60 text-amber-800 dark:text-amber-300 border-amber-300 dark:border-amber-700 shadow-sm'
                        : 'border-zinc-200 dark:border-zinc-800 text-zinc-600 dark:text-zinc-400'
                    }`}
                  >
                    <Edit3 className="w-3.5 h-3.5" />
                    <span>Правка</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setTicketType('BUG');
                      haptic('selection');
                    }}
                    className={`min-h-[44px] flex items-center justify-center gap-1.5 px-2 py-2 rounded-xl text-xs font-semibold border transition-all ${
                      ticketType === 'BUG'
                        ? 'bg-rose-50 dark:bg-rose-950/60 text-rose-800 dark:text-rose-300 border-rose-300 dark:border-rose-700 shadow-sm'
                        : 'border-zinc-200 dark:border-zinc-800 text-zinc-600 dark:text-zinc-400'
                    }`}
                  >
                    <Bug className="w-3.5 h-3.5" />
                    <span>Баг</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setTicketType('QUESTION');
                      haptic('selection');
                    }}
                    className={`min-h-[44px] flex items-center justify-center gap-1.5 px-2 py-2 rounded-xl text-xs font-semibold border transition-all ${
                      ticketType === 'QUESTION'
                        ? 'bg-sky-50 dark:bg-sky-950/60 text-sky-800 dark:text-sky-300 border-sky-300 dark:border-sky-700 shadow-sm'
                        : 'border-zinc-200 dark:border-zinc-800 text-zinc-600 dark:text-zinc-400'
                    }`}
                  >
                    <HelpCircle className="w-3.5 h-3.5" />
                    <span>Запитання</span>
                  </button>
                </div>
              </div>

              {/* Milestone link */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-zinc-700 dark:text-zinc-300">
                  Прив'язка до етапу:
                </label>
                <select
                  value={selectedMilestoneId}
                  onChange={(e) => setSelectedMilestoneId(e.target.value)}
                  className="w-full min-h-[44px] px-3 py-2 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-xs text-zinc-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="">Загальне / Без прив'язки</option>
                  {milestones.map((m) => (
                    <option key={m.id} value={m.id}>
                      Етап #{m.order_index}: {m.title}
                    </option>
                  ))}
                </select>
              </div>

              {/* Message */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-zinc-700 dark:text-zinc-300">
                  Опис зауваження або запитання <span className="text-rose-500">*</span>
                </label>
                <textarea
                  rows={4}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Опишіть, що саме потрібно виправити або уточнити..."
                  className="w-full p-3 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-xs text-zinc-900 dark:text-white placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              {/* Attachment URL */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-zinc-700 dark:text-zinc-300">
                  Посилання на скріншот / Loom (необов'язково):
                </label>
                <input
                  type="url"
                  value={attachmentUrl}
                  onChange={(e) => setAttachmentUrl(e.target.value)}
                  placeholder="https://..."
                  className="w-full min-h-[44px] px-3 py-2 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-xs text-zinc-900 dark:text-white placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              {errorMsg && (
                <p className="text-xs text-rose-600 dark:text-rose-400 font-medium">
                  {errorMsg}
                </p>
              )}

              {/* Submit Buttons */}
              <div className="flex gap-2 pt-2">
                <button
                  type="button"
                  onClick={handleCloseModal}
                  disabled={isCreating}
                  className="flex-1 min-h-[46px] px-4 py-2.5 rounded-xl border border-zinc-200 dark:border-zinc-700 text-xs font-semibold text-zinc-700 dark:text-zinc-300 hover:bg-zinc-50 dark:hover:bg-zinc-800"
                >
                  Скасувати
                </button>
                <button
                  type="submit"
                  disabled={isCreating}
                  className="flex-1 min-h-[46px] px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-md shadow-indigo-500/25 disabled:opacity-50 flex items-center justify-center gap-1.5"
                >
                  {isCreating ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Відправка...</span>
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4" />
                      <span>Надіслати</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
