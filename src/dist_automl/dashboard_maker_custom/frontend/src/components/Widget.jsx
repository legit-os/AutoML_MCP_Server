import React, { useState, useEffect } from 'react';
import { Rnd } from 'react-rnd';
import axios from 'axios';
import { 
  Table as TableIcon, 
  Image as ImageIcon, 
  Hash, 
  List as ListIcon, 
  Code,
  Maximize2
} from 'lucide-react';

const TableRenderer = ({ data }) => {
  if (!data || !data.columns) return <div>Loading table...</div>;
  return (
    <div className="table-container" style={{ padding: '10px' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
        <thead>
          <tr style={{ textAlign: 'left', borderBottom: '1px solid #444' }}>
            {data.columns.map(col => <th key={col} style={{ padding: '8px' }}>{col}</th>)}
          </tr>
        </thead>
        <tbody>
          {data.rows.slice(0, 100).map((row, i) => (
            <tr key={i} style={{ borderBottom: '1px solid #333' }}>
              {data.columns.map(col => <td key={col} style={{ padding: '8px' }}>{String(row[col])}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
      {data.rows.length > 100 && <p style={{ fontSize: '0.7rem', padding: '10px', color: '#888' }}>Showing first 100 rows...</p>}
    </div>
  );
};

const ImageRenderer = ({ src }) => (
  <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '10px' }}>
    <img src={src} alt="Analysis Plot" style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain', borderRadius: '4px' }} />
  </div>
);

const JsonRenderer = ({ data }) => (
  <pre style={{ padding: '15px', fontSize: '0.8rem', color: '#34d399', overflow: 'auto', height: '100%' }}>
    {JSON.stringify(data, null, 2)}
  </pre>
);

const KpiRenderer = ({ data, name }) => (
  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: '10px' }}>
    <div style={{ fontSize: '3rem', fontWeight: 'bold', color: '#3b82f6' }}>{data.value}</div>
    <div style={{ fontSize: '0.9rem', color: '#888' }}>{name}</div>
  </div>
);

const Widget = ({ widget, onLayoutChange, apiBase }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

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

  const renderContent = () => {
    if (loading) return <div className="empty-state">Loading...</div>;
    if (!data) return <div className="empty-state">No data</div>;

    switch (widget.type) {
      case 'dataframe': return <TableRenderer data={data} />;
      case 'figure': return <ImageRenderer src={data} />;
      case 'dict':
      case 'list': return <JsonRenderer data={data} />;
      case 'kpi': return <KpiRenderer data={data} name={widget.varName} />;
      default: return <div>Unknown type: {widget.type}</div>;
    }
  };

  const getIcon = () => {
    switch (widget.type) {
      case 'dataframe': return <TableIcon size={14} />;
      case 'figure': return <ImageIcon size={14} />;
      case 'kpi': return <Hash size={14} />;
      case 'list': return <ListIcon size={14} />;
      default: return <Code size={14} />;
    }
  };

  return (
    <Rnd
      default={{
        x: widget.x,
        y: widget.y,
        width: widget.width,
        height: widget.height,
      }}
      bounds="parent"
      dragHandleClassName="drag-handle"
      onDragStop={(e, d) => onLayoutChange(widget.id, { x: d.x, y: d.y })}
      onResizeStop={(e, direction, ref, delta, position) => {
        onLayoutChange(widget.id, {
          width: parseInt(ref.style.width),
          height: parseInt(ref.style.height),
          ...position
        });
      }}
      style={{ zIndex: 10 }}
    >
      <div className="widget-card" style={{ width: '100%', height: '100%' }}>
        <div className="widget-header drag-handle">
          <div className="sidebar-title" style={{ gap: '8px', fontSize: '0.85rem' }}>
            {getIcon()}
            <span className="widget-title">{widget.varName}</span>
          </div>
          <div className="var-type-badge" style={{ background: 'rgba(59, 130, 246, 0.2)', color: '#60a5fa' }}>
            {widget.type}
          </div>
        </div>
        <div className="widget-body">
          {renderContent()}
        </div>
      </div>
    </Rnd>
  );
};

export default Widget;
