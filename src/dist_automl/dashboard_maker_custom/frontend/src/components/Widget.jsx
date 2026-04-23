import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import {
  Table as TableIcon,
  Image as ImageIcon,
  Hash,
  List as ListIcon,
  Code,
} from 'lucide-react';

/* ---- Content Renderers ---- */

const TableRenderer = ({ data }) => {
  if (!data || !data.columns) return <div className="widget-loading">Loading table…</div>;
  return (
    <div className="table-container">
      <table>
        <thead>
          <tr>
            {data.columns.map(col => <th key={col}>{col}</th>)}
          </tr>
        </thead>
        <tbody>
          {data.rows.slice(0, 100).map((row, i) => (
            <tr key={i}>
              {data.columns.map(col => <td key={col}>{String(row[col])}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
      {data.rows.length > 100 && <p className="table-overflow-note">Showing first 100 of {data.rows.length} rows</p>}
    </div>
  );
};

const ImageRenderer = ({ src }) => (
  <div className="image-container">
    <img src={src} alt="Analysis Plot" />
  </div>
);

const JsonRenderer = ({ data }) => (
  <pre className="json-container">
    {JSON.stringify(data, null, 2)}
  </pre>
);

const KpiRenderer = ({ data, name }) => (
  <div className="kpi-container">
    <div className="kpi-value">{data.value}</div>
    <div className="kpi-label">{name}</div>
  </div>
);

/* ---- Resize handle definitions ---- */
const HANDLES = [
  // Corners
  { key: 'nw', cls: 'corner', dx: -1, dy: -1 },
  { key: 'ne', cls: 'corner', dx: 1, dy: -1 },
  { key: 'sw', cls: 'corner', dx: -1, dy: 1 },
  { key: 'se', cls: 'corner', dx: 1, dy: 1 },
  // Edges
  { key: 'n', cls: 'edge', dx: 0, dy: -1 },
  { key: 's', cls: 'edge', dx: 0, dy: 1 },
  { key: 'w', cls: 'edge', dx: -1, dy: 0 },
  { key: 'e', cls: 'edge', dx: 1, dy: 0 },
];

const MIN_WIDTH = 180;
const MIN_HEIGHT = 120;

/* ---- Widget Component ---- */

const Widget = ({
  widget,
  onLayoutChange,
  apiBase,
  scale,
  isSelected,
  onSelect,
  onPointerEnterWidget,
  onPointerLeaveWidget,
}) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const isDragging = useRef(false);
  const isResizing = useRef(false);
  const dragStart = useRef({ mx: 0, my: 0, wx: 0, wy: 0 });
  const resizeStart = useRef({ mx: 0, my: 0, wx: 0, wy: 0, ww: 0, wh: 0, dx: 0, dy: 0 });

  // Fetch widget data
  useEffect(() => {
    const fetchData = async () => {
      if (widget.type === 'figure') {
        setData(`${apiBase}/api/image?path=${widget.path}`);
        setLoading(false);
        return;
      }
      try {
        const response = await axios.get(`${apiBase}/api/data?path=${widget.path}`);
        setData(response.data);
      } catch (err) {
        console.error('Error fetching widget data:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [widget.path, widget.type, apiBase]);

  // ---- Drag (header) ----
  const onDragStart = useCallback((e) => {
    if (e.button !== 0) return;
    e.stopPropagation();
    e.preventDefault();
    isDragging.current = true;
    onSelect();
    dragStart.current = {
      mx: e.clientX,
      my: e.clientY,
      wx: widget.x,
      wy: widget.y,
    };

    const onMove = (ev) => {
      if (!isDragging.current) return;
      const dx = (ev.clientX - dragStart.current.mx) / scale;
      const dy = (ev.clientY - dragStart.current.my) / scale;
      onLayoutChange(widget.id, {
        x: dragStart.current.wx + dx,
        y: dragStart.current.wy + dy,
      });
    };

    const onUp = () => {
      isDragging.current = false;
      window.removeEventListener('pointermove', onMove);
      window.removeEventListener('pointerup', onUp);
    };

    window.addEventListener('pointermove', onMove);
    window.addEventListener('pointerup', onUp);
  }, [widget.id, widget.x, widget.y, scale, onLayoutChange, onSelect]);

  // ---- Resize (handles) ----
  const onResizeStart = useCallback((e, handleDx, handleDy) => {
    if (e.button !== 0) return;
    e.stopPropagation();
    e.preventDefault();
    isResizing.current = true;
    onSelect();
    resizeStart.current = {
      mx: e.clientX,
      my: e.clientY,
      wx: widget.x,
      wy: widget.y,
      ww: widget.width,
      wh: widget.height,
      dx: handleDx,
      dy: handleDy,
    };

    const onMove = (ev) => {
      if (!isResizing.current) return;
      const rs = resizeStart.current;
      const deltaX = (ev.clientX - rs.mx) / scale;
      const deltaY = (ev.clientY - rs.my) / scale;

      let newX = rs.wx;
      let newY = rs.wy;
      let newW = rs.ww;
      let newH = rs.wh;

      // Horizontal
      if (rs.dx === 1) {
        newW = Math.max(MIN_WIDTH, rs.ww + deltaX);
      } else if (rs.dx === -1) {
        const maxDx = rs.ww - MIN_WIDTH;
        const clampedDx = Math.min(deltaX, maxDx);
        newX = rs.wx + clampedDx;
        newW = rs.ww - clampedDx;
      }

      // Vertical
      if (rs.dy === 1) {
        newH = Math.max(MIN_HEIGHT, rs.wh + deltaY);
      } else if (rs.dy === -1) {
        const maxDy = rs.wh - MIN_HEIGHT;
        const clampedDy = Math.min(deltaY, maxDy);
        newY = rs.wy + clampedDy;
        newH = rs.wh - clampedDy;
      }

      onLayoutChange(widget.id, {
        x: newX,
        y: newY,
        width: newW,
        height: newH,
      });
    };

    const onUp = () => {
      isResizing.current = false;
      window.removeEventListener('pointermove', onMove);
      window.removeEventListener('pointerup', onUp);
    };

    window.addEventListener('pointermove', onMove);
    window.addEventListener('pointerup', onUp);
  }, [widget.id, widget.x, widget.y, widget.width, widget.height, scale, onLayoutChange, onSelect]);

  const renderContent = () => {
    if (loading) return <div className="widget-loading">Loading…</div>;
    if (!data) return <div className="widget-no-data">No data</div>;

    switch (widget.type) {
      case 'dataframe': return <TableRenderer data={data} />;
      case 'figure': return <ImageRenderer src={data} />;
      case 'dict':
      case 'list': return <JsonRenderer data={data} />;
      case 'kpi': return <KpiRenderer data={data} name={widget.varName} />;
      default: return <div className="widget-no-data">Unknown type: {widget.type}</div>;
    }
  };

  const getIcon = () => {
    const size = 14;
    switch (widget.type) {
      case 'dataframe': return <TableIcon size={size} />;
      case 'figure': return <ImageIcon size={size} />;
      case 'kpi': return <Hash size={size} />;
      case 'list': return <ListIcon size={size} />;
      default: return <Code size={size} />;
    }
  };

  return (
    <div
      className={`widget-wrapper ${isSelected ? 'selected' : ''}`}
      style={{
        left: `${widget.x}px`,
        top: `${widget.y}px`,
        width: `${widget.width}px`,
        height: `${widget.height}px`,
      }}
      onPointerDown={(e) => {
        e.stopPropagation(); // Prevent canvas panning when clicking on widget
        onSelect();
      }}
      onPointerEnter={onPointerEnterWidget}
      onPointerLeave={onPointerLeaveWidget}
    >
      <div className="widget-card">
        {/* Drag handle = the header */}
        <div className="widget-header" onPointerDown={onDragStart}>
          <div className="widget-header-left">
            <span className="widget-header-icon">{getIcon()}</span>
            <span className="widget-title">{widget.varName}</span>
          </div>
          <span className="widget-type-badge">{widget.type}</span>
        </div>

        <div className="widget-body">
          {renderContent()}
        </div>
      </div>

      {/* Resize handles */}
      {HANDLES.map(h => (
        <div
          key={h.key}
          className={`resize-handle ${h.cls} ${h.key}`}
          onPointerDown={(e) => onResizeStart(e, h.dx, h.dy)}
        />
      ))}
    </div>
  );
};

export default Widget;
