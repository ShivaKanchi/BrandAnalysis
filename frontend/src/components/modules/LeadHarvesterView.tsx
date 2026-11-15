'use client';

import React, { useState } from 'react';
import {
  Compass,
  MapPin,
  Search,
  ExternalLink,
  Star,
  ArrowRight,
  ShieldCheck,
  Zap,
  Download,
  RotateCcw,
} from 'lucide-react';
import { WorkflowGraph } from '@/components/graph/WorkflowGraph';

interface DiscoveredLead {
  business_name: string;
  category?: string;
  address_or_location?: string;
  website?: string;
  instagram_handle?: string;
  instagram_url?: string;
  maps_url?: string;
  rating?: string;
  review_count?: string;
  phone?: string;
  lead_status?: string;
  lead_intent_score?: 'High Intent' | 'Promising' | 'Low Intent / Ghost';
  authenticity_signals?: string[];
  opportunity_angle?: string;
  is_fresh_lead?: boolean;
}

export function LeadHarvesterView() {
  const [prospects, setProspects] = useState<DiscoveredLead[]>([]);
  const [nicheQuery, setNicheQuery] = useState('Gyms');
  const [locationQuery, setLocationQuery] = useState('Kandivali, Mumbai');
  const [isCrawling, setIsCrawling] = useState(false);
  const [freshOnly, setFreshOnly] = useState(true);
  const [autoExpand, setAutoExpand] = useState(true);
  const [stats, setStats] = useState<{
    scanned: number;
    fresh: number;
    skipped: number;
    highIntent: number;
    totalRegistry: number;
  } | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleHarvest = async () => {
    setIsCrawling(true);
    setErrorMsg(null);

    try {
      const params = new URLSearchParams({
        niche: nicheQuery,
        location: locationQuery,
        limit: '8',
        fresh_only: String(freshOnly),
        auto_expand: String(autoExpand),
      });

      // Try local FastAPI backend, with fallback to relative path
      let res;
      try {
        res = await fetch(`http://localhost:8000/api/harvest?${params.toString()}`);
      } catch {
        res = await fetch(`/api/harvest?${params.toString()}`);
      }

      if (!res.ok) {
        throw new Error(`Server returned HTTP ${res.status}`);
      }

      const data = await res.json();
      if (data.leads && Array.isArray(data.leads)) {
        setProspects(data.leads);
        setStats({
          scanned: data.total_places_scanned || data.leads.length,
          fresh: data.fresh_leads_count || data.leads.length,
          skipped: data.recycled_leads_skipped || 0,
          highIntent: data.high_intent_count || 0,
          totalRegistry: data.total_registry_leads || 0,
        });
      } else {
        throw new Error(data.error || 'Failed to retrieve leads');
      }
    } catch (err: any) {
      console.warn('Harvest request notice:', err);
      setErrorMsg(
        err.message || 'Harvest failed. Make sure the backend API is running at http://localhost:8000'
      );
    } finally {
      setIsCrawling(false);
    }
  };

  const handleExportJSON = () => {
    const blob = new Blob([JSON.stringify(prospects, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `leads_${locationQuery.replace(/[^a-zA-Z0-9]/g, '_')}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Workflow DAG for Lead Harvester */}
      <WorkflowGraph currentWorkflowId="lead-harvester" />

      {/* Harvester Query Box */}
      <div className="panel p-5 space-y-4">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <Compass className="w-4 h-4 text-accent" />
            <h3 className="text-xs font-medium text-ink">
              Lead Harvester & Autonomous Prospecting Engine
            </h3>
          </div>
          <span className="text-[11px] text-muted">
            Continuous deduplication: never pulls existing leads twice
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="relative">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
            <input
              type="text"
              value={nicheQuery}
              onChange={(e) => setNicheQuery(e.target.value)}
              placeholder="Niche (e.g. Specialty Coffee, Dentists, Gyms)"
              className="w-full pl-10 pr-3 py-2 bg-paper-3 border border-rule text-xs text-ink placeholder:text-muted focus-visible:outline-2 focus-visible:outline-focus focus:border-accent transition-colors duration-150"
            />
          </div>

          <div className="relative">
            <MapPin className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
            <input
              type="text"
              value={locationQuery}
              onChange={(e) => setLocationQuery(e.target.value)}
              placeholder="City, locality, or postal code"
              className="w-full pl-10 pr-3 py-2 bg-paper-3 border border-rule text-xs text-ink placeholder:text-muted focus-visible:outline-2 focus-visible:outline-focus focus:border-accent transition-colors duration-150"
            />
          </div>

          <button
            onClick={handleHarvest}
            disabled={isCrawling}
            className="flex items-center justify-center gap-2 px-5 py-2 text-xs font-medium bg-accent text-accent-ink border border-accent hover:opacity-95 transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <span className="whitespace-nowrap">
              {isCrawling ? 'Harvesting fresh leads…' : 'Harvest Fresh Leads'}
            </span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Deduplication & Strategy Toggles */}
        <div className="flex items-center gap-6 pt-1 text-xs text-muted flex-wrap">
          <label className="flex items-center gap-2 cursor-pointer hover:text-ink">
            <input
              type="checkbox"
              checked={freshOnly}
              onChange={(e) => setFreshOnly(e.target.checked)}
              className="rounded border-rule bg-paper-3 text-accent focus:ring-accent"
            />
            <span>✨ Fresh Leads Only (Skip previously harvested)</span>
          </label>

          <label className="flex items-center gap-2 cursor-pointer hover:text-ink">
            <input
              type="checkbox"
              checked={autoExpand}
              onChange={(e) => setAutoExpand(e.target.checked)}
              className="rounded border-rule bg-paper-3 text-accent focus:ring-accent"
            />
            <span>🔄 Auto-Expand Neighborhoods (If top results saturated)</span>
          </label>
        </div>

        {errorMsg && (
          <div className="p-3 bg-error/10 border border-error/30 text-error text-xs rounded">
            {errorMsg}
          </div>
        )}
      </div>

      {/* Discovery Telemetry Stats Row */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="panel p-3">
            <span className="text-[11px] text-muted block">Fresh Leads Found</span>
            <span className="text-lg font-mono font-medium text-accent">{stats.fresh}</span>
          </div>
          <div className="panel p-3">
            <span className="text-[11px] text-muted block">Previously Seen Skipped</span>
            <span className="text-lg font-mono font-medium text-muted">{stats.skipped}</span>
          </div>
          <div className="panel p-3">
            <span className="text-[11px] text-muted block">High-Intent Proof</span>
            <span className="text-lg font-mono font-medium text-emerald-400">{stats.highIntent}</span>
          </div>
          <div className="panel p-3">
            <span className="text-[11px] text-muted block">Total Tracked In Registry</span>
            <span className="text-lg font-mono font-medium text-ink">{stats.totalRegistry}</span>
          </div>
        </div>
      )}

      {/* Discovered Leads List / Table */}
      <div className="panel overflow-hidden">
        <div className="p-3 border-b border-rule flex items-center justify-between bg-paper-3 flex-wrap gap-2">
          <div>
            <h4 className="text-xs font-medium text-ink">
              Discovered Business Leads ({prospects.length})
            </h4>
            <span className="text-[11px] text-muted">
              Qualified by real Google review proof, custom domain status, and conversion bottlenecks
            </span>
          </div>

          {prospects.length > 0 && (
            <button
              onClick={handleExportJSON}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs border border-rule bg-paper text-ink hover:bg-paper-2"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export JSON</span>
            </button>
          )}
        </div>

        {prospects.length === 0 ? (
          <div className="p-12 text-center text-muted text-xs space-y-2">
            <Compass className="w-8 h-8 mx-auto text-muted/50 mb-2" />
            <p className="font-medium text-ink">No leads loaded yet</p>
            <p>Enter a business niche and locality above, then click &quot;Harvest Fresh Leads&quot;.</p>
          </div>
        ) : (
          <div className="divide-y divide-rule">
            {prospects.map((lead, idx) => (
              <div key={idx} className="p-4 hover:bg-paper-2/60 transition-colors space-y-3">
                <div className="flex items-start justify-between gap-4 flex-wrap">
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-xs text-muted">#{idx + 1}</span>
                      <h4 className="font-medium text-sm text-ink">{lead.business_name}</h4>
                      <span
                        className={`px-2 py-0.5 text-[11px] border font-medium ${
                          lead.lead_intent_score === 'High Intent'
                            ? 'border-emerald-500/40 text-emerald-400 bg-emerald-500/10'
                            : lead.lead_intent_score === 'Promising'
                            ? 'border-amber-500/40 text-amber-300 bg-amber-500/10'
                            : 'border-rule text-muted bg-paper-3'
                        }`}
                      >
                        {lead.lead_intent_score || 'Promising'}
                      </span>
                      {lead.is_fresh_lead && (
                        <span className="px-2 py-0.5 text-[11px] border border-accent/40 text-accent bg-accent/10">
                          ✨ Fresh Lead
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-3 text-xs text-muted mt-1 flex-wrap">
                      <span className="inline-flex items-center gap-1">
                        <MapPin className="w-3 h-3" />
                        {lead.address_or_location || locationQuery}
                      </span>
                      <span className="inline-flex items-center gap-1 text-accent">
                        <Star className="w-3 h-3 fill-current" />
                        {lead.rating || 'N/A'} ({lead.review_count || '0'} reviews)
                      </span>
                      {lead.phone && <span className="font-mono">📞 {lead.phone}</span>}
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {lead.instagram_handle && (
                      <a
                        href={lead.instagram_url || `https://instagram.com/${lead.instagram_handle}/`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-2.5 py-1 text-xs font-mono text-pink-400 bg-pink-500/10 border border-pink-500/30 hover:underline"
                      >
                        @{lead.instagram_handle}
                      </a>
                    )}
                    {lead.website ? (
                      <a
                        href={lead.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-2.5 py-1 text-xs text-accent-2 border border-rule bg-paper-3 hover:underline inline-flex items-center gap-1"
                      >
                        <span>Visit Site</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    ) : (
                      <span className="px-2.5 py-1 text-xs text-red-400 bg-red-500/10 border border-red-500/30">
                        No Website (Funnel Leak)
                      </span>
                    )}
                  </div>
                </div>

                {/* Authenticity Signals Badges */}
                {lead.authenticity_signals && lead.authenticity_signals.length > 0 && (
                  <div className="flex items-center gap-1.5 flex-wrap pt-1">
                    {lead.authenticity_signals.map((sig, sIdx) => (
                      <span
                        key={sIdx}
                        className="px-2 py-0.5 text-[11px] bg-paper-3 border border-rule text-ink-2"
                      >
                        {sig}
                      </span>
                    ))}
                  </div>
                )}

                {/* Cold Outreach Diagnostic Pitch Hook */}
                {lead.opportunity_angle && (
                  <div className="p-2.5 bg-accent/5 border-l-2 border-accent text-xs text-ink-2 rounded-r">
                    <span className="font-medium text-accent">Targeted Pitch Angle: </span>
                    {lead.opportunity_angle}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
