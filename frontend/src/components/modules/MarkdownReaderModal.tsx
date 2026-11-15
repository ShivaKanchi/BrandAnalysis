'use client';

import React, { useState } from 'react';
import {
  X,
  FileText,
  Code,
  Copy,
  Check,
  Download,
  ExternalLink,
} from 'lucide-react';
import { copyToClipboard } from '@/lib/utils';

interface MarkdownReaderModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  domain?: string;
  date?: string;
  markdownContent: string;
}

export function MarkdownReaderModal({
  isOpen,
  onClose,
  title,
  domain,
  date,
  markdownContent,
}: MarkdownReaderModalProps) {
  const [viewMode, setViewMode] = useState<'rendered' | 'source'>('rendered');
  const [isCopied, setIsCopied] = useState(false);

  if (!isOpen) return null;

  const handleCopy = async () => {
    const success = await copyToClipboard(markdownContent);
    if (success) {
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    }
  };

  const handleDownload = () => {
    const blob = new Blob([markdownContent], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${(domain || 'report').replace(/[^a-zA-Z0-9.-]/g, '_')}_audit.md`;
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  const lines = markdownContent.split('\n');

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-paper-3/90">
      <div className="relative w-full max-w-4xl max-h-[90vh] bg-paper-2 border border-rule flex flex-col overflow-hidden">
        {/* Modal Header */}
        <div className="p-4 border-b border-rule flex items-start justify-between bg-paper-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="px-1.5 py-0.5 border border-rule bg-paper-2 text-accent text-[11px]">
                .md
              </span>
              <h2 className="text-sm font-medium text-ink">{title}</h2>
              {domain && (
                <span className="text-xs font-mono text-accent-2">
                  {domain}
                </span>
              )}
            </div>
            {date && (
              <p className="text-xs text-muted">
                Generated: {date}
              </p>
            )}
          </div>

          <div className="flex items-center gap-2">
            {/* View Mode Toggle */}
            <div className="flex items-center bg-paper-2 border border-rule p-0.5">
              <button
                onClick={() => setViewMode('rendered')}
                className={`flex items-center gap-1 px-2.5 py-1 text-xs font-medium transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:bg-paper-3 disabled:opacity-40 disabled:cursor-not-allowed ${
                  viewMode === 'rendered'
                    ? 'bg-paper-3 text-accent border border-accent'
                    : 'text-muted hover:text-ink border border-transparent'
                }`}
              >
                <FileText className="w-3.5 h-3.5" />
                <span className="whitespace-nowrap">Reader</span>
              </button>
              <button
                onClick={() => setViewMode('source')}
                className={`flex items-center gap-1 px-2.5 py-1 text-xs font-medium transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:bg-paper-3 disabled:opacity-40 disabled:cursor-not-allowed ${
                  viewMode === 'source'
                    ? 'bg-paper-3 text-accent border border-accent'
                    : 'text-muted hover:text-ink border border-transparent'
                }`}
              >
                <Code className="w-3.5 h-3.5" />
                <span className="whitespace-nowrap">Raw MD</span>
              </button>
            </div>

            <button
              onClick={handleCopy}
              className="flex items-center gap-1 px-2.5 py-1 bg-paper-3 hover:bg-paper text-ink border border-rule hover:border-muted text-xs font-medium transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:bg-paper-2 disabled:opacity-40 disabled:cursor-not-allowed"
              title="Copy markdown text"
            >
              {isCopied ? <Check className="w-3.5 h-3.5 text-accent" /> : <Copy className="w-3.5 h-3.5" />}
              <span className="whitespace-nowrap">{isCopied ? 'Copied' : 'Copy'}</span>
            </button>

            <button
              onClick={handleDownload}
              className="flex items-center gap-1 px-2.5 py-1 bg-paper-3 hover:bg-paper text-ink border border-rule hover:border-muted text-xs font-medium transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:bg-paper-2 disabled:opacity-40 disabled:cursor-not-allowed"
              title="Download file"
            >
              <Download className="w-3.5 h-3.5 text-accent" />
              <span className="whitespace-nowrap">Download</span>
            </button>

            <button
              onClick={onClose}
              className="p-1 text-muted hover:text-ink hover:bg-paper-3 border border-transparent hover:border-rule transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:bg-paper disabled:opacity-40 disabled:cursor-not-allowed"
              title="Close modal"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Modal Content Body */}
        <div className="flex-1 overflow-y-auto p-5">
          {viewMode === 'source' ? (
            <div className="bg-paper-3 p-4 border border-rule font-mono text-xs overflow-x-auto">
              <pre className="text-ink-2 leading-relaxed">
                {lines.map((line, idx) => (
                  <div key={idx} className="flex gap-3 hover:bg-paper-2 px-1">
                    <span className="text-muted-2 select-none w-8 text-right">{idx + 1}</span>
                    <span className="flex-1 whitespace-pre-wrap">{line || ' '}</span>
                  </div>
                ))}
              </pre>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-4 text-xs text-ink-2 leading-relaxed">
              {lines.map((line, idx) => {
                const trimmed = line.trim();

                // Heading 1
                if (trimmed.startsWith('# ')) {
                  return (
                    <h1 key={idx} className="text-lg font-medium text-ink pt-2 pb-1 border-b border-rule">
                      {trimmed.slice(2)}
                    </h1>
                  );
                }
                // Heading 2
                if (trimmed.startsWith('## ')) {
                  return (
                    <h2 key={idx} className="text-sm font-medium text-ink pt-3 pb-1 border-b border-rule-2">
                      {trimmed.slice(3)}
                    </h2>
                  );
                }
                // Heading 3
                if (trimmed.startsWith('### ')) {
                  return (
                    <h3 key={idx} className="text-xs font-medium text-accent pt-2">
                      {trimmed.slice(4)}
                    </h3>
                  );
                }
                // Blockquote
                if (trimmed.startsWith('> ')) {
                  return (
                    <div key={idx} className="p-3 bg-paper-3 border-l-2 border-accent text-xs text-muted">
                      {trimmed.slice(2)}
                    </div>
                  );
                }
                // Bullet item
                if (trimmed.startsWith('- ')) {
                  return (
                    <div key={idx} className="flex items-start gap-2 pl-2">
                      <span className="w-1.5 h-1.5 bg-accent mt-1.5 shrink-0" />
                      <span>{trimmed.slice(2)}</span>
                    </div>
                  );
                }
                // Horizontal divider
                if (trimmed === '---' || trimmed === '***') {
                  return <hr key={idx} className="border-rule my-3" />;
                }
                // Empty line
                if (!trimmed) {
                  return <div key={idx} className="h-2" />;
                }
                // Default paragraph
                return (
                  <p key={idx} className="leading-relaxed">
                    {line}
                  </p>
                );
              })}
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-3 border-t border-rule bg-paper-3 flex items-center justify-between text-xs text-muted">
          <span>Markdown Document Viewer</span>
          <button
            onClick={onClose}
            className="px-3 py-1 bg-paper-2 hover:bg-paper text-ink border border-rule hover:border-muted text-xs transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:bg-paper-3 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Dismiss
          </button>
        </div>
      </div>
    </div>
  );
}
