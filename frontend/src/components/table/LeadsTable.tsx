'use client';

import React, { useState, useMemo } from 'react';
import {
  Search,
  Download,
  Copy,
  Check,
  ExternalLink,
  ShoppingBag,
  ArrowUpDown,
  FileText,
} from 'lucide-react';
import { LeadItem } from '@/types/workflow';
import {
  formatFollowers,
  getLighthouseBadgeStyle,
  getStatusBadgeStyle,
  copyToClipboard,
} from '@/lib/utils';
import { LeadPitchModal } from './LeadPitchModal';

interface LeadsTableProps {
  leads: LeadItem[];
  onExportCsv?: () => void;
}

export function LeadsTable({ leads, onExportCsv }: LeadsTableProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('All');
  const [selectedLeadForPitch, setSelectedLeadForPitch] = useState<LeadItem | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [sortField, setSortField] = useState<'followers' | 'lighthouse' | 'errors'>('errors');
  const [sortAsc, setSortAsc] = useState<boolean>(false);

  const filteredLeads = useMemo(() => {
    return leads.filter((lead) => {
      const matchesSearch =
        lead.domain.toLowerCase().includes(searchTerm.toLowerCase()) ||
        lead.storeName.toLowerCase().includes(searchTerm.toLowerCase()) ||
        lead.niche.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesStatus =
        statusFilter === 'All' || lead.qualificationStatus === statusFilter;

      return matchesSearch && matchesStatus;
    });
  }, [leads, searchTerm, statusFilter]);

  const sortedLeads = useMemo(() => {
    return [...filteredLeads].sort((a, b) => {
      let valA = 0;
      let valB = 0;
      if (sortField === 'followers') {
        valA = a.followers;
        valB = b.followers;
      } else if (sortField === 'lighthouse') {
        valA = a.lighthouseScore;
        valB = b.lighthouseScore;
      } else if (sortField === 'errors') {
        valA = a.consoleErrorsCount;
        valB = b.consoleErrorsCount;
      }
      return sortAsc ? valA - valB : valB - valA;
    });
  }, [filteredLeads, sortField, sortAsc]);

  const handleCopySummary = async (lead: LeadItem) => {
    const summary = `Store: ${lead.storeName} (${lead.domain})
Niche: ${lead.niche}
Shopify: ${lead.isShopify ? 'Yes' : 'No'}
Followers: ${lead.followers.toLocaleString()}
Lighthouse Performance: ${lead.lighthouseScore}/100
Console Errors: ${lead.consoleErrorsCount}`;

    const success = await copyToClipboard(summary);
    if (success) {
      setCopiedId(lead.id);
      setTimeout(() => setCopiedId(null), 2000);
    }
  };

  const handleExportCsvInternal = () => {
    if (onExportCsv) {
      onExportCsv();
      return;
    }

    const headers = [
      'Domain',
      'Store Name',
      'Niche',
      'Followers',
      'Is Shopify',
      'Lighthouse Score',
      'Console Errors',
      'Qualification Status',
      'Pitch Subject',
    ];

    const rows = sortedLeads.map((l) => [
      l.domain,
      `"${l.storeName.replace(/"/g, '""')}"`,
      `"${l.niche}"`,
      l.followers,
      l.isShopify ? 'TRUE' : 'FALSE',
      l.lighthouseScore,
      l.consoleErrorsCount,
      l.qualificationStatus,
      `"${(l.pitchEmail?.subject || '').replace(/"/g, '""')}"`,
    ]);

    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `shopify_revamp_leads_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  const handleSort = (field: 'followers' | 'lighthouse' | 'errors') => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  return (
    <div className="w-full space-y-4">
      {/* Top Filter & Action Bar */}
      <div className="panel p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* Search Input */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search stores by domain, brand name, or niche"
            className="w-full pl-10 pr-4 py-2 bg-paper-3 border border-rule text-xs text-ink placeholder:text-muted focus-visible:outline-2 focus-visible:outline-focus focus:border-accent transition-colors duration-150"
          />
        </div>

        {/* Status Filter Tabs */}
        <div className="flex items-center gap-1 flex-wrap">
          {['All', 'Qualified', 'Pending', 'Rejected', 'Non-Shopify'].map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-3 py-1.5 text-xs font-medium border transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:bg-paper-2 disabled:opacity-40 disabled:cursor-not-allowed ${
                statusFilter === status
                  ? 'border-accent bg-paper-2 text-accent'
                  : 'border-rule text-muted hover:text-ink bg-paper-3 hover:bg-paper-2'
              }`}
            >
              {status}
            </button>
          ))}
        </div>

        {/* CSV Export Button */}
        <button
          onClick={handleExportCsvInternal}
          className="flex items-center justify-center gap-2 px-4 py-2 text-xs font-medium bg-paper-3 hover:bg-paper-2 text-ink border border-rule hover:border-accent transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:bg-paper-2 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <Download className="w-3.5 h-3.5 text-accent" />
          <span className="whitespace-nowrap">Export CSV ({sortedLeads.length})</span>
        </button>
      </div>

      {/* Main Table */}
      <div className="panel overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-paper-3 text-muted border-b border-rule">
              <tr>
                <th className="py-3 px-4 font-normal">Domain and store</th>
                <th className="py-3 px-4 font-normal cursor-pointer" onClick={() => handleSort('followers')}>
                  <div className="flex items-center gap-1.5 hover:text-ink">
                    <span>Followers</span>
                    <ArrowUpDown className="w-3 h-3 text-muted" />
                  </div>
                </th>
                <th className="py-3 px-4 font-normal cursor-pointer" onClick={() => handleSort('lighthouse')}>
                  <div className="flex items-center gap-1.5 hover:text-ink">
                    <span>Lighthouse score</span>
                    <ArrowUpDown className="w-3 h-3 text-muted" />
                  </div>
                </th>
                <th className="py-3 px-4 font-normal cursor-pointer" onClick={() => handleSort('errors')}>
                  <div className="flex items-center gap-1.5 hover:text-ink">
                    <span>Console errors</span>
                    <ArrowUpDown className="w-3 h-3 text-muted" />
                  </div>
                </th>
                <th className="py-3 px-4 font-normal">Status</th>
                <th className="py-3 px-4 font-normal text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-rule-2 text-ink-2">
              {sortedLeads.length > 0 ? (
                sortedLeads.map((lead) => {
                  const lhStyle = getLighthouseBadgeStyle(lead.lighthouseScore);
                  const statusStyle = getStatusBadgeStyle(lead.qualificationStatus);

                  return (
                    <tr
                      key={lead.id}
                      className="hover:bg-paper-3 transition-colors duration-150 group"
                    >
                      {/* Domain & Store */}
                      <td className="py-3.5 px-4">
                        <div className="flex items-center gap-2">
                          <div>
                            <div className="flex items-center gap-1.5">
                              <span className="font-medium text-ink">
                                {lead.storeName}
                              </span>
                              {lead.isShopify && (
                                <span title="Verified Shopify Store">
                                  <ShoppingBag className="w-3.5 h-3.5 text-accent" />
                                </span>
                              )}
                            </div>
                            <div className="flex items-center gap-2 mt-0.5">
                              <a
                                href={`https://${lead.domain}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-[11px] font-mono text-accent-2 hover:underline flex items-center gap-1"
                              >
                                {lead.domain}
                                <ExternalLink className="w-2.5 h-2.5 opacity-60" />
                              </a>
                              <span className="text-[11px] text-muted">{lead.niche}</span>
                            </div>
                          </div>
                        </div>
                      </td>

                      {/* Followers */}
                      <td className="py-3.5 px-4 font-mono font-normal text-ink">
                        {formatFollowers(lead.followers)}
                      </td>

                      {/* Lighthouse Score */}
                      <td className="py-3.5 px-4">
                        <div
                          className={`inline-flex items-center gap-1.5 px-2 py-0.5 text-xs font-mono ${lhStyle.badgeClass}`}
                        >
                          <span className={`w-1.5 h-1.5 ${lhStyle.dotClass}`} />
                          <span>{lead.lighthouseScore} / 100</span>
                        </div>
                      </td>

                      {/* Console Errors */}
                      <td className="py-3.5 px-4">
                        {lead.consoleErrorsCount > 0 ? (
                          <div className="inline-flex items-center gap-1 px-2 py-0.5 border border-error text-error bg-paper-3 text-xs">
                            <span className="font-mono">{lead.consoleErrorsCount}</span>
                            <span>errors</span>
                          </div>
                        ) : (
                          <span className="text-muted text-xs font-mono">0</span>
                        )}
                      </td>

                      {/* Qualification Status */}
                      <td className="py-3.5 px-4">
                        <span
                          className={`px-2 py-0.5 text-xs border ${statusStyle}`}
                        >
                          {lead.qualificationStatus}
                        </span>
                      </td>

                      {/* Actions */}
                      <td className="py-3.5 px-4 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => handleCopySummary(lead)}
                            className="p-1.5 text-muted hover:text-ink hover:bg-paper-3 border border-rule transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:bg-paper-2 disabled:opacity-40 disabled:cursor-not-allowed"
                            title="Copy lead summary"
                          >
                            {copiedId === lead.id ? (
                              <Check className="w-3.5 h-3.5 text-accent" />
                            ) : (
                              <Copy className="w-3.5 h-3.5" />
                            )}
                          </button>

                          <button
                            onClick={() => setSelectedLeadForPitch(lead)}
                            className="flex items-center gap-1 px-3 py-1 text-xs font-medium bg-paper-3 hover:bg-paper-2 text-accent border border-rule hover:border-accent transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:bg-paper-2 disabled:opacity-40 disabled:cursor-not-allowed"
                          >
                            <FileText className="w-3.5 h-3.5 text-accent" />
                            <span className="whitespace-nowrap">Pitch kit</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-muted">
                    No leads found matching your criteria. Try adjusting the search query or status filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pitch Modal */}
      <LeadPitchModal
        lead={selectedLeadForPitch}
        onClose={() => setSelectedLeadForPitch(null)}
      />
    </div>
  );
}
