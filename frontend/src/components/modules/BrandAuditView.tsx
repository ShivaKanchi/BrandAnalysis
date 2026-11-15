'use client';

import React, { useState } from 'react';
import {
  FileSearch,
  CheckCircle2,
  TrendingUp,
  ArrowRight,
  AlertCircle,
  X,
  ExternalLink,
} from 'lucide-react';
import { WorkflowGraph } from '@/components/graph/WorkflowGraph';

interface BrandAuditData {
  brandName: string;
  overallScore: number;
  visualConsistency: number;
  copySentiment: number;
  trustSignals: number;
  archetype: string;
  colorPalette: string[];
  fontsDetected: string[];
  strengths: string[];
  weaknesses: string[];
  followersCount?: number;
  followersVerified?: boolean;
  softwarePitch?: string;
  website?: string;
}

export function BrandAuditView() {
  const [brandInput, setBrandInput] = useState('aloyoga.com');
  const [isAuditing, setIsAuditing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [auditResult, setAuditResult] = useState<BrandAuditData | null>(null);

  const handleRunAudit = () => {
    if (!brandInput.trim()) {
      setErrorMessage('Please enter a valid brand domain or Instagram handle.');
      return;
    }

    setIsAuditing(true);
    setErrorMessage(null);

    const target = brandInput.trim();
    const sseUrl = `/api/workflows/brand-audit/run?username=${encodeURIComponent(target)}&url=${encodeURIComponent(target)}`;
    const eventSource = new EventSource(sseUrl);

    // Initial draft result
    const currentData: BrandAuditData = {
      brandName: target.split('.')[0].toUpperCase(),
      overallScore: 75,
      visualConsistency: 70,
      copySentiment: 75,
      trustSignals: 70,
      archetype: 'Analyzing brand posture...',
      colorPalette: ['#1A1A1A', '#F4EBE1', '#E0A96D'],
      fontsDetected: ['System Typography'],
      strengths: [],
      weaknesses: [],
      website: target.startsWith('http') ? target : `https://${target}`,
    };

    eventSource.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        const eventType = payload.event;
        const nodeId = payload.node_id;

        if (eventType === 'node_complete' && payload.output) {
          const out = payload.output;

          if (nodeId === 'node_profile_scrape' && out.profile) {
            currentData.brandName = out.profile.full_name || target;
            currentData.followersCount = out.profile.followers_count || 0;
            currentData.followersVerified = Boolean(out.profile.followers_verified);
            if (out.profile.external_url) currentData.website = out.profile.external_url;
            if (out.profile.biography) {
              currentData.strengths.push(`Profile Bio: "${out.profile.biography}"`);
            }
          }

          if (nodeId === 'node_brand_voice' && out.brand_voice) {
            currentData.archetype = out.brand_voice.archetype || 'Tastemaker';
            if (out.brand_voice.target_audience) {
              currentData.strengths.push(`Audience Profile: ${out.brand_voice.target_audience}`);
            }
            if (out.brand_voice.tone_keywords) {
              currentData.strengths.push(`Tone Attributes: ${out.brand_voice.tone_keywords.join(', ')}`);
            }
          }

          if (nodeId === 'node_visual_aesthetic' && out.visual_identity) {
            currentData.visualConsistency = out.visual_identity.aesthetic_score || 85;
            if (out.visual_identity.palette) {
              currentData.colorPalette = out.visual_identity.palette;
            }
            if (out.visual_identity.recommendations) {
              currentData.weaknesses.push(...out.visual_identity.recommendations);
            }
          }

          if (nodeId === 'node_software_opps' && out.software_opportunity) {
            currentData.softwarePitch = out.software_opportunity.recommended_product;
            if (out.software_opportunity.pitch_angle) {
              currentData.strengths.push(`High-Value Pitch: ${out.software_opportunity.pitch_angle}`);
            }
          }

          if (nodeId === 'node_report_synthesis' && out.report) {
            currentData.overallScore = out.report.aesthetic_score || 80;
          }

          setAuditResult({ ...currentData });
        }

        if (eventType === 'node_error') {
          setErrorMessage(`Audit step failed: ${payload.error || 'Unknown error'}`);
          setIsAuditing(false);
          eventSource.close();
        }

        if (eventType === 'workflow_complete') {
          setIsAuditing(false);
          eventSource.close();
        }
      } catch (e) {
        console.warn('Error parsing SSE event:', e);
      }
    };

    eventSource.onerror = () => {
      setErrorMessage('Workflow stream interrupted or failed to connect to backend.');
      setIsAuditing(false);
      eventSource.close();
    };
  };

  return (
    <div className="space-y-6">
      {/* Workflow DAG for Brand Audit */}
      <WorkflowGraph
        currentWorkflowId="brand-audit"
        isRunning={isAuditing}
        onRunToggle={() => {
          if (isAuditing) setIsAuditing(false);
          else handleRunAudit();
        }}
        targetInput={brandInput}
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

      {/* Audit Trigger Card */}
      <div className="panel p-5">
        <div className="flex items-center gap-2 mb-3">
          <FileSearch className="w-4 h-4 text-accent" />
          <h3 className="text-xs font-medium text-ink">
            Brand Intelligence & Deep Reverse-Engineering Audit
          </h3>
        </div>

        <div className="flex flex-col sm:flex-row gap-3">
          <input
            type="text"
            value={brandInput}
            onChange={(e) => setBrandInput(e.target.value)}
            placeholder="Enter brand domain or store handle (e.g. aloyoga.com or glossier)"
            className="flex-1 px-4 py-2 bg-paper-3 border border-rule text-xs text-ink placeholder:text-muted focus-visible:outline-2 focus-visible:outline-focus focus:border-accent transition-colors duration-150"
          />
          <button
            onClick={handleRunAudit}
            disabled={isAuditing}
            className="flex items-center justify-center gap-2 px-5 py-2 text-xs font-medium bg-accent text-accent-ink border border-accent hover:opacity-95 transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <span className="whitespace-nowrap">{isAuditing ? 'Analyzing live brand…' : 'Run brand audit'}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Brand Audit Results Grid */}
      {auditResult ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Scorecard Overview */}
          <div className="panel p-5 space-y-4">
            <div>
              <span className="text-xs text-muted block mb-1">
                Brand composite health ({auditResult.brandName})
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
              {auditResult.followersCount !== undefined && (
                <p className="text-xs text-muted mt-1">
                  Audience:{' '}
                  <span className="text-ink font-mono font-medium">
                    {auditResult.followersVerified
                      ? `${auditResult.followersCount.toLocaleString()} verified followers`
                      : 'Unverified (Login barrier / Private)'}
                  </span>
                </p>
              )}
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
              <div className="flex items-center gap-2 flex-wrap">
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
            {auditResult.softwarePitch && (
              <div className="p-4 bg-accent/10 border border-accent/30">
                <span className="text-[10px] font-mono text-accent uppercase tracking-wider block mb-1">
                  Identified Software Product Hook
                </span>
                <p className="text-xs text-ink font-medium">
                  {auditResult.softwarePitch}
                </p>
              </div>
            )}

            <div>
              <h4 className="text-xs font-medium text-ink mb-2.5 flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-accent" />
                Audited brand strengths & signals
              </h4>
              <div className="space-y-1.5">
                {auditResult.strengths.length > 0 ? (
                  auditResult.strengths.map((str, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-paper-3 border border-rule text-xs text-ink-2 flex items-start gap-2.5"
                    >
                      <span className="w-1.5 h-1.5 bg-accent mt-1.5 shrink-0" />
                      <span>{str}</span>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-muted p-3 bg-paper-3 border border-rule">
                    Evaluating brand copy and storefront signals...
                  </p>
                )}
              </div>
            </div>

            <div>
              <h4 className="text-xs font-medium text-ink mb-2.5 flex items-center gap-2">
                <TrendingUp className="w-3.5 h-3.5 text-accent-2" />
                Strategic bottlenecks & recommendations
              </h4>
              <div className="space-y-1.5">
                {auditResult.weaknesses.length > 0 ? (
                  auditResult.weaknesses.map((w, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-paper-3 border border-rule text-xs text-ink-2 flex items-start gap-2.5"
                    >
                      <span className="w-1.5 h-1.5 bg-accent-2 mt-1.5 shrink-0" />
                      <span>{w}</span>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-muted p-3 bg-paper-3 border border-rule">
                    No critical bottlenecks flagged during current inspection pass.
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="panel p-12 text-center text-muted">
          <FileSearch className="w-8 h-8 text-muted mx-auto mb-3 opacity-60" />
          <h4 className="text-sm font-medium text-ink mb-1">No brand audit loaded</h4>
          <p className="text-xs text-muted max-w-md mx-auto">
            Enter any target brand domain (e.g. <code className="font-mono text-accent">aloyoga.com</code>) or handle above and click &ldquo;Run brand audit&rdquo; to execute a live reverse-engineering analysis.
          </p>
        </div>
      )}
    </div>
  );
}
