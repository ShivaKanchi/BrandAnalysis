'use client';

import React, { useState } from 'react';
import {
  Radar,
  AlertTriangle,
  Flame,
  MessageCircle,
} from 'lucide-react';
import { WorkflowGraph } from '@/components/graph/WorkflowGraph';

interface RadarIssue {
  id: string;
  title: string;
  source: 'Reddit r/shopify' | 'HackerNews' | 'Dev.to' | 'Twitter/X';
  category: 'Shopify Checkout' | 'Speed and CWV' | 'Theme Glitch' | 'App Conflict';
  sentiment: 'Frustrated' | 'Critical Bug' | 'High Demand';
  upvotes: number;
  commentsCount: number;
  timestamp: string;
  opportunity: string;
}

const INITIAL_RADAR_ISSUES: RadarIssue[] = [
  {
    id: 'rad-1',
    title: 'New Shopify checkout extensibility broke our custom upsell drawer and cart count badge',
    source: 'Reddit r/shopify',
    category: 'Shopify Checkout',
    sentiment: 'Critical Bug',
    upvotes: 184,
    commentsCount: 62,
    timestamp: '2 hours ago',
    opportunity: 'Offer headless Checkout UI Extension migration package ($1,500 - $3,000)',
  },
  {
    id: 'rad-2',
    title: 'Google PageSpeed dropped from 78 to 32 after installing Klaviyo and two review widgets',
    source: 'Reddit r/shopify',
    category: 'Speed and CWV',
    sentiment: 'Frustrated',
    upvotes: 215,
    commentsCount: 88,
    timestamp: '5 hours ago',
    opportunity: 'Third-party script deferral and web worker telemetry offloader',
  },
  {
    id: 'rad-3',
    title: 'Safari iOS 18 address bar clipping fixed sticky add-to-cart buttons on mobile',
    source: 'Dev.to',
    category: 'Theme Glitch',
    sentiment: 'Critical Bug',
    upvotes: 94,
    commentsCount: 31,
    timestamp: '1 day ago',
    opportunity: 'Viewport dynamic height (dvh) theme patch kit for popular storefronts',
  },
  {
    id: 'rad-4',
    title: 'Need a way to automatically audit client stores for broken 404 assets before BFCM',
    source: 'HackerNews',
    category: 'App Conflict',
    sentiment: 'High Demand',
    upvotes: 340,
    commentsCount: 112,
    timestamp: '2 days ago',
    opportunity: 'Automated Playwright continuous dead link and console error sentry runner',
  },
];

export function ProblemRadarView() {
  const [issues, setIssues] = useState<RadarIssue[]>(INITIAL_RADAR_ISSUES);
  const [selectedCategory, setSelectedCategory] = useState<string>('All');

  const filteredIssues = issues.filter(
    (i) => selectedCategory === 'All' || i.category === selectedCategory
  );

  return (
    <div className="space-y-6">
      {/* Workflow DAG for Problem Radar */}
      <WorkflowGraph currentWorkflowId="problem-radar" />

      {/* Filter and stats banner */}
      <div className="panel p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Radar className="w-4 h-4 text-accent" />
          <h3 className="text-xs font-medium text-ink">
            Community pain point and micro-opportunity radar
          </h3>
        </div>

        <div className="flex items-center gap-1.5 flex-wrap">
          {['All', 'Shopify Checkout', 'Speed and CWV', 'Theme Glitch', 'App Conflict'].map(
            (cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-3 py-1.5 text-xs font-medium border transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:bg-paper-2 disabled:opacity-40 disabled:cursor-not-allowed ${
                  selectedCategory === cat
                    ? 'border-accent bg-paper-2 text-accent'
                    : 'border-rule text-muted hover:text-ink bg-paper-3'
                }`}
              >
                {cat}
              </button>
            )
          )}
        </div>
      </div>

      {/* Issues Cards */}
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
                    issue.sentiment === 'Critical Bug'
                      ? 'border-error text-error bg-paper-3'
                      : issue.sentiment === 'Frustrated'
                      ? 'border-accent text-accent bg-paper-3'
                      : 'border-accent-2 text-accent-2 bg-paper-3'
                  }`}
                >
                  {issue.sentiment}
                </span>
              </div>

              <h4 className="text-xs font-medium text-ink leading-snug">
                {issue.title}
              </h4>
            </div>

            <div className="pt-3 border-t border-rule-2 space-y-2">
              <div className="p-3 bg-paper-3 border border-rule text-xs text-ink-2">
                <span className="block text-xs font-medium text-accent mb-0.5">
                  Agency pitch opportunity:
                </span>
                {issue.opportunity}
              </div>

              <div className="flex items-center justify-between text-xs text-muted">
                <div className="flex items-center gap-2">
                  <span>
                    <strong className="text-ink font-mono font-normal">{issue.upvotes}</strong> upvotes
                  </span>
                  <span className="border-l border-rule h-3" />
                  <span>
                    <strong className="text-ink font-mono font-normal">{issue.commentsCount}</strong> comments
                  </span>
                </div>
                <span>{issue.timestamp}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
