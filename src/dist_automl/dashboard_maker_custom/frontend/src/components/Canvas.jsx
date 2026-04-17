import React, { useRef, useEffect, useState } from 'react';
import { TransformWrapper, TransformComponent } from 'react-zoom-pan-pinch';
import Widget from './Widget';

const Canvas = ({ widgets, updateWidgetLayout, apiBase }) => {
  const [isZoomKeyHeld, setIsZoomKeyHeld] = useState(false);
  const containerRef = useRef(null);

  useEffect(() => {
    const handleWheel = (e) => {
      e.preventDefault();
    };

    const handleKeyDown = (e) => {
      if (e.key === '`') setIsZoomKeyHeld(true);
    };

    const handleKeyUp = (e) => {
      if (e.key === '`') setIsZoomKeyHeld(false);
    };

    const container = containerRef.current;
    if (container) {
      container.addEventListener('wheel', handleWheel, { passive: false });
    }
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);

    return () => {
      if (container) {
        container.removeEventListener('wheel', handleWheel);
      }
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, []);

  return (
    <div className="canvas-wrapper" ref={containerRef}>
      <TransformWrapper
        initialScale={1}
        minScale={0.1}
        maxScale={3}
        panning={{ excluded: ['drag-handle', 'widget-body'] }}
        wheel={{
          disabled: !isZoomKeyHeld,
          smooth: true,
          smoothStep: 0.002,
          step: 0.05
        }}
      >
        <TransformComponent
          wrapperStyle={{ width: '100%', height: '100%' }}
          contentStyle={{ width: '5000px', height: '5000px', position: 'relative' }}
        >
          {widgets.length === 0 ? (
            <div className="empty-state" style={{
              position: 'absolute',
              top: '50vh',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              width: '400px'
            }}>
              <p style={{ fontSize: '1.5rem', fontWeight: 600 }}>Your Dashboard</p>
              <p>Select variables from the sidebar to add widgets</p>
            </div>
          ) : (
            widgets.map(widget => (
              <Widget
                key={widget.id}
                widget={widget}
                onLayoutChange={updateWidgetLayout}
                apiBase={apiBase}
              />
            ))
          )}
        </TransformComponent>
      </TransformWrapper>
    </div>
  );
};

export default Canvas;
