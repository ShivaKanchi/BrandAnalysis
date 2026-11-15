'use client';

import React, { useState } from 'react';
import {
  FileSearch,
  CheckCircle2,
  TrendingUp,
  ArrowRight,
} from 'lucide-react';
import { WorkflowGraph } from '@/components/graph/WorkflowGraph';

export function BrandAuditView() {
  const [brandInput, setBrandInput] = useState('lumina-skin.com');
  const [isAuditing, setIsAuditing] = useState(false);
  const [auditResult, setAuditResult] = useState({
    brandName: 'Lumina Organic Skincare',
    overallScore: 78,
    visualConsistency: 85,
    copySentiment: 72,
    trustSignals: 68,
    archetype: 'The Natural Caregiver and Sage',
    colorPalette: ['#0f172a', '#10b981', '#06b6d4', '#f1f5f9'],
    fontsDetected: ['Cinzel', 'Inter Display', 'System Sans'],
    strengths: [
      'High photographic standard with consistent botanical and earth-tone art direction',
      'Clear value proposition centered on zero-pesticide, organic certified ingredients',
      'Strong user-generated content on storefront with 3.4% engagement rate',
    ],
    weaknesses: [
      'Disjointed typography scale between desktop hero and mobile product cards',
      'Absence of clinical trial or third-party dermatological certification above the fold',
      'Copy tone fluctuates between technical scientific and casual lifestyle prose',
    ],
  });

  const handleRunAudit = () => {
    setIsAuditing(true);
    setTimeout(() => {
      setIsAuditing(false);
    }, 1800);
  };

  return (
    <div className="space-y-6">
      {/* Workflow DAG for Brand Audit */}
      <WorkflowGraph currentWorkflowId="brand-audit" />

      {/* Audit Trigger Card */}
      <div className="panel p-5">
        <div className="flex items-center gap-2 mb-3">
          <FileSearch className="w-4 h-4 text-accent" />
          <h3 className="text-xs font-medium text-ink">
            Deep brand reverse-engineering audit
          </h3>
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            value={brandInput}
            onChange={(e) => setBrandInput(e.target.value)}
            placeholder="Enter brand domain or store handle (e.g. glossier.com)"
            className="flex-1 px-4 py-2 bg-paper-3 border border-rule text-xs text-ink placeholder:text-muted focus-visible:outline-2 focus-visible:outline-focus focus:border-accent transition-colors duration-150"
          />
          <button
            onClick={handleRunAudit}
            disabled={isAuditing}
            className="flex items-center justify-center gap-2 px-5 py-2 text-xs font-medium bg-accent text-accent-ink border border-accent hover:opacity-95 transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <span className="whitespace-nowrap">{isAuditing ? 'Analyzing brand…' : 'Run brand audit'}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Brand Audit Results Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Scorecard Overview */}
        <div className="panel p-5 space-y-4">
          <div>
            <span className="text-xs text-muted block mb-1">
              Brand composite health
            </span>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-normal text-accent font-mono">
                {auditResult.overallScore}
              </span>
              <span className="text-xs text-muted">/ 100</span>
            </div>
            <p className="text-xs text-muted mt-1">
              Archetype: <strong className="text-ink font-normal">{auditResult.archetype}</strong>
            </p>
          </div>

          <div className="space-y-3 pt-3 border-t border-rule-2">
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-muted">Visual consistency</span>
                <span className="text-ink font-mono">{auditResult.visualConsistency}%</span>
              </div>
              <div className="h-1 w-full bg-paper-3 border border-rule overflow-hidden">
                <div
                  className="h-full bg-accent"
                  style={{ width: `${auditResult.visualConsistency}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-muted">Copywriting sentiment</span>
                <span className="text-ink font-mono">{auditResult.copySentiment}%</span>
              </div>
              <div className="h-1 w-full bg-paper-3 border border-rule overflow-hidden">
                <div
                  className="h-full bg-accent-2"
                  style={{ width: `${auditResult.copySentiment}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-muted">Trust architecture</span>
                <span className="text-ink font-mono">{auditResult.trustSignals}%</span>
              </div>
              <div className="h-1 w-full bg-paper-3 border border-rule overflow-hidden">
                <div
                  className="h-full bg-accent"
                  style={{ width: `${auditResult.trustSignals}%` }}
                />
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-rule-2">
            <span className="text-xs text-muted block mb-2 font-normal">
              Extracted brand colors
            </span>
            <div className="flex items-center gap-2">
              {auditResult.colorPalette.map((color, idx) => (
                <div key={idx} className="flex flex-col items-center gap-1">
                  <div
                    className="w-6 h-6 border border-rule"
                    style={{ backgroundColor: color }}
                  />
                  <span className="text-[10px] font-mono text-muted">{color}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Brand Strengths & Opportunities */}
        <div className="panel p-5 lg:col-span-2 space-y-5">
          <div>
            <h4 className="text-xs font-medium text-ink mb-2.5 flex items-center gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-accent" />
              Core brand strengths
            </h4>
            <div className="space-y-1.5">
              {auditResult.strengths.map((str, idx) => (
                <div
                  key={idx}
                  className="p-3 bg-paper-3 border border-rule text-xs text-ink-2 flex items-start gap-2.5"
                >
                  <span className="w-1.5 h-1.5 bg-accent mt-1.5 shrink-0" />
                  <span>{str}</span>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h4 className="text-xs font-medium text-ink mb-2.5 flex items-center gap-2">
              <TrendingUp className="w-3.5 h-3.5 text-accent-2" />
              Strategic growth bottlenecks
            </h4>
            <div className="space-y-1.5">
              {auditResult.weaknesses.map((w, idx) => (
                <div
                  key={idx}
                  className="p-3 bg-paper-3 border border-rule text-xs text-ink-2 flex items-start gap-2.5"
                >
                  <span className="w-1.5 h-1.5 bg-accent-2 mt-1.5 shrink-0" />
                  <span>{w}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
