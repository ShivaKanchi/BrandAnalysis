'use client';

import React, { useState } from 'react';
import { Header, ActiveModule } from '@/components/layout/Header';
import { WorkflowGraph } from '@/components/graph/WorkflowGraph';
import { LeadsTable } from '@/components/table/LeadsTable';
import { ControlsPanel } from '@/components/controls/ControlsPanel';
import { LeadHarvesterView } from '@/components/modules/LeadHarvesterView';
import { BrandAuditView } from '@/components/modules/BrandAuditView';
import { CompetitorMatrixView } from '@/components/modules/CompetitorMatrixView';
import { ProblemRadarView } from '@/components/modules/ProblemRadarView';
import { SavedReportsView } from '@/components/modules/SavedReportsView';
import { useWorkflowAnnouncer } from '@/lib/uiSdkBehaviors';
import { INITIAL_LEADS } from '@/lib/mockData';
import { LeadItem, AuditThresholds } from '@/types/workflow';

export default function Home() {
  const [activeModule, setActiveModule] = useState<ActiveModule>('shopify-revamp');
  const [leads, setLeads] = useState<LeadItem[]>(INITIAL_LEADS);
  const [targetInput, setTargetInput] = useState<string>('Organic Skincare Brands in Austin');
  const [isRunningAutomation, setIsRunningAutomation] = useState<boolean>(false);
  const [thresholds, setThresholds] = useState<AuditThresholds>({
    maxLighthouseScore: 60,
    minFollowers: 2500,
    minConsoleErrors: 1,
  });

  useWorkflowAnnouncer(
    isRunningAutomation
      ? `Workflow pipeline running on target: ${targetInput}`
      : 'Workflow pipeline idle.'
  );

  const handleToggleRun = () => {
    setIsRunningAutomation((prev) => !prev);
  };

  const handleLeadDiscovered = (newLead: LeadItem) => {
    setLeads((prev) => {
      if (prev.some((l) => l.domain === newLead.domain)) return prev;
      return [newLead, ...prev];
    });
  };

  const qualifiedLeadsCount = leads.filter(
    (l) => l.qualificationStatus === 'Qualified'
  ).length;

  return (
    <div className="min-h-screen bg-paper text-ink flex flex-col antialiased selection:bg-accent/35 selection:text-ink overflow-x-clip">
      {/* Top Navigation Bar */}
      <Header
        activeModule={activeModule}
        onSelectModule={setActiveModule}
        leadsCount={leads.length}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-[1440px] w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* MODULE 1: SHOPIFY REVAMP (Primary Flagship Automation) */}
        {activeModule === 'shopify-revamp' && (
          <div className="space-y-6">
            {/* Hero / Overview Banner */}
            <div className="panel p-6">
              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="px-2 py-0.5 text-xs text-accent border border-rule bg-paper-3">
                      pipeline: <code className="font-mono">shopify-revamp</code>
                    </span>
                    <span className="text-xs text-muted">
                      autonomous crawler
                    </span>
                  </div>
                  <h1 className="text-xl sm:text-2xl font-medium text-ink tracking-tight">
                    Shopify Store Auditor and Revamp Finder
                  </h1>
                  <p className="text-xs sm:text-sm text-muted mt-1 max-w-2xl leading-relaxed">
                    Identifies Shopify webstores with low Lighthouse performance scores and runtime console errors,
                    generating customized revamp pitches for speed and layout modernizations.
                  </p>
                </div>

                {/* Telemetry Measurements Row */}
                <div className="flex items-center bg-paper-3 border border-rule">
                  <div className="text-left px-4 py-3 border-r border-rule">
                    <span className="text-xs text-muted block">
                      Qualified leads
                    </span>
                    <span className="text-lg font-normal font-mono text-accent">
                      {qualifiedLeadsCount}
                    </span>
                  </div>
                  <div className="text-left px-4 py-3 border-r border-rule">
                    <span className="text-xs text-muted block">
                      Total stores
                    </span>
                    <span className="text-lg font-normal font-mono text-ink">
                      {leads.length}
                    </span>
                  </div>
                  <div className="text-left px-4 py-3">
                    <span className="text-xs text-muted block">
                      Average speed
                    </span>
                    <span className="text-lg font-normal font-mono text-accent-2">
                      44 / 100
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Controls & Threshold Sliders Panel */}
            <ControlsPanel
              targetInput={targetInput}
              setTargetInput={setTargetInput}
              thresholds={thresholds}
              setThresholds={setThresholds}
              isRunning={isRunningAutomation}
              onRunToggle={handleToggleRun}
            />

            {/* Workflow Graph DAG Component */}
            <WorkflowGraph
              currentWorkflowId="shopify-revamp"
              isRunning={isRunningAutomation}
              onRunToggle={handleToggleRun}
              onLeadDiscovered={handleLeadDiscovered}
              targetInput={targetInput}
            />

            {/* Interactive Leads Data Table */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h2 className="text-sm font-medium text-ink">
                    Discovered stores and outreach telemetry
                  </h2>
                  <p className="text-xs text-muted">
                    Click “Pitch kit” to view customized cold email, social direct messages, and speed scorecards.
                  </p>
                </div>
              </div>

              <LeadsTable leads={leads} />
            </div>
          </div>
        )}

        {/* MODULE 2: LEAD HARVESTER */}
        {activeModule === 'lead-harvester' && (
          <div>
            <LeadHarvesterView />
          </div>
        )}

        {/* MODULE 3: BRAND AUDIT */}
        {activeModule === 'brand-audit' && (
          <div>
            <BrandAuditView />
          </div>
        )}

        {/* MODULE 4: COMPETITOR MATRIX */}
        {activeModule === 'competitor-matrix' && (
          <div>
            <CompetitorMatrixView />
          </div>
        )}

        {/* MODULE 5: PROBLEM RADAR */}
        {activeModule === 'problem-radar' && (
          <div>
            <ProblemRadarView />
          </div>
        )}

        {/* MODULE 6: SAVED REPORTS */}
        {activeModule === 'saved-reports' && (
          <div>
            <SavedReportsView />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-12 border-t border-rule bg-paper-2 py-5 text-xs text-muted">
        <div className="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 bg-accent signal-live" />
            <span>BrandAnalysis Autonomous Agency Engine</span>
          </p>
          <div className="flex items-center gap-6 text-muted">
            <span>Shopify Detection</span>
            <span>Playwright Telemetry</span>
            <span>Vision Diagnostics</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
