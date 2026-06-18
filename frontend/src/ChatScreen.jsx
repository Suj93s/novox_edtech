import React, { useState, useEffect, useRef } from 'react';
import { ArrowLeft, Send, Loader2, Bot, User } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

export default function ChatScreen({ course, session, url, onBack }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [moduleData, setModuleData] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // Initialize session and load module data
  useEffect(() => {
    async function initSession() {
      try {
        const { createClient } = await import('@supabase/supabase-js');
        const anonKey = localStorage.getItem('sb_key');
        const supabase = createClient(url, anonKey, {
          global: { headers: { Authorization: `Bearer ${session.access_token}` } }
        });
        
        // 1. Fetch the master module for this course
        const { data: fetchedModule, error: modError } = await supabase
          .from('novox_curriculum')
          .select('*')
          .eq('course_name', course.title)
          .single();

        if (modError || !fetchedModule) {
            console.error("Failed to fetch master track for course");
            return;
        }
        setModuleData(fetchedModule);
        setMessages([{ id: 'initial', role: 'ai', text: `Welcome to the ${fetchedModule.module_title}! I am your AI Mentor. How can I help you today?` }]);

        let currentId = null;
        const { data: existingSession } = await supabase
          .from('chat_sessions')
          .select('id')
          .eq('course_name', course.title)
          .eq('module_id', fetchedModule.id)
          .order('created_at', { ascending: false })
          .limit(1)
          .maybeSingle();

        if (existingSession) {
          currentId = existingSession.id;
        } else {
          const { data: newSession } = await supabase
            .from('chat_sessions')
            .insert({ course_name: course.title, user_id: session.user.id, module_id: fetchedModule.id })
            .select()
            .single();
          if (newSession) currentId = newSession.id;
        }

        if (currentId) {
          setSessionId(currentId);
        }
      } catch (err) {
        console.error("Failed to load session:", err);
      }
    }
    initSession();
  }, [course.title, url, session]);

  const handleSend = async (e) => {
    if (e) e.preventDefault();
    if (!input.trim() || isTyping || !sessionId || !moduleData) return;

    const userMsg = input.trim();
    setInput('');
    const newMessages = [...messages, { id: Date.now().toString(), role: 'user', text: userMsg }];
    setMessages(newMessages);
    setIsTyping(true);

    const aiMessageId = 'ai-' + Date.now();
    setMessages(prev => [...prev, { id: aiMessageId, role: 'ai', text: '' }]);

    try {
      const response = await fetch(`${url}/functions/v1/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({ message: userMsg, session_id: sessionId, course_name: course.title, module_id: moduleData.id })
      });

      if (!response.ok) {
        const errText = await response.text();
        setMessages(prev => prev.map(m => m.id === aiMessageId ? { ...m, text: "Error: " + errText } : m));
        setIsTyping(false);
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let aiText = '';
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();
        
        for (const line of lines) {
          if (line.trim() === '') continue;
          
          if (line.startsWith('data: ')) {
            const dataStr = line.replace('data: ', '').trim();
            if (dataStr === '[DONE]') continue;
            try {
              const data = JSON.parse(dataStr);
              if (data.error) {
                const errMsg = data.error.message || JSON.stringify(data.error);
                aiText += `\n[Error: ${errMsg}]`;
                setMessages(prev => prev.map(m => m.id === aiMessageId ? { ...m, text: aiText } : m));
                continue;
              }
              const textPart = data.choices?.[0]?.delta?.content || '';
              if (textPart) {
                aiText += textPart;
                setMessages(prev => prev.map(m => m.id === aiMessageId ? { ...m, text: aiText } : m));
              }
            } catch(err) {
              console.error("Failed to parse JSON:", dataStr, err);
            }
          }
        }
      }

      if (aiText === '') {
        setMessages(prev => prev.map(m => m.id === aiMessageId ? { ...m, text: "Error: Received empty response." } : m));
      }
    } catch (error) {
      setMessages(prev => prev.map(m => m.id === aiMessageId ? { ...m, text: "Error connecting to Edge Function: " + error.message } : m));
    } finally {
      setIsTyping(false);
    }
  };

  if (!moduleData) {
    return (
      <div className="chat-container animate-fade-in" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        <Loader2 className="spinning" size={48} color="#94a3b8" />
      </div>
    );
  }

  return (
    <div className="chat-container animate-fade-in">
      <div className="glass-panel chat-panel">
        <div className="chat-header">
          <button className="icon-btn" onClick={onBack}>
            <ArrowLeft size={24} />
          </button>
          <div className="chat-title-info">
            <h2>{moduleData.module_title}</h2>
            <div className="online-status">
              <span className="status-dot"></span> Online
            </div>
          </div>
        </div>

        <div className="chat-messages">
          {messages.map(m => (
            <div key={m.id} className={`message-wrapper ${m.role}`}>
              <div className="avatar">
                {m.role === 'ai' ? <Bot size={20} /> : <User size={20} />}
              </div>
              <div className="message-content">
                {m.text ? (
                  <ReactMarkdown>{m.text}</ReactMarkdown>
                ) : (
                  m.role === 'ai' && m.id.startsWith('ai-') && <Loader2 className="spinning" size={16} />
                )}
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={handleSend} className="chat-input-area">
          <input 
            type="text" 
            className="input-field chat-input" 
            placeholder="Ask your mentor anything..." 
            value={input}
            onChange={e => setInput(e.target.value)}
            disabled={isTyping}
          />
          <button type="submit" className="send-btn" disabled={isTyping || !input.trim() || !sessionId}>
            {isTyping ? <Loader2 className="spinning" size={20} /> : <Send size={20} />}
          </button>
        </form>
      </div>
    </div>
  );
}
