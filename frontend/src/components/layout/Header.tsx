'use client';

import React from 'react';
import {
  ShoppingBag,
  Compass,
  FileSearch,
  Grid,
  Radar,
  Archive,
  Layers,
  Activity,
} from 'lucide-react';

export type ActiveModule =
  | 'lead-harvester'
  | 'shopify-revamp'
  | 'brand-audit'
  | 'competitor-matrix'
  | 'problem-radar'
  | 'saved-reports';

interface HeaderProps {
  activeModule: ActiveModule;
  onSelectModule: (module: ActiveModule) => void;
  leadsCount: number;
}

export function Header({ activeModule, onSelectModule, leadsCount }: HeaderProps) {
  const navItems: { id: ActiveModule; label: string; icon: React.ElementType; badge?: string }[] = [
    {
      id: 'lead-harvester',
      label: 'Lead Harvester',
      icon: Compass,
    },
    {
      id: 'shopify-revamp',
      label: 'Store Lead Farming',
      icon: ShoppingBag,
      badge: `${leadsCount} leads`,
    },
    {
      id: 'brand-audit',
      label: 'Brand Audit',
      icon: FileSearch,
    },
    {
      id: 'competitor-matrix',
      label: 'Competitor Matrix',
      icon: Grid,
    },
    {
      id: 'problem-radar',
      label: 'Problem Radar',
      icon: Radar,
    },
    {
      id: 'saved-reports',
      label: 'Saved Reports',
      icon: Archive,
    },
  ];

  return (
    <header className="sticky top-0 z-30 w-full border-b border-rule bg-paper/95 backdrop-blur-sm">
      <div className="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">
          {/* Brand Wordmark & Telemetry Mark */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-paper-2 border border-rule flex items-center justify-center text-accent">
              <Layers className="w-4 h-4 stroke-[2]" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="font-display font-medium text-sm text-ink tracking-tight">
                BrandAnalysis
              </span>
              <span className="text-xs text-muted">
                lead harvester
              </span>
            </div>
          </div>

          {/* Navigation Controls */}
          <nav className="hidden lg:flex items-center gap-1 border-x border-rule px-2 h-full">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeModule === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onSelectModule(item.id)}
                  className={`flex items-center gap-2 px-3 py-1.5 text-xs font-medium border transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-accent active:bg-paper-3 disabled:opacity-40 disabled:cursor-not-allowed ${
                    isActive
                      ? 'border-accent bg-paper-2 text-ink'
                      : 'border-transparent text-muted hover:text-ink hover:bg-paper-2'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{item.label}</span>
                  {item.badge && (
                    <span
                      className={`text-[10px] px-1 font-mono ${
                        isActive
                          ? 'text-accent'
                          : 'text-muted-2'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>

          {/* Telemetry Status Monitor */}
          <div className="flex items-center gap-2 px-3 py-1 bg-paper-2 border border-rule text-xs">
            <Activity className="w-3.5 h-3.5 text-accent signal-live" />
            <span className="text-xs text-muted">
              FastAPI: <strong className="text-ink font-mono font-normal">:8000</strong>
            </span>
          </div>
        </div>

        {/* Mobile Navigation bar */}
        <div className="lg:hidden flex items-center gap-1 overflow-x-auto py-2 border-t border-rule-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeModule === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectModule(item.id)}
                className={`flex items-center gap-1.5 px-2.5 py-1 text-xs whitespace-nowrap border transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-accent active:bg-paper-3 ${
                  isActive
                    ? 'border-accent bg-paper-2 text-ink font-medium'
                    : 'border-transparent text-muted hover:text-ink bg-paper-3'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>
      </div>
    </header>
  );
}
