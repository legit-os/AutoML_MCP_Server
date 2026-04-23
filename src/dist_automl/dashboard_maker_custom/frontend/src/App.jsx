import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import Canvas from './components/Canvas';
import WidgetPicker from './components/WidgetPicker';
import './App.css';

// Base API URL
const API_BASE = window.location.origin === 'http://localhost:5173'
  ? 'http://localhost:8000'
  : window.location.origin;

function App() {
  const [metadata, setMetadata] = useState({ scripts: {} });
  const [activeWidgets, setActiveWidgets] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchMetadata = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE}/api/metadata`);
      setMetadata(response.data);
    } catch (error) {
      console.error('Error fetching metadata:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchMetadata();
  }, [fetchMetadata]);

  const toggleWidget = (scriptKey, varName) => {
    const id = `${scriptKey}::${varName}`;
    const exists = activeWidgets.find(w => w.id === id);

    if (exists) {
      setActiveWidgets(activeWidgets.filter(w => w.id !== id));
    } else {
      const info = metadata.scripts[scriptKey][varName];
      setActiveWidgets([...activeWidgets, {
        id,
        scriptKey,
        varName,
        ...info,
        x: info.x || 80 + activeWidgets.length * 30,
        y: info.y || 80 + activeWidgets.length * 30,
        width: info.width || 420,
        height: info.height || 320,
      }]);
    }
  };

  const updateWidgetLayout = async (id, layout) => {
    // Update local state immediately
    setActiveWidgets(prev => prev.map(w => w.id === id ? { ...w, ...layout } : w));

    // Persist to backend
    const widget = activeWidgets.find(w => w.id === id);
    if (!widget) return;

    const [scriptKey, varName] = id.split('::');
    const merged = { ...widget, ...layout };

    try {
      await axios.post(`${API_BASE}/api/update_layout`, {
        script_key: scriptKey,
        var_name: varName,
        x: merged.x,
        y: merged.y,
        width: merged.width,
        height: merged.height,
      });
    } catch (error) {
      console.error('Error updating layout:', error);
    }
  };

  return (
    <div className="app-container">
      <Canvas
        widgets={activeWidgets}
        updateWidgetLayout={updateWidgetLayout}
        apiBase={API_BASE}
      />
      <WidgetPicker
        metadata={metadata}
        activeWidgets={activeWidgets}
        toggleWidget={toggleWidget}
        onRefresh={fetchMetadata}
        loading={loading}
      />
    </div>
  );
}

export default App;
