'use client';

import React, { useState } from 'react';
import {
  Compass,
  MapPin,
  Search,
  ExternalLink,
  Star,
  ArrowRight,
} from 'lucide-react';
import { WorkflowGraph } from '@/components/graph/WorkflowGraph';

interface ProspectLead {
  id: string;
  name: string;
  niche: string;
  location: string;
  rating: number;
  reviewsCount: number;
  website: string;
  phone: string;
  socialInstagram?: string;
  followers?: number;
  email?: string;
  status: 'Verified' | 'Pending Social' | 'No Website';
}

const INITIAL_PROSPECTS: ProspectLead[] = [
  {
    id: 'p-1',
    name: 'Austin Artisan Apothecary',
    niche: 'Organic Skincare',
    location: 'Austin, TX',
    rating: 4.9,
    reviewsCount: 142,
    website: 'https://austin-apothecary.demo',
    phone: '+1 (512) 555-0192',
    socialInstagram: '@austin.apothecary',
    followers: 12400,
    email: 'hello@austin-apothecary.demo',
    status: 'Verified',
  },
  {
    id: 'p-2',
    name: 'Hill Country Leather Co',
    niche: 'Leather Goods',
    location: 'Austin, TX',
    rating: 4.8,
    reviewsCount: 89,
    website: 'https://hillcountryleather.demo',
    phone: '+1 (512) 555-0144',
    socialInstagram: '@hillcountryleather',
    followers: 8200,
    email: 'info@hillcountryleather.demo',
    status: 'Verified',
  },
  {
    id: 'p-3',
    name: 'Barton Springs Botanicals',
    niche: 'Herbal Wellness',
    location: 'Austin, TX',
    rating: 4.6,
    reviewsCount: 64,
    website: 'https://bartonbotanicals.demo',
    phone: '+1 (512) 555-0188',
    status: 'Pending Social',
  },
];

export function LeadHarvesterView() {
  const [prospects, setProspects] = useState<ProspectLead[]>(INITIAL_PROSPECTS);
  const [nicheQuery, setNicheQuery] = useState('Boutique Skincare');
  const [locationQuery, setLocationQuery] = useState('Austin, TX');
  const [isCrawling, setIsCrawling] = useState(false);

  const handleHarvest = () => {
    setIsCrawling(true);
    setTimeout(() => {
      setIsCrawling(false);
      setProspects((prev) => [
        {
          id: `p-${Date.now()}`,
          name: `${nicheQuery} Co`,
          niche: nicheQuery,
          location: locationQuery,
          rating: 4.7,
          reviewsCount: 52,
          website: 'https://example-store.demo',
          phone: '+1 (512) 555-0177',
          followers: 4300,
          email: 'contact@example-store.demo',
          status: 'Verified',
        },
        ...prev,
      ]);
    }, 2000);
  };

  return (
    <div className="space-y-6">
      {/* Workflow DAG for Lead Harvester */}
      <WorkflowGraph currentWorkflowId="lead-harvester" />

      {/* Harvester Query Box */}
      <div className="panel p-5">
        <div className="flex items-center gap-2 mb-3">
          <Compass className="w-4 h-4 text-accent" />
          <h3 className="text-xs font-medium text-ink">
            Directory and local map prospector
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="relative">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
            <input
              type="text"
              value={nicheQuery}
              onChange={(e) => setNicheQuery(e.target.value)}
              placeholder="Niche (e.g. Boutique, Coffee, Skincare)"
              className="w-full pl-10 pr-3 py-2 bg-paper-3 border border-rule text-xs text-ink placeholder:text-muted focus-visible:outline-2 focus-visible:outline-focus focus:border-accent transition-colors duration-150"
            />
          </div>

          <div className="relative">
            <MapPin className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-muted" />
            <input
              type="text"
              value={locationQuery}
              onChange={(e) => setLocationQuery(e.target.value)}
              placeholder="City, state, or postal code"
              className="w-full pl-10 pr-3 py-2 bg-paper-3 border border-rule text-xs text-ink placeholder:text-muted focus-visible:outline-2 focus-visible:outline-focus focus:border-accent transition-colors duration-150"
            />
          </div>

          <button
            onClick={handleHarvest}
            disabled={isCrawling}
            className="flex items-center justify-center gap-2 px-5 py-2 text-xs font-medium bg-accent text-accent-ink border border-accent hover:opacity-95 transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <span className="whitespace-nowrap">{isCrawling ? 'Harvesting directory…' : 'Harvest local leads'}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Leads Table */}
      <div className="panel overflow-hidden">
        <div className="p-3 border-b border-rule flex items-center justify-between bg-paper-3">
          <h4 className="text-xs font-medium text-ink">
            Discovered local leads ({prospects.length})
          </h4>
          <span className="text-xs text-muted">
            Extracts website, social presence, and verified contact channels
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-paper-3 text-muted border-b border-rule">
              <tr>
                <th className="py-3 px-4 font-normal">Business</th>
                <th className="py-3 px-4 font-normal">Location</th>
                <th className="py-3 px-4 font-normal">Rating</th>
                <th className="py-3 px-4 font-normal">Contact</th>
                <th className="py-3 px-4 font-normal">Audience</th>
                <th className="py-3 px-4 font-normal">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-rule-2 text-ink-2">
              {prospects.map((p) => (
                <tr key={p.id} className="hover:bg-paper-3 transition-colors duration-150">
                  <td className="py-3.5 px-4">
                    <span className="font-medium text-ink block">{p.name}</span>
                    <a
                      href={p.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[11px] font-mono text-accent-2 hover:underline inline-flex items-center gap-1"
                    >
                      {p.website}
                      <ExternalLink className="w-2.5 h-2.5" />
                    </a>
                  </td>
                  <td className="py-3.5 px-4 text-muted">{p.location}</td>
                  <td className="py-3.5 px-4">
                    <div className="flex items-center gap-1 text-accent">
                      <Star className="w-3.5 h-3.5 fill-current" />
                      <span className="font-mono">{p.rating}</span>
                      <span className="text-muted text-xs font-normal">({p.reviewsCount})</span>
                    </div>
                  </td>
                  <td className="py-3.5 px-4">
                    <div className="space-y-0.5 text-xs">
                      <div className="text-ink">{p.phone}</div>
                      {p.email && <div className="text-accent-2 font-mono text-[11px]">{p.email}</div>}
                    </div>
                  </td>
                  <td className="py-3.5 px-4">
                    {p.followers ? (
                      <span className="text-ink font-mono">{p.followers.toLocaleString()}</span>
                    ) : (
                      <span className="text-muted text-xs">Unlinked</span>
                    )}
                  </td>
                  <td className="py-3.5 px-4">
                    <span
                      className={`px-2 py-0.5 text-xs border ${
                        p.status === 'Verified'
                          ? 'border-accent text-accent bg-paper-3'
                          : 'border-rule text-muted bg-paper-3'
                      }`}
                    >
                      {p.status}
                    </span>
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
