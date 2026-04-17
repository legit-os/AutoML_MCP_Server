import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import Sidebar from './components/Sidebar';
import Canvas from './components/Canvas';
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
        x: info.x || 50,
        y: info.y || 50,
        width: info.width || 400,
        height: info.height || 300
      }]);
    }
  };

  const updateWidgetLayout = async (id, layout) => {
    // Update local state immediately for performance
    setActiveWidgets(prev => prev.map(w => w.id === id ? { ...w, ...layout } : w));

    // Save to backend
    const [scriptKey, varName] = id.split('::');
    try {
      await axios.post(`${API_BASE}/api/update_layout`, {
        script_key: scriptKey,
        var_name: varName,
        ...layout
      });
    } catch (error) {
      console.error('Error updating layout:', error);
    }
  };

  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  return (
    <div className={`app-container ${isSidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
      <Sidebar 
        metadata={metadata} 
        activeWidgets={activeWidgets} 
        toggleWidget={toggleWidget}
        onRefresh={fetchMetadata}
        loading={loading}
        isCollapsed={isSidebarCollapsed}
        onToggle={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
      />
      <main className="main-content">
        <Canvas 
          widgets={activeWidgets} 
          updateWidgetLayout={updateWidgetLayout}
          apiBase={API_BASE}
        />
      </main>
    </div>
  );
}

export default App;
