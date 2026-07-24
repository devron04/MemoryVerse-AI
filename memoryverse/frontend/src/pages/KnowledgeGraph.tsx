import { useEffect, useRef, useState } from 'react';
import { getGraphData } from '../api/client';
import type { GraphNode, GraphEdge } from '../api/client';
import './KnowledgeGraph.css';

interface SimNode extends GraphNode {
  x: number;
  y: number;
  vx: number;
  vy: number;
}

export default function KnowledgeGraph() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<GraphEdge | null>(null);

  // Load graph data from backend
  useEffect(() => {
    async function loadGraph() {
      try {
        setLoading(true);
        const data = await getGraphData();
        setNodes(data.nodes);
        setEdges(data.edges);
      } catch (err: any) {
        setError(err.message || 'Failed to load Knowledge Graph');
      } finally {
        setLoading(false);
      }
    }
    loadGraph();
  }, []);

  // Interactive Canvas Physics & Rendering Engine
  useEffect(() => {
    if (!canvasRef.current || nodes.length === 0) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Resize canvas to container
    const width = (canvas.width = canvas.parentElement?.clientWidth || 800);
    const height = (canvas.height = canvas.parentElement?.clientHeight || 600);

    // Initialize physics simulation nodes
    const simNodes: SimNode[] = nodes.map((node, i) => {
      const angle = (i / nodes.length) * Math.PI * 2;
      const radius = 150 + Math.random() * 80;
      return {
        ...node,
        x: width / 2 + Math.cos(angle) * radius,
        y: height / 2 + Math.sin(angle) * radius,
        vx: (Math.random() - 0.5) * 0.5,
        vy: (Math.random() - 0.5) * 0.5,
      };
    });

    let animationFrameId: number;

    // Simulation loop
    function step() {
      // 1. Physics update (Repulsion + Attraction + Center gravity)
      for (let i = 0; i < simNodes.length; i++) {
        const n1 = simNodes[i];

        // Center gravity
        n1.vx += (width / 2 - n1.x) * 0.0005;
        n1.vy += (height / 2 - n1.y) * 0.0005;

        // Node repulsion
        for (let j = i + 1; j < simNodes.length; j++) {
          const n2 = simNodes[j];
          const dx = n2.x - n1.x;
          const dy = n2.y - n1.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          if (dist < 250) {
            const force = (250 - dist) / dist * 0.15;
            n1.vx -= dx * force * 0.05;
            n1.vy -= dy * force * 0.05;
            n2.vx += dx * force * 0.05;
            n2.vy += dy * force * 0.05;
          }
        }
      }

      // Edge spring attraction
      edges.forEach((edge) => {
        const source = simNodes.find((n) => n.id === edge.source);
        const target = simNodes.find((n) => n.id === edge.target);
        if (source && target) {
          const dx = target.x - source.x;
          const dy = target.y - source.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = (dist - 120) * 0.002;
          source.vx += dx * force;
          source.vy += dy * force;
          target.vx -= dx * force;
          target.vy -= dy * force;
        }
      });

      // Apply velocity damping & bounds
      simNodes.forEach((n) => {
        n.vx *= 0.88;
        n.vy *= 0.88;
        n.x += n.vx;
        n.y += n.vy;
        n.x = Math.max(40, Math.min(width - 40, n.x));
        n.y = Math.max(40, Math.min(height - 40, n.y));
      });

      // 2. Render Canvas
      ctx.clearRect(0, 0, width, height);

      // Render Luminous Links / Edges
      edges.forEach((edge) => {
        const source = simNodes.find((n) => n.id === edge.source);
        const target = simNodes.find((n) => n.id === edge.target);
        if (!source || !target) return;

        const isSelected = selectedEdge?.id === edge.id;
        ctx.beginPath();
        ctx.moveTo(source.x, source.y);
        ctx.lineTo(target.x, target.y);
        ctx.strokeStyle = isSelected ? '#E8A93B' : 'rgba(111, 169, 140, 0.25)';
        ctx.lineWidth = isSelected ? 3 : 1.5;
        if (isSelected) {
          ctx.shadowColor = '#E8A93B';
          ctx.shadowBlur = 10;
        } else {
          ctx.shadowBlur = 0;
        }
        ctx.stroke();
      });

      // Render Glowing Nodes
      simNodes.forEach((node) => {
        const isSelected = selectedNode?.id === node.id;
        const radius = isSelected ? node.val + 4 : node.val;

        // Node Glow
        ctx.shadowColor = node.color;
        ctx.shadowBlur = isSelected ? 20 : 10;

        // Inner Circle
        ctx.beginPath();
        ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);
        ctx.fillStyle = node.color;
        ctx.fill();

        // Node Label
        ctx.shadowBlur = 0;
        ctx.font = node.type === 'Document' ? '600 13px Inter' : '400 12px IBM Plex Mono';
        ctx.fillStyle = '#F2EFE6';
        ctx.textAlign = 'center';
        ctx.fillText(node.name, node.x, node.y + radius + 16);
      });

      animationFrameId = requestAnimationFrame(step);
    }

    step();

    // Canvas Click Listener
    function handleClick(e: MouseEvent) {
      const rect = canvas.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const clickY = e.clientY - rect.top;

      // Check node click
      const clickedNode = simNodes.find((n) => {
        const dx = n.x - clickX;
        const dy = n.y - clickY;
        return Math.sqrt(dx * dx + dy * dy) <= n.val + 5;
      });

      if (clickedNode) {
        setSelectedNode(clickedNode);
        setSelectedEdge(null);
        return;
      }

      // Check edge click
      const clickedEdge = edges.find((edge) => {
        const source = simNodes.find((n) => n.id === edge.source);
        const target = simNodes.find((n) => n.id === edge.target);
        if (!source || !target) return false;
        // Distance from point to line segment
        const A = clickX - source.x;
        const B = clickY - source.y;
        const C = target.x - source.x;
        const D = target.y - source.y;
        const dot = A * C + B * D;
        const lenSq = C * C + D * D;
        let param = -1;
        if (lenSq !== 0) param = dot / lenSq;
        let xx, yy;
        if (param < 0) {
          xx = source.x;
          yy = source.y;
        } else if (param > 1) {
          xx = target.x;
          yy = target.y;
        } else {
          xx = source.x + param * C;
          yy = source.y + param * D;
        }
        const dx = clickX - xx;
        const dy = clickY - yy;
        return Math.sqrt(dx * dx + dy * dy) <= 8;
      });

      if (clickedEdge) {
        setSelectedEdge(clickedEdge);
        setSelectedNode(null);
        return;
      }

      setSelectedNode(null);
      setSelectedEdge(null);
    }

    canvas.addEventListener('click', handleClick);

    return () => {
      cancelAnimationFrame(animationFrameId);
      canvas.removeEventListener('click', handleClick);
    };
  }, [nodes, edges, selectedNode, selectedEdge]);

  // Categories for filter pills
  const categories = ['All', 'Certifications', 'Skills', 'Projects', 'Internships', 'Achievements', 'Academics'];

  return (
    <div className="graph-container">
      {/* Header */}
      <div className="graph-header">
        <div className="graph-header-title">
          <h1>Constellation Knowledge Graph</h1>
          <p>Explore relationships and LLM-generated explanations connecting your journey.</p>
        </div>

        <div className="graph-filters">
          {categories.map((cat) => (
            <button
              key={cat}
              className={`filter-pill ${selectedCategory === cat ? 'active' : ''}`}
              onClick={() => setSelectedCategory(cat)}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Canvas View */}
      <div className="canvas-wrapper">
        {loading && (
          <div className="empty-state">
            <div className="empty-icon">🌐</div>
            <h2>Loading Knowledge Graph...</h2>
          </div>
        )}

        {error && (
          <div className="empty-state">
            <div className="empty-icon">⚠️</div>
            <h2>Graph Connection Warning</h2>
            <p>{error}</p>
          </div>
        )}

        {!loading && nodes.length === 0 && !error && (
          <div className="empty-state">
            <div className="empty-icon">🌐</div>
            <h2>No Graph Nodes Yet</h2>
            <p>
              Upload documents in the Upload section to automatically build your identity constellation graph.
            </p>
            <span className="phase-badge">Phase 2 — Active</span>
          </div>
        )}

        <canvas ref={canvasRef} className="graph-canvas" />
      </div>

      {/* Floating Card: Node Detail */}
      {selectedNode && (
        <div className="graph-floating-card">
          <span className={`card-header-badge ${selectedNode.color === '#E8A93B' ? 'card-badge-gold' : 'card-badge-sage'}`}>
            {selectedNode.type}
          </span>
          <h2 className="card-title">{selectedNode.name}</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: 'var(--text-sm)', marginBottom: 'var(--space-3)' }}>
            Category: {selectedNode.category || 'Entity'}
          </p>
          <div className="card-actions">
            <button className="close-card-btn" onClick={() => setSelectedNode(null)}>
              Close
            </button>
          </div>
        </div>
      )}

      {/* Floating Card: Edge Explanation */}
      {selectedEdge && (
        <div className="graph-floating-card">
          <span className="card-header-badge card-badge-gold">
            Relationship Explanation
          </span>
          <h2 className="card-title">{selectedEdge.relationship}</h2>
          <div className="card-explanation">
            "{selectedEdge.explanation}"
          </div>
          <div className="card-actions">
            <button className="close-card-btn" onClick={() => setSelectedEdge(null)}>
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
