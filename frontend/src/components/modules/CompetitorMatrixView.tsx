'use client';

import React, { useState } from 'react';
import {
  Grid,
} from 'lucide-react';
import { WorkflowGraph } from '@/components/graph/WorkflowGraph';

interface CompetitorRow {
  brand: string;
  domain: string;
  pricePoint: string;
  followers: string;
  estTraffic: string;
  activeAdsCount: number;
  mobileSpeed: number;
  uniqueAngle: string;
  isMainTarget?: boolean;
}

const INITIAL_COMPETITORS: CompetitorRow[] = [
  {
    brand: 'Lumina Organic',
    domain: 'lumina-skin.com',
    pricePoint: '$42 - $88',
    followers: '18.4k',
    estTraffic: '65k / mo',
    activeAdsCount: 14,
    mobileSpeed: 38,
    uniqueAngle: '100% cold-pressed organic botanicals',
    isMainTarget: true,
  },
  {
    brand: 'Herbivore Botanicals',
    domain: 'herbivorebotanicals.com',
    pricePoint: '$48 - $94',
    followers: '540k',
    estTraffic: '420k / mo',
    activeAdsCount: 42,
    mobileSpeed: 74,
    uniqueAngle: 'Pastel packaging and Sephora retail reach',
  },
  {
    brand: 'Biossance',
    domain: 'biossance.com',
    pricePoint: '$52 - $110',
    followers: '310k',
    estTraffic: '890k / mo',
    activeAdsCount: 68,
    mobileSpeed: 68,
    uniqueAngle: 'Biotechnology squalane and clean clinical trials',
  },
  {
    brand: 'True Botanicals',
    domain: 'truebotanicals.com',
    pricePoint: '$65 - $140',
    followers: '280k',
    estTraffic: '350k / mo',
    activeAdsCount: 36,
    mobileSpeed: 62,
    uniqueAngle: 'MADE SAFE certified anti-aging',
  },
];

export function CompetitorMatrixView() {
  const [competitors, setCompetitors] = useState<CompetitorRow[]>(INITIAL_COMPETITORS);
  const [newCompetitor, setNewCompetitor] = useState('');

  const handleAdd = () => {
    if (!newCompetitor.trim()) return;
    setCompetitors((prev) => [
      ...prev,
      {
        brand: newCompetitor,
        domain: `${newCompetitor.toLowerCase().replace(/\s+/g, '')}.com`,
        pricePoint: '$40 - $80',
        followers: '25.0k',
        estTraffic: '80k / mo',
        activeAdsCount: 12,
        mobileSpeed: 55,
        uniqueAngle: 'Specialty formulation',
      },
    ]);
    setNewCompetitor('');
  };

  return (
    <div className="space-y-6">
      {/* Workflow DAG for Competitor Matrix */}
      <WorkflowGraph currentWorkflowId="competitor-matrix" />

      {/* Header Info Banner */}
      <div className="panel p-5 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Grid className="w-4 h-4 text-accent" />
            <h3 className="text-xs font-medium text-ink">
              Competitor intelligence and positioning matrix
            </h3>
          </div>
          <p className="text-xs text-muted">
            Side-by-side performance, active ad inventory, pricing tiers, and audience scale.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <input
            type="text"
            value={newCompetitor}
            onChange={(e) => setNewCompetitor(e.target.value)}
            placeholder="Add competitor domain"
            className="px-3 py-1.5 bg-paper-3 border border-rule text-xs text-ink placeholder:text-muted focus-visible:outline-2 focus-visible:outline-focus focus:border-accent transition-colors duration-150"
          />
          <button
            onClick={handleAdd}
            className="px-3.5 py-1.5 bg-accent text-accent-ink text-xs font-medium border border-accent hover:opacity-95 transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Add
          </button>
        </div>
      </div>

      {/* Comparison Grid */}
      <div className="panel overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-paper-3 text-muted border-b border-rule">
              <tr>
                <th className="py-3 px-4 font-normal">Brand</th>
                <th className="py-3 px-4 font-normal">Price tier</th>
                <th className="py-3 px-4 font-normal">Audience</th>
                <th className="py-3 px-4 font-normal">Estimated traffic</th>
                <th className="py-3 px-4 font-normal">Active ads</th>
                <th className="py-3 px-4 font-normal">Speed score</th>
                <th className="py-3 px-4 font-normal">Core positioning angle</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-rule-2 text-ink-2">
              {competitors.map((c, idx) => (
                <tr
                  key={idx}
                  className={`hover:bg-paper-3 transition-colors duration-150 ${
                    c.isMainTarget ? 'bg-paper-2 border-l-2 border-accent' : ''
                  }`}
                >
                  <td className="py-3.5 px-4">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-ink">{c.brand}</span>
                      {c.isMainTarget && (
                        <span className="px-1.5 py-0.5 text-[10px] text-accent border border-accent bg-paper-3">
                          target
                        </span>
                      )}
                    </div>
                    <span className="text-[11px] font-mono text-muted">{c.domain}</span>
                  </td>
                  <td className="py-3.5 px-4 font-mono">{c.pricePoint}</td>
                  <td className="py-3.5 px-4 font-mono">{c.followers}</td>
                  <td className="py-3.5 px-4 font-mono">{c.estTraffic}</td>
                  <td className="py-3.5 px-4">
                    <span className="px-2 py-0.5 border border-rule bg-paper-3 text-xs">
                      <span className="font-mono">{c.activeAdsCount}</span> ads
                    </span>
                  </td>
                  <td className="py-3.5 px-4">
                    <span
                      className={`font-mono px-2 py-0.5 border text-xs ${
                        c.mobileSpeed < 50
                          ? 'border-error text-error bg-paper-3'
                          : 'border-accent text-accent bg-paper-3'
                      }`}
                    >
                      {c.mobileSpeed} / 100
                    </span>
                  </td>
                  <td className="py-3.5 px-4 max-w-xs text-xs text-ink-2">
                    {c.uniqueAngle}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
