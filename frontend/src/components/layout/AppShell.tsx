/**
 * AppShell — the main layout wrapper.
 * Provides Header + Sidebar (desktop) + BottomNav (mobile) + content area.
 */
import { Outlet } from 'react-router-dom';
import Header from './Header';
import Sidebar from './Sidebar';
import BottomNav from './BottomNav';

export default function AppShell() {
  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--color-surface-primary)' }}>
      <Header />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 p-4 md:p-6 pb-20 md:pb-6 overflow-auto">
          <Outlet />
        </main>
      </div>
      <BottomNav />
    </div>
  );
}
