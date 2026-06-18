import React from 'react';
import { BookOpen, Code, Database, Smartphone, PenTool, TrendingUp, Layers } from 'lucide-react';

const layers = [
  { id: 'design', title: 'Design', progress: 0, icon: <PenTool size={32} color="#f43f5e" /> },
  { id: 'marketing', title: 'Marketing', progress: 0, icon: <TrendingUp size={32} color="#10b981" /> },
  { id: 'development', title: 'Development', progress: 0, icon: <Code size={32} color="#3b82f6" /> },
];

export default function Dashboard({ onSelectCourse }) {
  return (
    <div className="dashboard-container animate-fade-in">
      <header className="dashboard-header">
        <h1 className="gradient-text title">EdTech Layers</h1>
        <p className="text-muted">Select a mentor layer to continue.</p>
      </header>

      <div className="course-grid">
        {layers.map(layer => (
          <div 
            key={layer.id} 
            className="glass-panel course-tile" 
            onClick={() => onSelectCourse(layer)}
          >
            <div className="course-icon-wrapper" style={{ backgroundColor: `${layer.icon.props.color}20` }}>
              {layer.icon}
            </div>
            <h3 className="course-title">{layer.title} Mentor</h3>
            <div className="progress-container">
              <div className="progress-bar-bg">
                <div 
                  className="progress-bar-fill" 
                  style={{ width: `${layer.progress}%`, backgroundColor: layer.icon.props.color }}
                ></div>
              </div>
              <span className="progress-text">Enter Layer</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
