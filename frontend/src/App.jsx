import React, { useState, useEffect, useCallback } from 'react';
import { useTelegram } from './context/TelegramContext';
import { api } from './services/api';
import Header from './components/Header';
import MilestonesTimeline from './components/MilestonesTimeline';
import SignatureModal from './components/SignatureModal';
import TicketsSection from './components/TicketsSection';
import AdminDashboard from './components/AdminDashboard';
import { Loader2, AlertCircle, RotateCcw, Check } from 'lucide-react';

export default function App() {
  const { initData, isAdmin, activeRole, haptic } = useTelegram();

  // Component state - ALL hooks declared at the very top
  const [project, setProject] = useState(null);
  const [adminProjects, setAdminProjects] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null); // { text, type: 'success' | 'error' | 'info' }

  // Signature modal state
  const [isSignatureModalOpen, setIsSignatureModalOpen] = useState(false);
  const [selectedMilestone, setSelectedMilestone] = useState(null);
  const [isSubmittingSignature, setIsSubmittingSignature] = useState(false);

  // Ticket creation state
  const [isCreatingTicket, setIsCreatingTicket] = useState(false);

  // Toast auto-dismiss timer
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => {
      setToast(null);
    }, 3500);
    return () => clearTimeout(timer);
  }, [toast]);

  const showToast = useCallback((text, type = 'info') => {
    setToast({ text, type });
  }, []);

  // Fetch client active project
  const loadClientProject = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getActiveProject(initData);
      setProject(data);
    } catch (err) {
      console.error('Failed to load active project:', err);
      setError(err.message || 'Не вдалося завантажити проект');
    } finally {
      setIsLoading(false);
    }
  }, [initData]);

  // Fetch admin projects
  const loadAdminProjects = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getAdminProjects(initData);
      setAdminProjects(data);
    } catch (err) {
      console.error('Failed to load admin projects:', err);
      setError(err.message || 'Не вдалося завантажити панель адміністратора');
    } finally {
      setIsLoading(false);
    }
  }, [initData]);

  // Main data fetch effect when role or initData changes
  useEffect(() => {
    if (isAdmin) {
      loadAdminProjects();
    } else {
      loadClientProject();
    }
  }, [isAdmin, loadClientProject, loadAdminProjects]);

  // Refresh handler
  const handleRefresh = useCallback(() => {
    haptic('light');
    if (isAdmin) {
      loadAdminProjects();
    } else {
      loadClientProject();
    }
  }, [isAdmin, haptic, loadClientProject, loadAdminProjects]);

  // Signature approval flow
  const handleOpenSignature = useCallback((milestone) => {
    setSelectedMilestone(milestone);
    setIsSignatureModalOpen(true);
  }, []);

  const handleCloseSignature = useCallback(() => {
    if (isSubmittingSignature) return;
    setIsSignatureModalOpen(false);
    setSelectedMilestone(null);
  }, [isSubmittingSignature]);

  const handleConfirmSignature = useCallback(
    async (signatureData) => {
      if (!selectedMilestone) return;
      setIsSubmittingSignature(true);
      try {
        await api.approveMilestone(initData, selectedMilestone.id, signatureData);
        haptic('success');
        showToast('Етап успішно затверджено', 'success');
        setIsSignatureModalOpen(false);
        setSelectedMilestone(null);
        await loadClientProject();
      } catch (err) {
        console.error('Approval failed:', err);
        haptic('error');
        showToast(err.message || 'Помилка затвердження етапу', 'error');
        throw err;
      } finally {
        setIsSubmittingSignature(false);
      }
    },
    [selectedMilestone, initData, haptic, showToast, loadClientProject]
  );

  // Ticket creation flow
  const handleCreateTicket = useCallback(
    async (ticketData) => {
      setIsCreatingTicket(true);
      try {
        const newTicket = await api.createTicket(initData, ticketData);
        haptic('success');
        showToast('Запит успішно надіслано', 'success');
        if (project) {
          setProject((prev) => ({
            ...prev,
            tickets: [newTicket, ...(prev?.tickets || [])],
          }));
        }
      } catch (err) {
        console.error('Ticket creation failed:', err);
        haptic('error');
        showToast(err.message || 'Не вдалося створити запит', 'error');
        throw err;
      } finally {
        setIsCreatingTicket(false);
      }
    },
    [initData, haptic, showToast, project]
  );

  // Admin status update handlers
  const handleAdminUpdateMilestoneStatus = useCallback(
    async (milestoneId, status) => {
      try {
        await api.updateMilestoneStatus(initData, milestoneId, status);
        showToast(`Статус етапу оновлено: ${status}`, 'success');
        await loadAdminProjects();
      } catch (err) {
        showToast(err.message || 'Помилка зміни статусу етапу', 'error');
      }
    },
    [initData, showToast, loadAdminProjects]
  );

  const handleAdminUpdateTicketStatus = useCallback(
    async (ticketId, status) => {
      try {
        await api.updateTicketStatus(initData, ticketId, status);
        showToast(`Статус тікета #${ticketId} оновлено`, 'success');
        await loadAdminProjects();
      } catch (err) {
        showToast(err.message || 'Помилка зміни статусу тікета', 'error');
      }
    },
    [initData, showToast, loadAdminProjects]
  );

  return (
    <div className="max-w-md mx-auto min-h-screen px-4 py-4 pb-20 overflow-x-hidden space-y-4">
      {/* Toast Notification */}
      {toast && (
        <div className="fixed top-4 left-1/2 -translate-x-1/2 z-50 w-[90%] max-w-sm transition-all duration-300">
          <div
            className={`flex items-center gap-2.5 px-4 py-3 rounded-2xl shadow-xl text-xs font-semibold backdrop-blur-md border ${
              toast.type === 'success'
                ? 'bg-zinc-900/95 dark:bg-zinc-100/95 text-white dark:text-zinc-900 border-zinc-800'
                : toast.type === 'error'
                ? 'bg-rose-600/95 text-white border-rose-500 shadow-rose-900/20'
                : 'bg-zinc-900/95 text-white border-zinc-700'
            }`}
          >
            {toast.type === 'success' ? (
              <Check className="w-4 h-4 flex-shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
            )}
            <span className="flex-1 break-words">{toast.text}</span>
          </div>
        </div>
      )}

      {/* Apple / Samsung Header with Refresh */}
      <Header
        project={project}
        onRefresh={handleRefresh}
        isLoading={isLoading}
      />

      {/* Main Content Area: Strict Role Isolation */}
      {!isAdmin ? (
        <main className="space-y-4">
          {isLoading && !project ? (
            <div className="py-16 text-center space-y-2">
              <Loader2 className="w-6 h-6 mx-auto animate-spin text-zinc-400" />
              <p className="text-xs text-zinc-400 font-medium">Завантаження проекту...</p>
            </div>
          ) : error && !project ? (
            <div className="bg-white dark:bg-zinc-900 rounded-2xl p-6 text-center border border-zinc-200/80 dark:border-zinc-800 space-y-3">
              <AlertCircle className="w-6 h-6 mx-auto text-zinc-400" />
              <div className="space-y-1">
                <p className="text-sm font-semibold text-zinc-900 dark:text-white">Помилка завантаження</p>
                <p className="text-xs text-zinc-500 break-words">{error}</p>
              </div>
              <button
                type="button"
                onClick={handleRefresh}
                className="min-h-[44px] px-4 py-2 rounded-xl bg-zinc-900 hover:bg-black dark:bg-zinc-100 dark:hover:bg-white text-white dark:text-zinc-900 text-xs font-semibold shadow-sm transition-all inline-flex items-center gap-1.5"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Спробувати знову</span>
              </button>
            </div>
          ) : project ? (
            <>
              {/* Milestones timeline */}
              <MilestonesTimeline
                milestones={project.milestones || []}
                currency={project.currency}
                onOpenSignature={handleOpenSignature}
              />

              {/* Tickets section */}
              <TicketsSection
                tickets={project.tickets || []}
                milestones={project.milestones || []}
                onCreateTicket={handleCreateTicket}
                isCreating={isCreatingTicket}
              />
            </>
          ) : null}
        </main>
      ) : (
        <main>
          {isLoading && adminProjects.length === 0 ? (
            <div className="py-16 text-center space-y-2">
              <Loader2 className="w-6 h-6 mx-auto animate-spin text-zinc-400" />
              <p className="text-xs text-zinc-400 font-medium">Завантаження панелі розробника...</p>
            </div>
          ) : (
            <AdminDashboard
              projects={adminProjects}
              isLoading={isLoading}
              onRefresh={handleRefresh}
              onUpdateMilestoneStatus={handleAdminUpdateMilestoneStatus}
              onUpdateTicketStatus={handleAdminUpdateTicketStatus}
            />
          )}
        </main>
      )}

      {/* Signature Modal */}
      <SignatureModal
        isOpen={isSignatureModalOpen}
        onClose={handleCloseSignature}
        milestone={selectedMilestone}
        onConfirm={handleConfirmSignature}
        isSubmitting={isSubmittingSignature}
      />

      {/* Minimalist Footer */}
      <footer className="pt-6 text-center text-[11px] text-zinc-400 dark:text-zinc-600 space-y-0.5">
        <p className="font-medium">Client Portal &amp; Milestone Desk</p>
        <p>Захищено цифровим підписом</p>
      </footer>
    </div>
  );
}
