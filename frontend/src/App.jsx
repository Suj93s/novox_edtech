import React, { useState } from 'react';
import AuthScreen from './AuthScreen';
import Dashboard from './Dashboard';
import ChatScreen from './ChatScreen';
import './App.css';

export default function App() {
  const [sessionData, setSessionData] = useState(null);
  const [selectedCourse, setSelectedCourse] = useState(null);

  const handleAuthSuccess = (data) => {
    setSessionData(data);
  };

  const handleSelectCourse = (course) => {
    setSelectedCourse(course);
  };

  const handleBackToDashboard = () => {
    setSelectedCourse(null);
  };

  return (
    <div className="app-root">
      {!sessionData ? (
        <AuthScreen onAuthSuccess={handleAuthSuccess} />
      ) : !selectedCourse ? (
        <Dashboard onSelectCourse={handleSelectCourse} />
      ) : (
        <ChatScreen 
          course={selectedCourse} 
          session={sessionData.session} 
          url={sessionData.url} 
          onBack={handleBackToDashboard} 
        />
      )}
    </div>
  );
}
