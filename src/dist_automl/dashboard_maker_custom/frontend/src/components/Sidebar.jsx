import React from 'react';
import { LayoutDashboard, RefreshCw, Square, CheckSquare } from 'lucide-react';

const Sidebar = ({ metadata, activeWidgets, toggleWidget, onRefresh, loading }) => {
  const scripts = metadata.scripts || {};
  
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-title">
          <LayoutDashboard size={20} color="#3b82f6" />
          <span>Dashboard</span>
        </div>
        <button 
          className={`refresh-btn ${loading ? 'spinning' : ''}`}
          onClick={onRefresh}
          disabled={loading}
        >
          <RefreshCw size={18} />
        </button>
      </div>

      <div className="sidebar-content">
        {Object.keys(scripts).length === 0 ? (
          <div className="empty-state">
            <p>No variables found.</p>
            <p style={{fontSize: '0.8rem'}}>Run an analysis script first.</p>
          </div>
        ) : (
          Object.entries(scripts).map(([scriptPath, vars]) => (
            <div key={scriptPath} className="script-group">
              <div className="script-header" title={scriptPath}>
                {scriptPath.split(/[\\/]/).pop()}
              </div>
              {Object.entries(vars).map(([varName, info]) => {
                const id = `${scriptPath}::${varName}`;
                const isActive = activeWidgets.some(w => w.id === id);
                
                return (
                  <div 
                    key={varName} 
                    className={`var-item ${isActive ? 'active' : ''}`}
                    onClick={() => toggleWidget(scriptPath, varName)}
                  >
                    {isActive ? <CheckSquare size={16} /> : <Square size={16} />}
                    <span className="var-name">{varName}</span>
                    <span className="var-type-badge">{info.type}</span>
                  </div>
                );
              })}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default Sidebar;
