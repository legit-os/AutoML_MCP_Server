import React, { useState, useRef, useCallback } from 'react';
import {
  LayoutDashboard,
  RefreshCw,
  Square,
  CheckSquare,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

const WidgetPicker = ({ metadata, activeWidgets, toggleWidget, onRefresh, loading }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [position, setPosition] = useState({ x: 16, y: 16 });
  const isDragging = useRef(false);
  const dragStart = useRef({ mx: 0, my: 0, px: 0, py: 0 });

  const scripts = metadata.scripts || {};

  // ---- Drag the picker bar ----
  const onBarPointerDown = useCallback((e) => {
    // Don't start drag on button clicks
    if (e.target.closest('button')) return;
    if (e.button !== 0) return;
    e.preventDefault();
    isDragging.current = true;
    dragStart.current = {
      mx: e.clientX,
      my: e.clientY,
      px: position.x,
      py: position.y,
    };

    const onMove = (ev) => {
      if (!isDragging.current) return;
      const dx = ev.clientX - dragStart.current.mx;
      const dy = ev.clientY - dragStart.current.my;
      setPosition({
        x: dragStart.current.px + dx,
        y: dragStart.current.py + dy,
      });
    };

    const onUp = () => {
      isDragging.current = false;
      window.removeEventListener('pointermove', onMove);
      window.removeEventListener('pointerup', onUp);
    };

    window.addEventListener('pointermove', onMove);
    window.addEventListener('pointerup', onUp);
  }, [position.x, position.y]);

  return (
    <div
      className="widget-picker"
      style={{ left: `${position.x}px`, top: `${position.y}px` }}
    >
      {/* Toggle bar — draggable */}
      <div className="picker-toggle-bar" onPointerDown={onBarPointerDown}>
        <button
          className="picker-toggle-btn"
          onClick={() => setIsOpen(!isOpen)}
          title="Toggle widget picker"
        >
          <LayoutDashboard size={16} />
          <span>Dashboard</span>
          {isOpen ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>

        <button
          className={`picker-refresh-btn ${loading ? 'spinning' : ''}`}
          onClick={onRefresh}
          disabled={loading}
          title="Refresh metadata"
        >
          <RefreshCw size={14} />
        </button>
      </div>

      {/* Dropdown */}
      {isOpen && (
        <div className="picker-dropdown">
          <div className="picker-dropdown-content">
            {Object.keys(scripts).length === 0 ? (
              <div className="picker-empty">
                <p>No variables found.</p>
                <p>Run an analysis script first.</p>
              </div>
            ) : (
              Object.entries(scripts).map(([scriptPath, vars]) => (
                <div key={scriptPath} className="picker-script-group">
                  <div className="picker-script-header" title={scriptPath}>
                    {scriptPath.split(/[\\/]/).pop()}
                  </div>
                  {Object.entries(vars).map(([varName, info]) => {
                    const id = `${scriptPath}::${varName}`;
                    const isActive = activeWidgets.some(w => w.id === id);

                    return (
                      <div
                        key={varName}
                        className={`picker-var-item ${isActive ? 'active' : ''}`}
                        onClick={() => toggleWidget(scriptPath, varName)}
                      >
                        <span className="picker-checkbox">
                          {isActive ? <CheckSquare size={15} /> : <Square size={15} />}
                        </span>
                        <span className="picker-var-name">{varName}</span>
                        <span className="picker-var-type">{info.type}</span>
                      </div>
                    );
                  })}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default WidgetPicker;
