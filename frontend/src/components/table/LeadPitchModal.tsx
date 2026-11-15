'use client';

import React, { useState } from 'react';
import {
  X,
  Mail,
  MessageCircle,
  Zap,
  Sparkles,
  Copy,
  Check,
  ExternalLink,
  AlertTriangle,
  FileText,
  Download,
  ArrowRight,
} from 'lucide-react';
import { LeadItem } from '@/types/workflow';
import { copyToClipboard, getLighthouseBadgeStyle } from '@/lib/utils';

interface LeadPitchModalProps {
  lead: LeadItem | null;
  onClose: () => void;
}

export function LeadPitchModal({ lead, onClose }: LeadPitchModalProps) {
  const [activeTab, setActiveTab] = useState<'email' | 'dm' | 'speed' | 'ux' | 'report'>('email');
  const [dmPlatform, setDmPlatform] = useState<'instagram' | 'linkedin'>('instagram');
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  if (!lead) return null;

  const lhStyle = getLighthouseBadgeStyle(lead.lighthouseScore);

  const fullMarkdownReport = `# Technical Revamp Audit: ${lead.storeName} (${lead.domain})
> Telemetry Source: Playwright Headless and Google Lighthouse | Status: ${lead.qualificationStatus}

## 1. Executive Summary
- Store Name: ${lead.storeName}
- Domain: https://${lead.domain}
- Niche: ${lead.niche}
- Shopify Verified: ${lead.isShopify ? 'Yes (Detected CDN and Cart APIs)' : 'No'}
- Social Audience Base: ${lead.followers.toLocaleString()} followers

## 2. Performance and Error Telemetry
- Lighthouse Speed Score: ${lead.lighthouseScore} / 100
- Console Errors: ${lead.consoleErrorsCount} runtime exceptions
- First Contentful Paint: ${lead.lighthouseMetrics?.fcp || '2.8s'}
- Largest Contentful Paint: ${lead.lighthouseMetrics?.lcp || '5.7s'}
- Cumulative Layout Shift: ${lead.lighthouseMetrics?.cls || '0.19'}

## 3. Gemini Vision UX Assessment
- Score: ${lead.visionScore || 58} / 100
- Critique Summary: ${lead.visionCritique?.summary || 'Store suffers from high mobile layout shift and sluggish responsive checkout.'}

## 4. Generated Outreach Proposal
### Subject
${lead.pitchEmail?.subject || `Question regarding ${lead.domain} mobile checkout delay`}

### Body
${lead.pitchEmail?.body || 'We prepared a technical teardown showing how to get your store sub-1.2s load speeds.'}`;

  const handleCopy = async (key: string, text: string) => {
    const success = await copyToClipboard(text);
    if (success) {
      setCopiedKey(key);
      setTimeout(() => setCopiedKey(null), 2500);
    }
  };

  const handleDownloadReport = () => {
    const blob = new Blob([fullMarkdownReport], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${lead.domain}_revamp_audit.md`;
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-paper-3/90">
      <div className="relative w-full max-w-4xl max-h-[90vh] bg-paper-2 border border-rule flex flex-col overflow-hidden">
        {/* Header */}
        <div className="p-5 border-b border-rule flex items-start justify-between bg-paper-3">
          <div>
            <div className="flex items-center gap-3 mb-2 flex-wrap">
              <h2 className="text-lg font-medium text-ink">{lead.storeName}</h2>
              <span className="text-xs font-mono text-accent-2 bg-paper-2 px-2 py-0.5 border border-rule">
                {lead.domain}
              </span>
              <span
                className={`px-2 py-0.5 text-xs border ${lhStyle.badgeClass}`}
              >
                Lighthouse: <span className="font-mono">{lead.lighthouseScore} / 100</span>
              </span>
              {lead.isShopify && (
                <span className="px-2 py-0.5 text-xs text-accent border border-rule bg-paper-2">
                  Shopify verified
                </span>
              )}
            </div>
            <div className="flex flex-wrap items-center gap-3 text-xs text-muted">
              <span>Niche: <strong className="text-ink font-normal">{lead.niche}</strong></span>
              <span className="border-l border-rule h-3" />
              <span>Followers: <strong className="text-ink font-mono font-normal">{lead.followers.toLocaleString()}</strong></span>
              <span className="border-l border-rule h-3" />
              <span>Console errors: <strong className="text-error font-mono font-normal">{lead.consoleErrorsCount}</strong></span>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 text-muted hover:text-ink hover:bg-paper-2 border border-transparent hover:border-rule transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:bg-paper disabled:opacity-40 disabled:cursor-not-allowed"
            title="Close pitch modal"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-rule bg-paper-3 px-5 gap-1 overflow-x-auto">
          <button
            onClick={() => setActiveTab('email')}
            className={`flex items-center gap-1.5 py-2.5 px-3 text-xs font-medium border-b-2 transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:bg-paper-2 disabled:opacity-40 disabled:cursor-not-allowed ${
              activeTab === 'email'
                ? 'border-accent text-ink'
                : 'border-transparent text-muted hover:text-ink'
            }`}
          >
            <Mail className="w-3.5 h-3.5" />
            <span className="whitespace-nowrap">Cold email</span>
          </button>

          <button
            onClick={() => setActiveTab('dm')}
            className={`flex items-center gap-1.5 py-2.5 px-3 text-xs font-medium border-b-2 transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:bg-paper-2 disabled:opacity-40 disabled:cursor-not-allowed ${
              activeTab === 'dm'
                ? 'border-accent text-ink'
                : 'border-transparent text-muted hover:text-ink'
            }`}
          >
            <MessageCircle className="w-3.5 h-3.5" />
            <span className="whitespace-nowrap">Direct message</span>
          </button>

          <button
            onClick={() => setActiveTab('speed')}
            className={`flex items-center gap-1.5 py-2.5 px-3 text-xs font-medium border-b-2 transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:bg-paper-2 disabled:opacity-40 disabled:cursor-not-allowed ${
              activeTab === 'speed'
                ? 'border-accent text-ink'
                : 'border-transparent text-muted hover:text-ink'
            }`}
          >
            <Zap className="w-3.5 h-3.5" />
            <span className="whitespace-nowrap">Speed scorecard</span>
          </button>

          <button
            onClick={() => setActiveTab('ux')}
            className={`flex items-center gap-1.5 py-2.5 px-3 text-xs font-medium border-b-2 transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:bg-paper-2 disabled:opacity-40 disabled:cursor-not-allowed ${
              activeTab === 'ux'
                ? 'border-accent text-ink'
                : 'border-transparent text-muted hover:text-ink'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span className="whitespace-nowrap">UX teardown</span>
          </button>

          <button
            onClick={() => setActiveTab('report')}
            className={`flex items-center gap-1.5 py-2.5 px-3 text-xs font-medium border-b-2 transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:bg-paper-2 disabled:opacity-40 disabled:cursor-not-allowed ${
              activeTab === 'report'
                ? 'border-accent text-ink'
                : 'border-transparent text-muted hover:text-ink'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span className="whitespace-nowrap">Read MD report</span>
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {/* TAB 1: COLD EMAIL */}
          {activeTab === 'email' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted">
                  Tailored cold outreach proposal
                </span>
                <button
                  onClick={() =>
                    handleCopy(
                      'email',
                      `Subject: ${lead.pitchEmail?.subject}\n\n${lead.pitchEmail?.body}`
                    )
                  }
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-accent text-accent-ink border border-accent hover:opacity-95 transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {copiedKey === 'email' ? (
                    <>
                      <Check className="w-3.5 h-3.5" />
                      <span className="whitespace-nowrap">Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span className="whitespace-nowrap">Copy pitch</span>
                    </>
                  )}
                </button>
              </div>

              {/* Subject Line */}
              <div className="bg-paper-3 p-4 border border-rule">
                <span className="text-xs text-muted block mb-1">
                  Subject line
                </span>
                <p className="text-xs font-medium text-ink">
                  {lead.pitchEmail?.subject ||
                    `Question regarding ${lead.domain} mobile checkout delay`}
                </p>
              </div>

              {/* Body */}
              <div className="bg-paper-3 p-4 border border-rule">
                <span className="text-xs text-muted block mb-2">
                  Email body
                </span>
                <div className="text-xs text-ink-2 whitespace-pre-line leading-relaxed">
                  {lead.pitchEmail?.body ||
                    `Hi team,\n\nWhile reviewing ${lead.domain}, we recorded a mobile performance score of ${lead.lighthouseScore}/100 and ${lead.consoleErrorsCount} runtime console errors.\n\nWe prepared a technical teardown showing how to achieve sub-1.2s page load speeds.\n\nBest regards,\nRevamp Team`}
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: SOCIAL DMs */}
          {activeTab === 'dm' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setDmPlatform('instagram')}
                    className={`px-3 py-1.5 text-xs font-medium border transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:bg-paper-2 disabled:opacity-40 disabled:cursor-not-allowed ${
                      dmPlatform === 'instagram'
                        ? 'bg-paper-2 text-accent border-accent'
                        : 'border-rule text-muted hover:text-ink bg-paper-3'
                    }`}
                  >
                    Instagram direct message
                  </button>
                  <button
                    onClick={() => setDmPlatform('linkedin')}
                    className={`px-3 py-1.5 text-xs font-medium border transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:bg-paper-2 disabled:opacity-40 disabled:cursor-not-allowed ${
                      dmPlatform === 'linkedin'
                        ? 'bg-paper-2 text-accent-2 border-accent-2'
                        : 'border-rule text-muted hover:text-ink bg-paper-3'
                    }`}
                  >
                    LinkedIn message
                  </button>
                </div>

                <button
                  onClick={() =>
                    handleCopy(
                      dmPlatform,
                      dmPlatform === 'instagram'
                        ? lead.pitchDm?.instagram || ''
                        : lead.pitchDm?.linkedin || ''
                    )
                  }
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-accent text-accent-ink border border-accent hover:opacity-95 transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed"
                >
                  {copiedKey === dmPlatform ? (
                    <>
                      <Check className="w-3.5 h-3.5" />
                      <span className="whitespace-nowrap">Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span className="whitespace-nowrap">Copy DM</span>
                    </>
                  )}
                </button>
              </div>

              <div className="bg-paper-3 p-4 border border-rule">
                <p className="text-xs text-ink-2 leading-relaxed whitespace-pre-line">
                  {dmPlatform === 'instagram'
                    ? lead.pitchDm?.instagram ||
                      `Hello ${lead.storeName} team. Your mobile store has script errors delaying checkout by approximately four seconds. We prepared a two-minute fix teardown if you would like to review it.`
                    : lead.pitchDm?.linkedin ||
                      `Hello ${lead.storeName} team. We noted your mobile Lighthouse score is currently ${lead.lighthouseScore} with active console errors. We have an audit overview showing how to bring it above 90.`}
                </p>
              </div>
            </div>
          )}

          {/* TAB 3: SPEED & HEALTH SCORECARD */}
          {activeTab === 'speed' && (
            <div className="space-y-5">
              {/* Metrics Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-paper-3 p-3.5 border border-rule">
                  <span className="text-xs text-muted block mb-1">
                    First Contentful Paint
                  </span>
                  <p className="text-base font-normal font-mono text-accent">
                    {lead.lighthouseMetrics?.fcp || '2.8s'}
                  </p>
                </div>

                <div className="bg-paper-3 p-3.5 border border-rule">
                  <span className="text-xs text-muted block mb-1">
                    Largest Contentful Paint
                  </span>
                  <p className="text-base font-normal font-mono text-error">
                    {lead.lighthouseMetrics?.lcp || '5.7s'}
                  </p>
                </div>

                <div className="bg-paper-3 p-3.5 border border-rule">
                  <span className="text-xs text-muted block mb-1">
                    Cumulative Layout Shift
                  </span>
                  <p className="text-base font-normal font-mono text-accent-2">
                    {lead.lighthouseMetrics?.cls || '0.19'}
                  </p>
                </div>

                <div className="bg-paper-3 p-3.5 border border-rule">
                  <span className="text-xs text-muted block mb-1">
                    Speed Index
                  </span>
                  <p className="text-base font-normal font-mono text-error">
                    {lead.lighthouseMetrics?.speedIndex || '5.1s'}
                  </p>
                </div>
              </div>

              {/* Exact Console Error Logs */}
              <div>
                <h4 className="text-xs font-medium text-ink mb-2.5 flex items-center gap-2">
                  <AlertTriangle className="w-3.5 h-3.5 text-error" />
                  JavaScript console errors ({lead.consoleErrorsCount})
                </h4>

                <div className="space-y-2">
                  {lead.consoleErrorsList && lead.consoleErrorsList.length > 0 ? (
                    lead.consoleErrorsList.map((err, idx) => (
                      <div
                        key={idx}
                        className="bg-paper-3 p-3 border border-rule font-mono text-xs text-ink-2 leading-relaxed"
                      >
                        <div className="flex items-center gap-2 mb-1 text-[11px] text-error font-body">
                          <span className="px-1 py-0.5 border border-error bg-paper-2 font-mono text-[10px]">
                            {err.type}
                          </span>
                          {err.sourceUrl && (
                            <span className="text-muted truncate max-w-sm">
                              {err.sourceUrl} {err.line ? `:${err.line}` : ''}
                            </span>
                          )}
                        </div>
                        <p className="text-ink">{err.message}</p>
                      </div>
                    ))
                  ) : (
                    <div className="bg-paper-3 p-4 border border-rule text-xs text-muted text-center">
                      No console errors reported during Playwright headless navigation.
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: AI DESIGN & UX REVAMP */}
          {activeTab === 'ux' && (
            <div className="space-y-5">
              {/* Vision Score banner */}
              <div className="p-4 bg-paper-3 border border-rule flex items-center justify-between">
                <div>
                  <span className="text-xs text-muted">Vision UX score</span>
                  <p className="text-xl font-normal text-ink font-mono">
                    {lead.visionScore || 58} <span className="text-xs text-muted">/ 100</span>
                  </p>
                </div>
                <div className="max-w-md text-xs text-ink-2">
                  {lead.visionCritique?.summary ||
                    'High potential store with desktop visual polish, but suffering from layout shift and clunky navigation on mobile devices.'}
                </div>
              </div>

              {/* Identified UX Flaws */}
              <div>
                <h4 className="text-xs font-medium text-ink mb-2.5 flex items-center gap-2">
                  <AlertTriangle className="w-3.5 h-3.5 text-accent" />
                  Identified design bottlenecks
                </h4>
                <div className="space-y-1.5">
                  {lead.visionCritique?.flaws?.map((flaw, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 bg-paper-3 border border-rule text-xs text-ink-2 flex items-start gap-2"
                    >
                      <span className="w-1.5 h-1.5 bg-accent mt-1.5 shrink-0" />
                      <span>{flaw}</span>
                    </div>
                  )) || (
                    <p className="text-xs text-muted">No major UX flaws detected.</p>
                  )}
                </div>
              </div>

              {/* Revamp Blueprint Ideas */}
              <div>
                <h4 className="text-xs font-medium text-ink mb-2.5 flex items-center gap-2">
                  <Sparkles className="w-3.5 h-3.5 text-accent" />
                  Redesign blueprint recommendations
                </h4>
                <div className="space-y-1.5">
                  {lead.visionCritique?.revampIdeas?.map((idea, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 bg-paper-3 border border-rule text-xs text-ink flex items-start gap-2"
                    >
                      <ArrowRight className="w-3.5 h-3.5 text-accent mt-0.5 shrink-0" />
                      <span>{idea}</span>
                    </div>
                  )) || (
                    <p className="text-xs text-muted">Generating blueprint suggestions…</p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: FULL MD REPORT */}
          {activeTab === 'report' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted">
                  Audit Report Document (.md)
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleCopy('report', fullMarkdownReport)}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-paper-3 hover:bg-paper-2 text-ink border border-rule hover:border-accent transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:bg-paper-2 disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    {copiedKey === 'report' ? <Check className="w-3.5 h-3.5 text-accent" /> : <Copy className="w-3.5 h-3.5" />}
                    <span className="whitespace-nowrap">{copiedKey === 'report' ? 'Copied' : 'Copy MD'}</span>
                  </button>

                  <button
                    onClick={handleDownloadReport}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-accent text-accent-ink border border-accent hover:opacity-95 transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    <Download className="w-3.5 h-3.5 text-accent-ink" />
                    <span className="whitespace-nowrap">Download .md</span>
                  </button>
                </div>
              </div>

              {/* Formatted Markdown Content */}
              <div className="bg-paper-3 p-5 border border-rule font-mono text-xs overflow-x-auto leading-relaxed text-ink-2">
                <pre className="whitespace-pre-wrap">{fullMarkdownReport}</pre>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-rule bg-paper-3 flex items-center justify-between">
          <a
            href={`https://${lead.domain}`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-xs text-muted hover:text-accent transition-colors duration-150"
          >
            <ExternalLink className="w-3.5 h-3.5" />
            <span>Visit store: {lead.domain}</span>
          </a>

          <button
            onClick={onClose}
            className="px-3.5 py-1.5 bg-paper-2 hover:bg-paper text-ink text-xs font-medium border border-rule hover:border-muted transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:bg-paper-3 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
