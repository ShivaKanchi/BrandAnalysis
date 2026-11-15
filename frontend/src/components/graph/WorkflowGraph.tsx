'use client';

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Node,
  Edge,
  MarkerType,
} from '@xyflow/react';
import { Play, Square, RotateCcw, Activity } from 'lucide-react';
import { CustomNode } from './CustomNode';
import { NodeInspectDrawer } from './NodeInspectDrawer';
import { WORKFLOW_PRESETS } from '@/lib/mockData';
import { WorkflowNodeData, NodeStatus } from '@/types/workflow';

const nodeTypes = {
  custom: CustomNode,
};

interface WorkflowGraphProps {
  currentWorkflowId?: string;
  onWorkflowChange?: (workflowId: string) => void;
  onLeadDiscovered?: (lead: any) => void;
  isRunning?: boolean;
  onRunToggle?: () => void;
  targetInput?: string;
}

export function WorkflowGraph({
  currentWorkflowId = 'shopify-revamp',
  onWorkflowChange,
  onLeadDiscovered,
  isRunning = false,
  onRunToggle,
  targetInput,
}: WorkflowGraphProps) {
  const [selectedPresetId, setSelectedPresetId] = useState<string>(currentWorkflowId);
  const [inspectedNode, setInspectedNode] = useState<WorkflowNodeData | null>(null);
  const [activeRunningNodeId, setActiveRunningNodeId] = useState<string | null>(null);
  const [executionStats, setExecutionStats] = useState<{
    elapsedSeconds: number;
    completedCount: number;
    totalNodes: number;
  }>({ elapsedSeconds: 0, completedCount: 0, totalNodes: 8 });

  // Find active preset
  const currentPreset = useMemo(() => {
    return (
      WORKFLOW_PRESETS.find((p) => p.id === selectedPresetId) ||
      WORKFLOW_PRESETS[0]
    );
  }, [selectedPresetId]);

  // Compute initial nodes in a clean DAG horizontal layout
  const initialNodes: Node[] = useMemo(() => {
    const spacingX = 320;
    const spacingY = 120;
    const isMultiRow = currentPreset.nodes.length > 5;

    return currentPreset.nodes.map((n, index) => {
      let x = index * spacingX;
      let y = 100;

      if (isMultiRow) {
        const row = Math.floor(index / 4);
        const col = index % 4;
        x = col * spacingX + 60;
        y = row * 220 + 80;
      }

      return {
        id: n.id,
        type: 'custom',
        position: { x, y },
        data: {
          id: n.id,
          label: n.label,
          subtitle: n.subtitle,
          iconName: n.iconName,
          status: 'idle' as NodeStatus,
          durationMs: 0,
          logs: [
            `Initialized node [${n.id}]`,
            `Waiting for pipeline trigger...`,
          ],
          inputParams: { target: targetInput || 'skincare stores in austin' },
          outputArtifacts: {},
        },
      };
    });
  }, [currentPreset, targetInput]);

  // Compute edges with theme CSS variables
  const initialEdges: Edge[] = useMemo(() => {
    return currentPreset.edges.map((e) => ({
      id: e.id,
      source: e.source,
      target: e.target,
      type: 'smoothstep',
      animated: isRunning,
      style: {
        stroke: isRunning ? 'var(--color-accent)' : 'var(--color-rule)',
        strokeWidth: 1.5,
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: isRunning ? 'var(--color-accent)' : 'var(--color-rule)',
        width: 12,
        height: 12,
      },
    }));
  }, [currentPreset, isRunning]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Update nodes and edges when preset changes
  useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
    setExecutionStats((prev) => ({
      ...prev,
      totalNodes: initialNodes.length,
      completedCount: 0,
    }));
  }, [initialNodes, initialEdges, setNodes, setEdges]);

  // Handle node click -> open inspect drawer
  const handleNodeClick = useCallback(
    (_: any, node: Node) => {
      setInspectedNode(node.data as unknown as WorkflowNodeData);
    },
    []
  );

  // Update inspectedNode live if node data changes
  useEffect(() => {
    if (inspectedNode) {
      const updated = nodes.find((n) => n.id === inspectedNode.id);
      if (updated) {
        setInspectedNode(updated.data as unknown as WorkflowNodeData);
      }
    }
  }, [nodes, inspectedNode]);

  // Workflow run simulation / SSE subscriber
  useEffect(() => {
    if (!isRunning) {
      setActiveRunningNodeId(null);
      return;
    }

    let currentIndex = 0;
    const nodeSequence = currentPreset.nodes.map((n) => n.id);
    let eventSource: EventSource | null = null;

    try {
      const sseUrl = `/api/workflows/${selectedPresetId}/run?target=${encodeURIComponent(
        targetInput || 'default'
      )}`;
      eventSource = new EventSource(sseUrl);

      eventSource.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.nodeId) {
            setNodes((nds) =>
              nds.map((node) => {
                if (node.id === payload.nodeId) {
                  return {
                    ...node,
                    data: {
                      ...node.data,
                      status: payload.status || 'running',
                      logs: payload.logs || (node.data as any).logs,
                      durationMs: payload.durationMs || (node.data as any).durationMs,
                      outputArtifacts: payload.output || (node.data as any).outputArtifacts,
                    },
                  };
                }
                return node;
              })
            );
          }
          if (payload.lead && onLeadDiscovered) {
            onLeadDiscovered(payload.lead);
          }
        } catch (e) {
          console.warn('SSE payload parse error', e);
        }
      };

      eventSource.onerror = () => {
        eventSource?.close();
      };
    } catch {
      // Backend not yet reachable
    }

    const interval = setInterval(() => {
      if (currentIndex < nodeSequence.length) {
        const nodeId = nodeSequence[currentIndex];
        setActiveRunningNodeId(nodeId);

        setNodes((nds) =>
          nds.map((n) => {
            if (n.id === nodeId) {
              const currentLogs = (n.data as any).logs || [];
              return {
                ...n,
                data: {
                  ...n.data,
                  status: 'running',
                  logs: [
                    ...currentLogs,
                    `[${new Date().toLocaleTimeString()}] Executing step: ${n.data.label}...`,
                    `[${new Date().toLocaleTimeString()}] Telemetry analysis for ${targetInput || 'lumina-skin.com'}`,
                  ],
                },
              };
            }
            return n;
          })
        );

        setTimeout(() => {
          setNodes((nds) =>
            nds.map((n) => {
              if (n.id === nodeId) {
                const currentLogs = (n.data as any).logs || [];
                return {
                  ...n,
                  data: {
                    ...n.data,
                    status: 'completed',
                    durationMs: Math.floor(Math.random() * 800 + 400),
                    logs: [
                      ...currentLogs,
                      `[${new Date().toLocaleTimeString()}] Step completed cleanly (code 200).`,
                    ],
                  },
                };
              }
              return n;
            })
          );
          setExecutionStats((prev) => ({
            ...prev,
            completedCount: prev.completedCount + 1,
          }));
        }, 1200);

        currentIndex++;
      } else {
        clearInterval(interval);
        setActiveRunningNodeId(null);
        if (onRunToggle && isRunning) {
          onRunToggle();
        }
      }
    }, 1500);

    return () => {
      clearInterval(interval);
      if (eventSource) {
        eventSource.close();
      }
    };
  }, [isRunning, currentPreset, targetInput, selectedPresetId, onLeadDiscovered, onRunToggle, setNodes]);

  const handleReset = () => {
    setNodes(initialNodes);
    setActiveRunningNodeId(null);
    setExecutionStats({
      elapsedSeconds: 0,
      completedCount: 0,
      totalNodes: initialNodes.length,
    });
  };

  const handlePresetSelect = (id: string) => {
    setSelectedPresetId(id);
    if (onWorkflowChange) {
      onWorkflowChange(id);
    }
  };

  return (
    <div className="panel relative w-full h-[540px] overflow-hidden flex flex-col">
      {/* Top Workflow Preset Selector Toolbar */}
      <div className="px-4 py-3 border-b border-rule bg-paper-2 flex flex-wrap items-center justify-between gap-4 z-10">
        <div className="flex items-center gap-3">
          <div className="p-1.5 border border-rule bg-paper-3 text-accent">
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted">
                Pipeline architecture
              </span>
              <span className="inline-flex items-center gap-1.5 px-2 py-0.5 border border-rule text-[10px] text-accent bg-paper-3">
                <span className="w-1.5 h-1.5 bg-accent signal-live" />
                Live DAG
              </span>
            </div>
            <h3 className="text-xs font-medium text-ink">
              {currentPreset.name}
            </h3>
          </div>
        </div>

        {/* Preset Selector Tabs */}
        <div className="flex items-center gap-1 bg-paper-3 p-1 border border-rule">
          {WORKFLOW_PRESETS.map((preset) => {
            const isActive = preset.id === selectedPresetId;
            return (
              <button
                key={preset.id}
                onClick={() => handlePresetSelect(preset.id)}
                className={`px-2.5 py-1 text-xs font-medium transition-colors duration-150 border focus-visible:outline-2 focus-visible:outline-focus disabled:opacity-40 disabled:cursor-not-allowed ${
                  isActive
                    ? 'border-accent text-accent bg-paper-2'
                    : 'border-transparent text-muted hover:text-ink hover:bg-paper-2'
                }`}
              >
                {preset.name.split(' ')[0]}
              </button>
            );
          })}
        </div>

        {/* Workflow Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleReset}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-paper-3 hover:bg-paper text-muted hover:text-ink border border-rule hover:border-muted transition-colors duration-150 focus-visible:outline-2 focus-visible:outline-focus active:bg-paper-2 disabled:opacity-40 disabled:cursor-not-allowed"
            title="Reset DAG nodes"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span className="whitespace-nowrap">Reset</span>
          </button>

          <button
            onClick={onRunToggle}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-medium whitespace-nowrap transition-colors duration-150 border focus-visible:outline-2 focus-visible:outline-focus active:opacity-90 disabled:opacity-40 disabled:cursor-not-allowed ${
              isRunning
                ? 'bg-paper-3 border-error text-error hover:bg-error/10'
                : 'bg-accent border-accent text-accent-ink hover:opacity-95'
            }`}
          >
            {isRunning ? (
              <>
                <Square className="w-3.5 h-3.5 fill-current" />
                <span className="whitespace-nowrap">Stop</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span className="whitespace-nowrap">Execute</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Main React Flow Canvas */}
      <div className="flex-1 w-full h-full relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={handleNodeClick}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.3 }}
          minZoom={0.4}
          maxZoom={1.5}
          proOptions={{ hideAttribution: true }}
        >
          <Background color="var(--color-rule)" gap={20} size={1} />
          <Controls showInteractive={false} position="bottom-left" />
          <MiniMap
            nodeStrokeColor="var(--color-rule)"
            nodeColor="var(--color-paper-2)"
            maskColor="var(--color-paper-3)"
            position="bottom-right"
            className="!bg-paper-2 !border !border-rule overflow-hidden"
          />
        </ReactFlow>

        {/* Live Status Overlay in bottom center */}
        {isRunning && (
          <div className="absolute bottom-5 left-1/2 -translate-x-1/2 bg-paper-2 border border-rule px-3.5 py-1.5 flex items-center gap-3 text-xs text-ink z-20">
            <span className="w-2 h-2 bg-accent signal-live" />
            <span className="font-medium text-xs">
              Running:{' '}
              <span className="text-accent font-mono">
                {activeRunningNodeId || 'orchestrating'}
              </span>
            </span>
            <span className="border-l border-rule h-3.5" />
            <span className="text-muted text-xs">
              <span className="font-mono text-ink">{executionStats.completedCount}/{executionStats.totalNodes}</span> complete
            </span>
          </div>
        )}
      </div>

      {/* Slide-over Node Inspector Drawer */}
      <NodeInspectDrawer
        node={inspectedNode}
        onClose={() => setInspectedNode(null)}
      />
    </div>
  );
}
