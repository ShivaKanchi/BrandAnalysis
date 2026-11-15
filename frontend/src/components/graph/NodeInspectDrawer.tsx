'use client';

import React, { useState } from 'react';
import {
  X,
  Terminal,
  Layers,
  Database,
  Activity,
  CheckCircle2,
  AlertCircle,
  Clock,
  Copy,
  Check,
  FileText,
} from 'lucide-react';
import { WorkflowNodeData } from '@/types/workflow';
import { copyToClipboard } from '@/lib/utils';

interface NodeInspectDrawerProps {
  node: WorkflowNodeData | null;
  onClose: () => void;
}

export function NodeInspectDrawer({ node, onClose }: NodeInspectDrawerProps) {
  const [activeTab, setActiveTab] = useState<'logs' | 'inputs' | 'outputs' | 'metrics'>('logs');
  const [outputView, setOutputView] = useState<'json' | 'md'>('json');
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  if (!node) return null;

  const nodeMarkdownArtifact = `# Step Telemetry Report: ${node.label} (${node.id})
> Execution Status: ${node.status} | Duration: ${node.durationMs || 1240}ms

## 1. Parameters and Target
- Target: ${node.inputParams?.target || 'lumina-skin.com'}
- Pipeline Node: ${node.label}
- Exit Code: 200 OK

## 2. Emitted Telemetry Artifacts
- Shopify Platform Detected: ${(node.outputArtifacts as any)?.isShopify ? 'Yes (Verified)' : 'Pending Verification'}
- Mobile Lighthouse Score: ${(node.outputArtifacts as any)?.lighthouseScore || 38} / 100
- Trapped Console Errors: ${(node.outputArtifacts as any)?.consoleErrors || 7} exceptions
- Audience Follower Base: ${(node.outputArtifacts as any)?.followers?.toLocaleString() || '18,400'} followers

## 3. Recommended Remediation
Step completed cleanly with zero unhandled exceptions. Telemetry passed downstream to pitch synthesizer.`;

  const handleCopy = async (key: string, text: string) => {
    const success = await copyToClipboard(text);
    if (success) {
      setCopiedKey(key);
      setTimeout(() => setCopiedKey(null), 2000);
    }
  };

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-xl bg-paper border-l border-rule flex flex-col transition-transform duration-200 motion-reduce:transition-none">
      {/* Header */}
      <div className="p-4 border-b border-rule flex items-center justify-between bg-paper-2">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h3 className="text-sm font-medium text-ink">{node.label}</h3>
            <span
              className={`px-2 py-0.5 text-[10px] font-mono border ${
                node.status === 'completed'
                  ? 'border-accent text-accent bg-paper-3'
                  : node.status === 'running'
                  ? 'border-accent-2 text-accent-2 bg-paper-3'
                  : node.status === 'error'
                  ? 'border-error text-error bg-paper-3'
                  : 'border-rule text-muted bg-paper-3'
              }`}
            >
              {node.status}
            </span>
          </div>
          <p className="text-xs text-muted">node id: <span className="font-mono">{node.id}</span></p>
        </div>

        <button
          onClick={onClose}
          className="p-1.5 text-muted hover:text-ink hover:bg-paper-3 active:bg-paper border border-transparent hover:border-rule transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus disabled:opacity-40 disabled:cursor-not-allowed"
          title="Close drawer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-rule bg-paper-3 px-4">
        <button
          onClick={() => setActiveTab('logs')}
          className={`flex items-center gap-1.5 py-2.5 px-3 text-xs font-medium border-b-2 transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:bg-paper-2 disabled:opacity-40 disabled:cursor-not-allowed ${
            activeTab === 'logs'
              ? 'border-accent text-ink'
              : 'border-transparent text-muted hover:text-ink'
          }`}
        >
          <Terminal className="w-3.5 h-3.5" />
          <span className="whitespace-nowrap">Logs ({node.logs?.length || 0})</span>
        </button>

        <button
          onClick={() => setActiveTab('inputs')}
          className={`flex items-center gap-1.5 py-2.5 px-3 text-xs font-medium border-b-2 transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:bg-paper-2 disabled:opacity-40 disabled:cursor-not-allowed ${
            activeTab === 'inputs'
              ? 'border-accent text-ink'
              : 'border-transparent text-muted hover:text-ink'
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          <span className="whitespace-nowrap">Inputs</span>
        </button>

        <button
          onClick={() => setActiveTab('outputs')}
          className={`flex items-center gap-1.5 py-2.5 px-3 text-xs font-medium border-b-2 transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:bg-paper-2 disabled:opacity-40 disabled:cursor-not-allowed ${
            activeTab === 'outputs'
              ? 'border-accent text-ink'
              : 'border-transparent text-muted hover:text-ink'
          }`}
        >
          <Database className="w-3.5 h-3.5" />
          <span className="whitespace-nowrap">Artifacts</span>
        </button>

        <button
          onClick={() => setActiveTab('metrics')}
          className={`flex items-center gap-1.5 py-2.5 px-3 text-xs font-medium border-b-2 transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:bg-paper-2 disabled:opacity-40 disabled:cursor-not-allowed ${
            activeTab === 'metrics'
              ? 'border-accent text-ink'
              : 'border-transparent text-muted hover:text-ink'
          }`}
        >
          <Activity className="w-3.5 h-3.5" />
          <span className="whitespace-nowrap">Metrics</span>
        </button>
      </div>

      {/* Content body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {activeTab === 'logs' && (
          <div className="bg-paper-3 p-4 border border-rule text-xs">
            <div className="flex items-center justify-between text-muted mb-3 pb-2 border-b border-rule-2">
              <span className="flex items-center gap-1.5 text-xs text-ink font-body">
                <span className="w-2 h-2 bg-accent signal-live" />
                Execution stream
              </span>
              <button
                onClick={() => handleCopy('logs', (node.logs || []).join('\n'))}
                className="flex items-center gap-1 text-muted hover:text-ink text-xs focus-visible:outline-2 focus-visible:outline-focus active:text-ink disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {copiedKey === 'logs' ? <Check className="w-3 h-3 text-accent" /> : <Copy className="w-3 h-3" />}
                <span>Copy logs</span>
              </button>
            </div>

            {node.logs && node.logs.length > 0 ? (
              <div className="space-y-1.5 font-mono text-ink-2">
                {node.logs.map((line, idx) => (
                  <div key={idx} className="leading-relaxed hover:bg-paper-2 px-1 flex gap-2">
                    <span className="text-muted-2 select-none">[{idx + 1}]</span>
                    <span className={line.includes('ERROR') || line.includes('error') ? 'text-error' : line.includes('SUCCESS') || line.includes('Shopify') ? 'text-accent' : 'text-ink-2'}>
                      {line}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-8 text-center text-muted">
                No logs recorded for this node yet. Trigger the workflow to stream live execution steps.
              </div>
            )}
          </div>
        )}

        {activeTab === 'inputs' && (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs text-muted">
              <span>Input parameters and environment flags</span>
              <button
                onClick={() => handleCopy('inputs', JSON.stringify(node.inputParams || {}, null, 2))}
                className="flex items-center gap-1 text-muted hover:text-ink text-xs focus-visible:outline-2 focus-visible:outline-focus active:text-ink disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {copiedKey === 'inputs' ? <Check className="w-3 h-3 text-accent" /> : <Copy className="w-3 h-3" />}
                <span>Copy JSON</span>
              </button>
            </div>
            <pre className="bg-paper-3 p-4 border border-rule text-xs text-accent-2 font-mono overflow-x-auto leading-relaxed">
              {JSON.stringify(
                node.inputParams || {
                  targetDomain: 'lumina-skin.com',
                  thresholds: { minFollowers: 2500, maxLighthouse: 60, minConsoleErrors: 1 },
                  headlessPlaywright: true,
                  timeoutMs: 30000,
                },
                null,
                2
              )}
            </pre>
          </div>
        )}

        {activeTab === 'outputs' && (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs text-muted flex-wrap gap-2">
              <div className="flex items-center bg-paper-3 border border-rule p-0.5">
                <button
                  onClick={() => setOutputView('json')}
                  className={`px-2.5 py-0.5 text-xs font-medium transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:bg-paper-2 disabled:opacity-40 disabled:cursor-not-allowed ${
                    outputView === 'json'
                      ? 'bg-paper-2 text-accent border border-accent'
                      : 'text-muted hover:text-ink border border-transparent'
                  }`}
                >
                  <span className="whitespace-nowrap">JSON artifacts</span>
                </button>
                <button
                  onClick={() => setOutputView('md')}
                  className={`flex items-center gap-1 px-2.5 py-0.5 text-xs font-medium transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:bg-paper-2 disabled:opacity-40 disabled:cursor-not-allowed ${
                    outputView === 'md'
                      ? 'bg-paper-2 text-accent border border-accent'
                      : 'text-muted hover:text-ink border border-transparent'
                  }`}
                >
                  <FileText className="w-3 h-3" />
                  <span className="whitespace-nowrap">Read MD report</span>
                </button>
              </div>

              <button
                onClick={() =>
                  handleCopy(
                    'outputs',
                    outputView === 'json'
                      ? JSON.stringify(node.outputArtifacts || {}, null, 2)
                      : nodeMarkdownArtifact
                  )
                }
                className="flex items-center gap-1 text-muted hover:text-ink text-xs focus-visible:outline-2 focus-visible:outline-focus active:text-ink disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {copiedKey === 'outputs' ? <Check className="w-3 h-3 text-accent" /> : <Copy className="w-3 h-3" />}
                <span>{outputView === 'json' ? 'Copy JSON' : 'Copy MD'}</span>
              </button>
            </div>

            {outputView === 'json' ? (
              <pre className="bg-paper-3 p-4 border border-rule text-xs text-accent font-mono overflow-x-auto leading-relaxed">
                {JSON.stringify(
                  node.outputArtifacts || {
                    isShopify: true,
                    lighthouseScore: 38,
                    consoleErrors: 7,
                    followers: 18400,
                    qualificationStatus: 'Qualified',
                  },
                  null,
                  2
                )}
              </pre>
            ) : (
              <div className="bg-paper-3 p-4 border border-rule text-xs font-mono text-ink-2 overflow-x-auto leading-relaxed">
                <pre className="whitespace-pre-wrap">{nodeMarkdownArtifact}</pre>
              </div>
            )}
          </div>
        )}

        {activeTab === 'metrics' && (
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-paper-2 p-3.5 border border-rule">
              <span className="text-xs text-muted flex items-center gap-1 mb-1">
                <Clock className="w-3.5 h-3.5 text-accent" />
                Execution duration
              </span>
              <p className="text-base font-normal text-ink font-mono">
                {node.durationMs ? `${node.durationMs}ms` : '1240ms'}
              </p>
            </div>

            <div className="bg-paper-2 p-3.5 border border-rule">
              <span className="text-xs text-muted flex items-center gap-1 mb-1">
                <CheckCircle2 className="w-3.5 h-3.5 text-accent" />
                Exit status
              </span>
              <p className="text-base font-normal text-accent font-mono">200 OK</p>
            </div>

            <div className="bg-paper-2 p-3.5 border border-rule col-span-2">
              <span className="text-xs text-muted mb-1 block">Subscribed stream node</span>
              <p className="text-xs text-ink">
                <code>backend.workflows.shopify_revamp.{node.id}</code>
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-rule bg-paper-2 flex items-center justify-between text-xs text-muted">
        <span className="text-xs">
          EventStream: <code className="font-mono text-ink text-xs">/api/workflows/run</code>
        </span>
        <button
          onClick={onClose}
          className="px-3 py-1 bg-paper-3 hover:bg-paper text-ink border border-rule hover:border-muted text-xs transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:bg-paper-2 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Dismiss
        </button>
      </div>
    </div>
  );
}
