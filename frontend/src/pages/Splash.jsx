import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Sparkles } from 'lucide-react';
import './Splash.css';

const Splash = () => {
  const navigate = useNavigate();

  return (
    <div className="page-container grid-bg splash-container">
      <header className="splash-header">
        <div className="logo-badge">
          <Sparkles size={16} color="var(--primary-yellow)" />
          <span>Marathi RAG Tutor</span>
        </div>
      </header>

      <main className="splash-main">
        <div className="splash-content">
          <h1 className="splash-title">
            The best AI Marathi Tutor<br/>
            <span className="marathi-title">जगातील सर्वोत्तम एआय मराठी शिक्षक</span>
          </h1>
          <p className="splash-subtitle">
            Master the Marathi language with an intelligent textbook-based AI tutor. Reliable, grounded, and easy to use.
          </p>
          <button className="primary-btn mt-6" onClick={() => navigate('/explore')}>
            <span>Start learning now</span>
            <div className="icon-circle">
              <ArrowRight size={18} />
            </div>
          </button>
        </div>

        <div className="illustrations-container">
          <div className="stamp stamp-1">
            <div className="stamp-inner">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"></path></svg>
            </div>
          </div>
          <div className="stamp stamp-2">
             <div className="stamp-inner dark">
               <span style={{ fontSize: '32px' }}>अ</span>
             </div>
          </div>
          <div className="stamp stamp-3">
             <div className="stamp-inner landscape">
               <svg width="60" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M12 20h9"></path><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"></path></svg>
             </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Splash;
