'use client';

import React from 'react';
import {
  Play,
  Square,
  Sliders,
  Compass,
  Shield,
  Loader2,
  Gauge,
  Users,
  AlertOctagon,
} from 'lucide-react';
import { AuditThresholds } from '@/types/workflow';

interface ControlsPanelProps {
  targetInput: string;
  setTargetInput: (val: string) => void;
  thresholds: AuditThresholds;
  setThresholds: React.Dispatch<React.SetStateAction<AuditThresholds>>;
  isRunning: boolean;
  onRunToggle: () => void;
}

export function ControlsPanel({
  targetInput,
  setTargetInput,
  thresholds,
  setThresholds,
  isRunning,
  onRunToggle,
}: ControlsPanelProps) {
  const quickSuggestions = [
    'Organic Skincare Brands',
    'Artisan Jewelry Austin',
    'Sustainable Outdoor Apparel',
    'Specialty Coffee Roasters',
  ];

  return (
    <div className="w-full space-y-4">
      {/* Automation Trigger Bar */}
      <div className="panel p-5">
        <div className="flex flex-col md:flex-row items-stretch md:items-center gap-3">
          {/* Target input field */}
          <div className="relative flex-1">
            <div className="absolute left-3.5 top-1/2 -translate-y-1/2 text-muted">
              <Compass className="w-4 h-4" />
            </div>
            <input
              type="text"
              value={targetInput}
              onChange={(e) => setTargetInput(e.target.value)}
              placeholder="Target niche or store domain (e.g. Organic Skincare Brands in Austin)"
              className="w-full pl-10 pr-4 py-2.5 bg-paper-3 border border-rule text-sm text-ink placeholder:text-muted focus-visible:outline-2 focus-visible:outline-focus focus:border-accent transition-colors duration-150"
            />
          </div>

          {/* Run Automation CTA */}
          <button
            onClick={onRunToggle}
            className={`flex items-center justify-center gap-2 px-5 py-2.5 text-xs font-medium whitespace-nowrap transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus disabled:opacity-40 disabled:cursor-not-allowed ${
              isRunning
                ? 'bg-paper-3 border border-error text-error hover:bg-error/10 active:bg-error/20'
                : 'bg-accent text-accent-ink border border-accent hover:opacity-95 active:opacity-90'
            }`}
          >
            {isRunning ? (
              <>
                <Square className="w-3.5 h-3.5 fill-current" />
                <span className="whitespace-nowrap">Halt</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span className="whitespace-nowrap">Run</span>
              </>
            )}
          </button>
        </div>

        {/* Quick Suggestion Chips */}
        <div className="flex flex-wrap items-center gap-2 mt-3 pt-3 border-t border-rule-2">
          <span className="text-xs text-muted">Suggested targets:</span>
          {quickSuggestions.map((suggestion) => (
            <button
              key={suggestion}
              onClick={() => setTargetInput(suggestion)}
              className="px-2.5 py-1 text-xs text-muted hover:text-ink bg-paper-3 border border-rule hover:border-muted transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>

      {/* Threshold Sliders Panel */}
      <div className="panel p-5">
        <div className="flex items-center justify-between mb-4 pb-2 border-b border-rule-2">
          <div className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-accent" />
            <h3 className="text-xs font-medium text-ink">
              Qualification thresholds
            </h3>
          </div>
          <span className="text-xs text-muted">
            Telemetry filter boundaries
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Threshold 1: Max Lighthouse Speed */}
          <div className="space-y-2 p-3 bg-paper-3 border border-rule-2">
            <div className="flex items-center justify-between">
              <label className="text-xs text-muted flex items-center gap-1.5">
                <Gauge className="w-3.5 h-3.5 text-accent-2" />
                Max Lighthouse score
              </label>
              <span className="font-mono text-xs text-accent-2">
                {thresholds.maxLighthouseScore} / 100
              </span>
            </div>
            <input
              type="range"
              min="20"
              max="90"
              step="5"
              value={thresholds.maxLighthouseScore}
              onChange={(e) =>
                setThresholds((prev) => ({
                  ...prev,
                  maxLighthouseScore: Number(e.target.value),
                }))
              }
              className="w-full h-1 bg-paper border border-rule accent-[var(--color-accent)] cursor-pointer"
            />
            <p className="text-[11px] text-muted-2">
              Flags stores scoring below this threshold as performance revamp candidates.
            </p>
          </div>

          {/* Threshold 2: Min Follower Base */}
          <div className="space-y-2 p-3 bg-paper-3 border border-rule-2">
            <div className="flex items-center justify-between">
              <label className="text-xs text-muted flex items-center gap-1.5">
                <Users className="w-3.5 h-3.5 text-accent" />
                Minimum followers
              </label>
              <span className="font-mono text-xs text-accent">
                {thresholds.minFollowers.toLocaleString()}
              </span>
            </div>
            <input
              type="range"
              min="500"
              max="25000"
              step="500"
              value={thresholds.minFollowers}
              onChange={(e) =>
                setThresholds((prev) => ({
                  ...prev,
                  minFollowers: Number(e.target.value),
                }))
              }
              className="w-full h-1 bg-paper border border-rule accent-[var(--color-accent)] cursor-pointer"
            />
            <p className="text-[11px] text-muted-2">
              Filters out abandoned accounts with insufficient audience scale.
            </p>
          </div>

          {/* Threshold 3: Min Console Errors */}
          <div className="space-y-2 p-3 bg-paper-3 border border-rule-2">
            <div className="flex items-center justify-between">
              <label className="text-xs text-muted flex items-center gap-1.5">
                <AlertOctagon className="w-3.5 h-3.5 text-error" />
                Minimum console errors
              </label>
              <span className="font-mono text-xs text-error">
                {thresholds.minConsoleErrors} {thresholds.minConsoleErrors === 1 ? 'error' : 'errors'}
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="10"
              step="1"
              value={thresholds.minConsoleErrors}
              onChange={(e) =>
                setThresholds((prev) => ({
                  ...prev,
                  minConsoleErrors: Number(e.target.value),
                }))
              }
              className="w-full h-1 bg-paper border border-rule accent-[var(--color-accent)] cursor-pointer"
            />
            <p className="text-[11px] text-muted-2">
              Requires Playwright telemetry to capture runtime script failures.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
