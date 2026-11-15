'use client';

import React, { useState } from 'react';
import {
  Radar,
  AlertTriangle,
  Flame,
  MessageCircle,
  ExternalLink,
  Sparkles,
  AlertCircle,
  X,
  ArrowRight,
} from 'lucide-react';
import { WorkflowGraph } from '@/components/graph/WorkflowGraph';

interface RadarIssue {
  id: string;
  title: string;
  source: string;
  category: string;
  sentiment: string;
  severity: number;
  velocity: string;
  excerpt: string;
  url?: string;
  opportunity: string;
}

interface MicroSaaSBlueprint {
  concept: string;
  source_problem?: string;
  target_icp: string;
  mvp_features: string[];
  monetization: string;
}

export function ProblemRadarView() {
  const [issues, setIssues] = useState<RadarIssue[]>([]);
  const [blueprints, setBlueprints] = useState<MicroSaaSBlueprint[]>([]);
  const [isScanning, setIsScanning] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [selectedSource, setSelectedSource] = useState<string>('All');

  const handleScanRadar = () => {
    setIsScanning(true);
    setErrorMessage(null);

    const sseUrl = `/api/workflows/problem-radar/run`;
    const eventSource = new EventSource(sseUrl);

    eventSource.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        const eventType = payload.event;
        const nodeId = payload.node_id;

        if (eventType === 'node_complete' && payload.output) {
          const out = payload.output;

          if (nodeId === 'node_severity_velocity' && out.scored_problems) {
            setIssues(out.scored_problems);
          }

          if (nodeId === 'node_saas_architect' && out.blueprints) {
            setBlueprints(out.blueprints);
          }
        }

        if (eventType === 'node_error') {
          setErrorMessage(`Problem Radar error: ${payload.error || 'Failed to scan feeds'}`);
          setIsScanning(false);
          eventSource.close();
        }

        if (eventType === 'workflow_complete') {
          setIsScanning(false);
          eventSource.close();
        }
      } catch (e) {
        console.warn('Error parsing SSE event:', e);
      }
    };

    eventSource.onerror = () => {
      setErrorMessage('Workflow stream interrupted or failed to connect to backend.');
      setIsScanning(false);
      eventSource.close();
    };
  };

  const filteredIssues = issues.filter(
    (i) => selectedSource === 'All' || i.source.toLowerCase().includes(selectedSource.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Workflow DAG for Problem Radar */}
      <WorkflowGraph
        currentWorkflowId="problem-radar"
        isRunning={isScanning}
        onRunToggle={() => {
          if (isScanning) setIsScanning(false);
          else handleScanRadar();
        }}
      />

      {/* Error notification banner */}
      {errorMessage && (
        <div className="p-4 bg-error/10 border border-error/30 text-error text-xs flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-error" />
            <span>{errorMessage}</span>
          </div>
          <button
            onClick={() => setErrorMessage(null)}
            className="p-1 hover:bg-error/20 text-error rounded"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Filter and stats banner */}
      <div className="panel p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Radar className="w-4 h-4 text-accent" />
          <div>
            <h3 className="text-xs font-medium text-ink">
              Developer Pain Points & Micro-SaaS Radar
            </h3>
            <p className="text-[11px] text-muted">
              Live crawler scanning discussions from Hacker News, Dev.to, and Google Tech News RSS.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <div className="flex items-center gap-1 bg-paper-3 p-1 border border-rule">
            {['All', 'Hacker News', 'Dev.to', 'Google'].map((src) => (
              <button
                key={src}
                onClick={() => setSelectedSource(src)}
                className={`px-2.5 py-1 text-xs font-medium border transition-colors duration-150 ${
                  selectedSource === src
                    ? 'border-accent bg-paper-2 text-accent'
                    : 'border-transparent text-muted hover:text-ink'
                }`}
              >
                {src}
              </button>
            ))}
          </div>

          <button
            onClick={handleScanRadar}
            disabled={isScanning}
            className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-medium bg-accent text-accent-ink border border-accent hover:opacity-95 transition-colors duration-150 active:opacity-90 disabled:opacity-40"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>{isScanning ? 'Scanning feeds…' : 'Scan Live Feeds'}</span>
          </button>
        </div>
      </div>

      {/* Architected Micro-SaaS Blueprints */}
      {blueprints.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-xs font-medium text-ink flex items-center gap-2">
            <Sparkles className="w-3.5 h-3.5 text-accent" />
            Synthesized Micro-SaaS & DevTool Opportunities
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {blueprints.map((bp, idx) => (
              <div key={idx} className="panel p-4 space-y-3 bg-paper-2 border-accent/30">
                <div>
                  <span className="text-[10px] font-mono text-accent uppercase tracking-wider block mb-1">
                    Concept #{idx + 1}
                  </span>
                  <h5 className="text-xs font-medium text-ink leading-snug">
                    {bp.concept}
                  </h5>
                  <p className="text-[11px] text-muted mt-1">
                    ICP: <span className="text-ink font-normal">{bp.target_icp}</span>
                  </p>
                </div>

                <div className="space-y-1 pt-2 border-t border-rule-2">
                  <span className="text-[10px] text-muted uppercase font-mono block">MVP Scope</span>
                  {bp.mvp_features.map((feat, fIdx) => (
                    <div key={fIdx} className="text-xs text-ink-2 flex items-start gap-1.5">
                      <span className="w-1 h-1 bg-accent rounded-full mt-1.5 shrink-0" />
                      <span>{feat}</span>
                    </div>
                  ))}
                </div>

                <div className="pt-2 border-t border-rule-2 flex justify-between items-center text-xs">
                  <span className="text-muted">Model:</span>
                  <span className="font-mono text-accent font-medium">{bp.monetization}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Issues Cards */}
      {filteredIssues.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredIssues.map((issue) => (
            <div
              key={issue.id}
              className="panel p-4 space-y-3 flex flex-col justify-between hover:border-muted transition-colors duration-150"
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-2">
                  <span className="text-xs font-mono px-2 py-0.5 border border-rule bg-paper-3 text-muted">
                    {issue.source}
                  </span>
                  <span
                    className={`text-xs px-2 py-0.5 border ${
                      issue.severity >= 8.5
                        ? 'border-error text-error bg-paper-3'
                        : 'border-accent text-accent bg-paper-3'
                    }`}
                  >
                    Severity: {issue.severity}/10
                  </span>
                </div>

                <h4 className="text-xs font-medium text-ink leading-snug">
                  {issue.title}
                </h4>
                {issue.excerpt && (
                  <p className="text-xs text-muted mt-1.5 leading-relaxed line-clamp-3">
                    {issue.excerpt}
                  </p>
                )}
              </div>

              <div className="pt-3 border-t border-rule-2 space-y-2">
                <div className="p-3 bg-paper-3 border border-rule text-xs text-ink-2">
                  <span className="block text-xs font-medium text-accent mb-0.5">
                    Opportunity Vector:
                  </span>
                  {issue.opportunity}
                </div>

                <div className="flex items-center justify-between text-xs text-muted">
                  <span className="font-mono text-[11px]">{issue.velocity}</span>
                  {issue.url && (
                    <a
                      href={issue.url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 text-accent hover:underline text-[11px] font-mono"
                    >
                      <span>Discussion</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="panel py-12 text-center text-muted">
          <Radar className="w-8 h-8 text-muted mx-auto mb-3 opacity-60" />
          <h4 className="text-sm font-medium text-ink mb-1">No community discussions loaded</h4>
          <p className="text-xs text-muted max-w-md mx-auto">
            Click &ldquo;Scan Live Feeds&rdquo; above to query Hacker News, Dev.to, and Google Tech News for developer friction and Micro-SaaS ideas.
          </p>
        </div>
      )}
    </div>
  );
}
