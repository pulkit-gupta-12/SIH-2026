/**
 * Notification Monitor Page (Step A).
 * Route: /admin/rules/notifications
 * Displays detected legal amendment notices with AI Draft Generation trigger.
 */
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { adminApi } from '../api';
import type { RuleNotification } from '../types';

export default function NotificationMonitorPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedNotification, setSelectedNotification] = useState<RuleNotification | null>(null);

  const { data: notifications = [], isLoading, error } = useQuery({
    queryKey: ['admin-notifications'],
    queryFn: adminApi.getNotifications,
  });

  const draftMutation = useMutation({
    mutationFn: (notificationId: number) => adminApi.createDraft({ notification_id: notificationId }),
    onSuccess: (draft) => {
      queryClient.invalidateQueries({ queryKey: ['admin-notifications'] });
      navigate(`/admin/rules/${draft.id}/review`);
    },
  });

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="glass-card p-6 border-l-4 border-amber-500 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-600 border border-amber-200">
              Regulatory Feed &middot; Step A
            </span>
            <span className="text-xs text-[var(--color-text-muted)]">e-Gazette & DoCA Monitor</span>
          </div>
          <h1 className="text-2xl font-bold text-[var(--color-text-primary)] mt-1">Legal Metrology Amendment Notifications</h1>
          <p className="text-sm text-[var(--color-text-secondary)] mt-0.5">
            Incoming gazette notifications requiring legal review, rule diffing, and system activation.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/admin/rules')}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-[var(--color-surface-tertiary)] hover:bg-gray-100 text-[var(--color-text-primary)] border border-[var(--color-border)] transition-all cursor-pointer"
          >
            Live Rule Repository &rarr;
          </button>
        </div>
      </div>

      {/* Notifications List */}
      {isLoading ? (
        <div className="glass-card p-12 text-center text-[var(--color-text-muted)] animate-pulse">
          Loading incoming amendment notifications...
        </div>
      ) : error ? (
        <div className="glass-card p-6 text-red-400 bg-red-950/30 border border-red-800">
          Failed to load notifications. Please check backend connection.
        </div>
      ) : notifications.length === 0 ? (
        <div className="glass-card p-12 text-center text-[var(--color-text-muted)]">
          No new amendment notifications found.
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {notifications.map((notif) => {
            const isDrafting = draftMutation.isPending && draftMutation.variables === notif.id;

            return (
              <div
                key={notif.id}
                className="glass-card p-5 border border-[var(--color-border)] hover:border-[var(--color-border)] transition-all space-y-4"
              >
                <div className="flex flex-col md:flex-row md:items-start justify-between gap-3">
                  <div className="space-y-1 flex-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-xs font-mono px-2 py-0.5 rounded bg-[var(--color-accent)]/15 text-[var(--color-accent)] font-semibold border border-[var(--color-accent)]">
                        {notif.notification_no}
                      </span>
                      <span className="text-xs px-2 py-0.5 rounded bg-[var(--color-surface-tertiary)] text-[var(--color-text-secondary)] uppercase tracking-wider font-medium">
                        {notif.category}
                      </span>
                      <span
                        className={`text-xs px-2 py-0.5 rounded font-semibold ${
                          notif.status === 'published'
                            ? 'bg-[var(--color-accent)]/20 text-[var(--color-accent)] border border-green-200'
                            : notif.status === 'approved'
                            ? 'bg-blue-50 text-blue-600 border border-blue-200'
                            : notif.status === 'drafted'
                            ? 'bg-amber-50 text-amber-600 border border-amber-200'
                            : 'bg-red-50 text-red-600 border border-red-200'
                        }`}
                      >
                        Status: {notif.status.toUpperCase()}
                      </span>
                      <span className="text-xs text-[var(--color-text-muted)]">
                        Published: {notif.published_date}
                      </span>
                    </div>
                    <h3 className="text-base font-bold text-[var(--color-text-primary)]">{notif.title}</h3>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setSelectedNotification(notif)}
                      className="px-3 py-1.5 rounded-lg text-xs font-medium bg-[var(--color-surface-tertiary)] hover:bg-gray-100 text-[var(--color-text-secondary)] transition-all cursor-pointer"
                    >
                      View Gazette Text
                    </button>
                    <button
                      onClick={() => draftMutation.mutate(notif.id)}
                      disabled={isDrafting}
                      className="px-4 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-[var(--color-text-primary)] shadow-md transition-all cursor-pointer disabled:opacity-50"
                    >
                      {isDrafting ? 'Generating AI Draft...' : '⚡ Generate AI Rule Draft'}
                    </button>
                  </div>
                </div>

                {/* Snippet */}
                <div className="p-3 rounded-lg bg-[var(--color-surface-tertiary)] border border-[var(--color-border)] text-xs text-[var(--color-text-secondary)] font-mono line-clamp-2 leading-relaxed">
                  "{notif.source_text}"
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Gazette Text Modal */}
      {selectedNotification && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[var(--color-surface-tertiary)]/80 backdrop-blur-sm animate-fade-in">
          <div className="glass-card max-w-2xl w-full p-6 space-y-4 max-h-[85vh] overflow-y-auto border border-[var(--color-border)]">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-[var(--color-accent)] font-semibold">
                {selectedNotification.notification_no}
              </span>
              <button
                onClick={() => setSelectedNotification(null)}
                className="text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] text-lg font-bold cursor-pointer"
              >
                &times;
              </button>
            </div>

            <h2 className="text-lg font-bold text-[var(--color-text-primary)]">{selectedNotification.title}</h2>
            <div className="text-xs text-[var(--color-text-muted)] flex items-center gap-4">
              <span>Category: <strong>{selectedNotification.category}</strong></span>
              <span>Published: <strong>{selectedNotification.published_date}</strong></span>
            </div>

            <div className="p-4 rounded-xl bg-[var(--color-surface-tertiary)]/90 border border-[var(--color-border)] text-xs text-[var(--color-text-primary)] font-serif leading-relaxed whitespace-pre-wrap">
              {selectedNotification.source_text}
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                onClick={() => setSelectedNotification(null)}
                className="px-4 py-2 rounded-xl text-xs font-medium bg-[var(--color-surface-tertiary)] hover:bg-gray-100 text-[var(--color-text-secondary)] cursor-pointer"
              >
                Close
              </button>
              <button
                onClick={() => {
                  const id = selectedNotification.id;
                  setSelectedNotification(null);
                  draftMutation.mutate(id);
                }}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-orange-600 hover:bg-orange-500 text-[var(--color-text-primary)] cursor-pointer"
              >
                ⚡ Generate AI Draft from this Text
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
