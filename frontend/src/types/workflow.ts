export type NodeStatus = 'idle' | 'running' | 'completed' | 'error';

export interface WorkflowNodeData {
  id: string;
  label: string;
  subtitle?: string;
  iconName?: string;
  status: NodeStatus;
  durationMs?: number;
  inputParams?: Record<string, any>;
  outputArtifacts?: Record<string, any>;
  logs?: string[];
  metrics?: Record<string, string | number>;
  errorMessage?: string;
}

export interface WorkflowPreset {
  id: string;
  name: string;
  description: string;
  nodes: {
    id: string;
    label: string;
    subtitle: string;
    iconName: string;
  }[];
  edges: {
    id: string;
    source: string;
    target: string;
  }[];
}

export type QualificationStatus = 'Qualified' | 'Pending' | 'Rejected' | 'Non-Shopify';

export interface ConsoleErrorItem {
  type: 'error' | 'warning' | 'network_404';
  message: string;
  sourceUrl?: string;
  line?: number;
}

export interface LeadItem {
  id: string;
  domain: string;
  storeName: string;
  niche: string;
  platform: string;
  isShopify: boolean;
  followers: number;
  engagementRate?: string;
  lighthouseScore: number;
  lighthouseMetrics?: {
    fcp?: string;
    lcp?: string;
    cls?: string;
    speedIndex?: string;
    seo?: number;
    accessibility?: number;
  };
  consoleErrorsCount: number;
  consoleErrorsList?: ConsoleErrorItem[];
  visionScore?: number;
  visionCritique?: {
    summary: string;
    flaws: string[];
    revampIdeas: string[];
  };
  qualificationStatus: QualificationStatus;
  pitchEmail?: {
    subject: string;
    body: string;
  };
  pitchDm?: {
    instagram: string;
    linkedin: string;
  };
  discoveredAt: string;
}

export interface AuditThresholds {
  maxLighthouseScore: number;
  minFollowers: number;
  minConsoleErrors: number;
}

export interface WorkflowRunEvent {
  workflowId: string;
  runId: string;
  timestamp: string;
  event: 'run_start' | 'node_start' | 'node_progress' | 'node_complete' | 'node_error' | 'lead_discovered' | 'run_complete';
  nodeId?: string;
  status?: NodeStatus;
  logs?: string[];
  durationMs?: number;
  lead?: LeadItem;
  output?: Record<string, any>;
  error?: string;
}
