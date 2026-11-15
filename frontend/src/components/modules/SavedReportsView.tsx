'use client';

import React, { useState, useEffect } from 'react';
import {
  Archive,
  Download,
  Calendar,
  Eye,
  FileText,
  AlertCircle,
  X,
} from 'lucide-react';
import { MarkdownReaderModal } from './MarkdownReaderModal';

interface SavedReport {
  id: string;
  title: string;
  domain: string;
  type: string;
  format: string;
  generatedAt: string;
  fileSize: string;
  summary: string;
  content: string;
}

export function SavedReportsView() {
  const [reports, setReports] = useState<SavedReport[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [activeReportForView, setActiveReportForView] = useState<SavedReport | null>(null);

  const fetchReports = () => {
    setIsLoading(true);
    setErrorMessage(null);
    fetch('/api/reports')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}: Failed to fetch reports`);
        return res.json();
      })
      .then((data) => {
        if (Array.isArray(data)) {
          setReports(data);
        } else {
          setReports([]);
        }
      })
      .catch((err) => {
        console.error('Error fetching reports:', err);
        setErrorMessage(err.message || 'Could not load saved reports');
      })
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleDownload = (report: SavedReport) => {
    const blob = new Blob([report.content], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${report.domain || 'report'}_audit.${(report.format || 'md').toLowerCase()}`;
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="panel p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="p-1.5 border border-rule bg-paper-3 text-accent">
            <Archive className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-medium text-ink">
              Intelligence Index & Saved Audit Reports
            </h3>
            <p className="text-xs text-muted">
              Persisted technical audits, pitch decks, and exported client intelligence records.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 text-xs">
          <span className="text-muted">
            Archived reports: <strong className="font-mono text-accent font-normal">{reports.length}</strong>
          </span>
          <button
            onClick={fetchReports}
            className="px-2.5 py-1 bg-paper-3 hover:bg-paper-2 border border-rule text-xs text-muted hover:text-ink transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

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

      {/* Reports Grid */}
      {isLoading ? (
        <div className="panel p-12 text-center text-muted">
          <p className="text-xs">Loading archived intelligence reports...</p>
        </div>
      ) : reports.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {reports.map((report) => (
            <div
              key={report.id}
              className="panel p-4 flex flex-col justify-between space-y-3 hover:border-muted transition-colors duration-150"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs text-muted">
                  <span className="px-2 py-0.5 border border-rule bg-paper-3 text-ink text-xs font-medium">
                    {report.type}
                  </span>
                  <div className="flex items-center gap-1.5 text-muted">
                    <span className="font-mono text-[10px]">{report.format}</span>
                    <span className="border-l border-rule h-2.5" />
                    <span className="font-mono text-[10px]">{report.fileSize}</span>
                  </div>
                </div>

                <h4 className="text-xs font-medium text-ink leading-snug">
                  {report.title}
                </h4>
                <p className="text-xs text-muted line-clamp-3 leading-relaxed">
                  {report.summary}
                </p>
              </div>

              <div className="pt-3 border-t border-rule-2 flex items-center justify-between text-xs">
                <span className="text-[11px] text-muted font-mono flex items-center gap-1">
                  <Calendar className="w-3 h-3 text-muted" />
                  {report.generatedAt ? new Date(report.generatedAt).toLocaleDateString() : 'Recent'}
                </span>

                <div className="flex items-center gap-1.5">
                  <button
                    onClick={() => setActiveReportForView(report)}
                    className="flex items-center gap-1 px-2.5 py-1 bg-paper-3 hover:bg-paper-2 text-accent border border-rule hover:border-accent text-xs font-medium transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:bg-paper-2"
                  >
                    <Eye className="w-3 h-3 text-accent" />
                    <span className="whitespace-nowrap">Read MD</span>
                  </button>

                  <button
                    onClick={() => handleDownload(report)}
                    className="flex items-center gap-1 px-2.5 py-1 bg-paper-3 hover:bg-paper-2 text-ink border border-rule hover:border-muted text-xs font-medium transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:bg-paper-2"
                  >
                    <Download className="w-3 h-3 text-muted" />
                    <span className="whitespace-nowrap">Download</span>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="panel p-12 text-center text-muted">
          <FileText className="w-8 h-8 text-muted mx-auto mb-3 opacity-60" />
          <h4 className="text-sm font-medium text-ink mb-1">No archived reports found</h4>
          <p className="text-xs text-muted max-w-md mx-auto">
            Audit a brand or run the Store Lead Harvester pipeline to generate and persist actionable client intelligence reports.
          </p>
        </div>
      )}

      {/* Markdown Reader Modal */}
      {activeReportForView && (
        <MarkdownReaderModal
          isOpen={true}
          onClose={() => setActiveReportForView(null)}
          title={activeReportForView.title}
          domain={activeReportForView.domain}
          date={activeReportForView.generatedAt}
          markdownContent={activeReportForView.content}
        />
      )}
    </div>
  );
}
