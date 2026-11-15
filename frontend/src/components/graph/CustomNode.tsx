'use client';

import React, { memo } from 'react';
import { Handle, Position } from '@xyflow/react';
import {
  Search,
  ShoppingBag,
  Users,
  Zap,
  AlertTriangle,
  Eye,
  CheckCircle2,
  Sparkles,
  Compass,
  FileText,
  MailCheck,
  Database,
  Palette,
  MessageSquare,
  TrendingUp,
  Award,
  Activity,
  Network,
  ShoppingCart,
  BellRing,
  Check,
  XCircle,
  Loader2,
  Clock,
  ArrowUpRight,
} from 'lucide-react';
import { WorkflowNodeData } from '@/types/workflow';

const ICON_MAP: Record<string, React.ElementType> = {
  Search,
  ShoppingBag,
  Users,
  Zap,
  AlertTriangle,
  Eye,
  CheckCircle2,
  Sparkles,
  Compass,
  FileText,
  MailCheck,
  Database,
  Palette,
  MessageSquare,
  TrendingUp,
  Award,
  Activity,
  Network,
  ShoppingCart,
  BellRing,
};

interface CustomNodeProps {
  data: WorkflowNodeData & {
    selected?: boolean;
    onClick?: () => void;
  };
}

export const CustomNode = memo(({ data }: CustomNodeProps) => {
  const IconComponent = (data.iconName && ICON_MAP[data.iconName]) || Activity;

  const getStatusStyles = () => {
    switch (data.status) {
      case 'running':
        return {
          containerClass: 'border-accent bg-paper-2',
          badgeClass: 'border border-accent text-accent bg-paper-3',
          badgeText: 'Running',
          badgeIcon: <Loader2 className="w-3 h-3 animate-spin motion-reduce:animate-none text-accent" />,
          iconBg: 'border border-accent text-accent bg-paper-3',
        };
      case 'completed':
        return {
          containerClass: 'border-rule bg-paper-2 hover:border-muted',
          badgeClass: 'border border-rule text-muted bg-paper-3',
          badgeText: 'Complete',
          badgeIcon: <Check className="w-3 h-3 text-accent" />,
          iconBg: 'border border-rule text-muted bg-paper-3',
        };
      case 'error':
        return {
          containerClass: 'border-error bg-paper-2',
          badgeClass: 'border border-error text-error bg-paper-3',
          badgeText: 'Failed',
          badgeIcon: <XCircle className="w-3 h-3 text-error" />,
          iconBg: 'border border-error text-error bg-paper-3',
        };
      default:
        return {
          containerClass: 'border-rule bg-paper-2 hover:border-muted',
          badgeClass: 'border border-rule-2 text-muted-2 bg-paper-3',
          badgeText: 'Idle',
          badgeIcon: <Clock className="w-3 h-3 text-muted-2" />,
          iconBg: 'border border-rule-2 text-muted-2 bg-paper-3',
        };
    }
  };

  const statusInfo = getStatusStyles();

  return (
    <div
      onClick={data.onClick}
      className={`relative p-4 min-w-[240px] max-w-[280px] border transition-colors duration-150 cursor-pointer ${statusInfo.containerClass}`}
    >
      {/* Target input handle */}
      <Handle
        type="target"
        position={Position.Left}
        className="!w-2.5 !h-2.5 !bg-paper-3 !border !border-rule hover:!border-accent transition-colors"
      />

      {/* Header with icon and status badge */}
      <div className="flex items-center justify-between gap-3 mb-2.5">
        <div className="flex items-center gap-2">
          <div className={`p-1.5 ${statusInfo.iconBg}`}>
            <IconComponent className="w-3.5 h-3.5" />
          </div>
          <div>
            <h4 className="text-xs font-medium text-ink leading-snug">
              {data.label}
            </h4>
          </div>
        </div>

        <div
          className={`flex items-center gap-1 px-1.5 py-0.5 text-[10px] font-mono ${statusInfo.badgeClass}`}
        >
          {statusInfo.badgeIcon}
          <span>{statusInfo.badgeText}</span>
        </div>
      </div>

      {/* Subtitle / Description */}
      {data.subtitle && (
        <p className="text-[11px] text-muted leading-relaxed line-clamp-2 mb-2">
          {data.subtitle}
        </p>
      )}

      {/* Duration or log snippet if running or complete */}
      <div className="flex items-center justify-between text-[11px] text-muted pt-2 border-t border-rule-2">
        <span className="font-mono text-muted">
          {data.durationMs ? `${data.durationMs}ms` : 'Ready'}
        </span>
        <div className="flex items-center gap-1 text-accent hover:text-accent/80 font-medium">
          <span>Inspect</span>
          <ArrowUpRight className="w-3 h-3" />
        </div>
      </div>

      {/* Source output handle */}
      <Handle
        type="source"
        position={Position.Right}
        className="!w-2.5 !h-2.5 !bg-paper-3 !border !border-rule hover:!border-accent transition-colors"
      />
    </div>
  );
});

CustomNode.displayName = 'CustomNode';
