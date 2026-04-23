import React, { useRef, useState, useCallback, useEffect } from 'react';
import Widget from './Widget';
import { Minus, Plus, Maximize2 } from 'lucide-react';

const MIN_SCALE = 0.1;
const MAX_SCALE = 4;
const ZOOM_STEP = 0.1;
const SCROLL_ZOOM_FACTOR = 0.001;

const Canvas = ({ widgets, updateWidgetLayout, apiBase }) => {
  const viewportRef = useRef(null);

  // Camera state: offset is in screen pixels, scale is the zoom factor
  const [camera, setCamera] = useState({ x: 0, y: 0, scale: 1 });
  const [isPanning, setIsPanning] = useState(false);
  const panStart = useRef({ x: 0, y: 0, camX: 0, camY: 0 });

  // Track whether pointer is over a widget (to change cursor)
  const [overWidget, setOverWidget] = useState(false);

  // Track which widget is selected
  const [selectedWidget, setSelectedWidget] = useState(null);

  // ---- Panning via left-click on canvas background ----
  const handlePointerDown = useCallback((e) => {
    // Only left button and only if clicking on the canvas itself (not a widget)
    if (e.button !== 0) return;
    if (e.target !== viewportRef.current && e.target !== viewportRef.current?.querySelector('.canvas-transform')) return;

    setIsPanning(true);
    setSelectedWidget(null);
    panStart.current = {
      x: e.clientX,
      y: e.clientY,
      camX: camera.x,
      camY: camera.y,
    };
    viewportRef.current?.setPointerCapture(e.pointerId);
    e.preventDefault();
  }, [camera.x, camera.y]);

  const handlePointerMove = useCallback((e) => {
    if (!isPanning) return;
    const dx = e.clientX - panStart.current.x;
    const dy = e.clientY - panStart.current.y;
    setCamera(prev => ({
      ...prev,
      x: panStart.current.camX + dx,
      y: panStart.current.camY + dy,
    }));
  }, [isPanning]);

  const handlePointerUp = useCallback((e) => {
    if (isPanning) {
      setIsPanning(false);
      viewportRef.current?.releasePointerCapture(e.pointerId);
    }
  }, [isPanning]);

  // ---- Zoom via Ctrl+Scroll, centered on cursor ----
  const handleWheel = useCallback((e) => {
    e.preventDefault();

    if (e.ctrlKey || e.metaKey) {
      // Zoom
      const rect = viewportRef.current.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      setCamera(prev => {
        const delta = -e.deltaY * SCROLL_ZOOM_FACTOR;
        const newScale = Math.min(MAX_SCALE, Math.max(MIN_SCALE, prev.scale * (1 + delta)));
        const ratio = newScale / prev.scale;

        // Adjust offset so the point under the cursor stays fixed
        const newX = mouseX - ratio * (mouseX - prev.x);
        const newY = mouseY - ratio * (mouseY - prev.y);

        return { x: newX, y: newY, scale: newScale };
      });
    } else {
      // Pan with scroll
      setCamera(prev => ({
        ...prev,
        x: prev.x - e.deltaX,
        y: prev.y - e.deltaY,
      }));
    }
  }, []);

  // Attach wheel listener with { passive: false }
  useEffect(() => {
    const vp = viewportRef.current;
    if (!vp) return;
    vp.addEventListener('wheel', handleWheel, { passive: false });
    return () => vp.removeEventListener('wheel', handleWheel);
  }, [handleWheel]);

  // ---- Zoom buttons ----
  const zoomIn = () => {
    setCamera(prev => ({
      ...prev,
      scale: Math.min(MAX_SCALE, prev.scale + ZOOM_STEP),
    }));
  };

  const zoomOut = () => {
    setCamera(prev => ({
      ...prev,
      scale: Math.max(MIN_SCALE, prev.scale - ZOOM_STEP),
    }));
  };

  const resetZoom = () => {
    setCamera({ x: 0, y: 0, scale: 1 });
  };

  // Compute CSS transform for the content layer
  const transformStyle = {
    transform: `translate(${camera.x}px, ${camera.y}px) scale(${camera.scale})`,
  };

  // Compute grid background offset and size
  const baseGridSize = 30;
  const gridSize = baseGridSize * camera.scale;
  const gridOx = camera.x % gridSize;
  const gridOy = camera.y % gridSize;

  const viewportClass = [
    'canvas-viewport',
    isPanning ? 'panning' : '',
    overWidget && !isPanning ? 'on-widget' : '',
  ].filter(Boolean).join(' ');

  return (
    <>
      <div
        ref={viewportRef}
        className={viewportClass}
        style={{
          '--grid-size': `${gridSize}px`,
          '--grid-ox': `${gridOx}px`,
          '--grid-oy': `${gridOy}px`,
        }}
        onPointerDown={handlePointerDown}
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
      >
        <div className="canvas-transform" style={transformStyle}>
          {widgets.map(widget => (
            <Widget
              key={widget.id}
              widget={widget}
              onLayoutChange={updateWidgetLayout}
              apiBase={apiBase}
              scale={camera.scale}
              isSelected={selectedWidget === widget.id}
              onSelect={() => setSelectedWidget(widget.id)}
              onPointerEnterWidget={() => setOverWidget(true)}
              onPointerLeaveWidget={() => setOverWidget(false)}
            />
          ))}
        </div>

        {widgets.length === 0 && (
          <div className="canvas-empty">
            <h2>Your Dashboard</h2>
            <p>Open the widget picker and select variables to visualize</p>
          </div>
        )}
      </div>

      {/* Zoom indicator */}
      <div className="zoom-indicator">
        <button className="zoom-btn" onClick={zoomOut} title="Zoom out">
          <Minus size={14} />
        </button>
        <span className="zoom-level" onClick={resetZoom} title="Reset zoom">
          {Math.round(camera.scale * 100)}%
        </span>
        <button className="zoom-btn" onClick={zoomIn} title="Zoom in">
          <Plus size={14} />
        </button>
      </div>
    </>
  );
};

export default Canvas;
