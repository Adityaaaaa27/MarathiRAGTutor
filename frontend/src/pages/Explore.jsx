import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Sparkles } from 'lucide-react';
import './Explore.css';

const Explore = () => {
  const navigate = useNavigate();

  return (
    <div className="page-container grid-bg explore-container">
      <header className="explore-header desktop-header">
        <div className="logo-badge">
          <Sparkles size={16} color="var(--primary-yellow)" />
          <span>Marathi RAG Tutor</span>
        </div>
        <div className="avatar">
          <div className="avatar-img"></div>
        </div>
      </header>

      <main className="explore-main desktop-main">
        <div className="explore-left">
          <h1 className="explore-title">
            Explore Marathi Knowledge<br/>
            <span className="marathi-title">मराठी ज्ञान शोधा</span>
          </h1>

          <button className="primary-btn new-chat-btn" onClick={() => navigate('/chat')}>
            <span>New Chat</span>
            <div className="icon-circle">
              <ArrowRight size={18} />
            </div>
          </button>
        </div>

        <div className="explore-right">
          <section className="section-container">
            <div className="section-header">
              <h2>Chat history (चॅट इतिहास)</h2>
              <button className="see-all">See All</button>
            </div>
            <div className="history-tags">
              <span className="history-tag">संत तुकाराम अभंग अर्थ</span>
              <span className="history-tag">Marathi Vyakaran: Samas</span>
              <span className="history-tag">शिवाजी महाराज इतिहास</span>
              <span className="history-tag">Poem summary Std 6</span>
            </div>
          </section>

          <section className="section-container">
            <div className="section-header">
              <h2>Popular Prompts (लोकप्रिय प्रश्न)</h2>
            </div>
            
            <div className="prompt-cards desktop-cards">
              <div className="prompt-card pink-card" onClick={() => navigate('/chat')}>
                <h3>Explain the meaning of 'Balakavi' poems</h3>
                <p>Standard 6 Marathi Textbook</p>
                <div className="card-decoration">
                  <Sparkles size={16} />
                </div>
                <button className="use-prompt-btn">Use this prompt</button>
              </div>
              
              <div className="prompt-card green-card" onClick={() => navigate('/chat')}>
                <h3>Give the summary of Chapter 4</h3>
                <p>Std 6 History & Civics</p>
                <div className="card-decoration">
                  <Sparkles size={16} />
                </div>
                <button className="use-prompt-btn">Use this prompt</button>
              </div>
            </div>
          </section>
        </div>
      </main>
    </div>
  );
};

export default Explore;
