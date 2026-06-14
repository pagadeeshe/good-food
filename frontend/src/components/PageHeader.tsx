import type { ReactNode } from 'react';

interface PageHeaderProps {
  eyebrow?: string;
  title: string;
  subtitle?: string;
  icon?: string;
  children?: ReactNode;
}

export function PageHeader({ eyebrow, title, subtitle, icon, children }: PageHeaderProps) {
  return (
    <header className="page-header">
      <div className="page-header-text">
        {eyebrow && <span className="eyebrow">{eyebrow}</span>}
        <h1>
          {icon && <span className="page-icon" aria-hidden>{icon}</span>}
          {title}
        </h1>
        {subtitle && <p className="page-subtitle">{subtitle}</p>}
      </div>
      {children && <div className="page-header-actions">{children}</div>}
    </header>
  );
}

export function LoadingState({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="loading-state">
      <div className="spinner" aria-hidden />
      <p>{label}</p>
    </div>
  );
}

export function EmptyState({ icon, title, message }: { icon: string; title: string; message: string }) {
  return (
    <div className="empty-state">
      <span className="empty-icon" aria-hidden>{icon}</span>
      <h3>{title}</h3>
      <p>{message}</p>
    </div>
  );
}
