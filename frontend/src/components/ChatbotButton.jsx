import React, { useState } from 'react';
import Chatbot from './Chatbot';
import './ChatbotButton.css';

const ChatbotButton = () => {
  const [isChatOpen, setIsChatOpen] = useState(false);

  const toggleChat = () => {
    setIsChatOpen(!isChatOpen);
  };

  return (
    <>
      <button 
        className="chatbot-button"
        onClick={toggleChat}
        title="Open Finance Assistant"
      >
        💬
      </button>
      <Chatbot isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />
    </>
  );
};

export default ChatbotButton;
