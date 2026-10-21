import React from 'react';
import { Info, AlertTriangle, AlertOctagon, CheckCircle2 } from 'lucide-react';

interface CalloutProps {
  type?: 'info' | 'tip' | 'warning' | 'caution';
  title?: string;
  children: React.ReactNode;
}

export const Callout: React.FC<CalloutProps> = ({
  type = 'info',
  title,
  children,
}) => {
  const configs = {
    info: {
      border: 'border-cyan-500/30',
      bg: 'bg-cyan-950/20',
      titleColor: 'text-cyan-300',
      icon: Info,
      iconColor: 'text-cyan-400',
      defaultTitle: 'Note',
    },
    tip: {
      border: 'border-emerald-500/30',
      bg: 'bg-emerald-950/20',
      titleColor: 'text-emerald-300',
      icon: CheckCircle2,
      iconColor: 'text-emerald-400',
      defaultTitle: 'Pro Tip',
    },
    warning: {
      border: 'border-amber-500/30',
      bg: 'bg-amber-950/20',
      titleColor: 'text-amber-300',
      icon: AlertTriangle,
      iconColor: 'text-amber-400',
      defaultTitle: 'Important',
    },
    caution: {
      border: 'border-rose-500/40',
      bg: 'bg-rose-950/20',
      titleColor: 'text-rose-300',
      icon: AlertOctagon,
      iconColor: 'text-rose-400',
      defaultTitle: 'Caution / Destructive Action',
    },
  };

  const config = configs[type];
  const Icon = config.icon;

  return (
    <div className={`my-4 p-4 rounded-xl border ${config.border} ${config.bg} backdrop-blur-sm text-sm leading-relaxed shadow-lg`}>
      <div className="flex items-center gap-2 mb-1.5">
        <Icon className={`w-4 h-4 ${config.iconColor} flex-shrink-0`} />
        <span className={`font-semibold ${config.titleColor} text-sm font-sans tracking-wide uppercase text-[12px]`}>
          {title || config.defaultTitle}
        </span>
      </div>
      <div className="text-slate-300 text-[13.5px] leading-relaxed pl-6 space-y-1">
        {children}
      </div>
    </div>
  );
};
