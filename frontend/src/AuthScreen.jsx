import React, { useState, useEffect } from 'react';
import { LogIn, Key, Link2, Mail, Lock } from 'lucide-react';
import { getSupabaseClient } from './supabaseClient';

export default function AuthScreen({ onAuthSuccess }) {
  const [url] = useState('https://doyxtvzfwjauhsfblxez.supabase.co');
  const [key] = useState('eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRveXh0dnpmd2phdWhzZmJseGV6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODEwODIwMDksImV4cCI6MjA5NjY1ODAwOX0._lvRibQwz6MzGPlyKy0UYqFjFbBLi_Req76CKIqKQis');
  const [email, setEmail] = useState(localStorage.getItem('sb_email') || '');
  const [pass, setPass] = useState(localStorage.getItem('sb_pass') || '');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleConnect = async (e) => {
    e.preventDefault();
    setError('');
    
    if (!url || !key || !email || !pass) {
      setError('Please fill in all fields.');
      return;
    }

    localStorage.setItem('sb_url', url);
    localStorage.setItem('sb_key', key);
    localStorage.setItem('sb_email', email);
    localStorage.setItem('sb_pass', pass);

    setLoading(true);

    try {
      const supabase = getSupabaseClient(url, key);
      let { data, error: signUpError } = await supabase.auth.signUp({ email, password: pass });
      
      if (signUpError && signUpError.message.includes('already registered')) {
        const signInRes = await supabase.auth.signInWithPassword({ email, password: pass });
        data = signInRes.data;
        if (signInRes.error) throw signInRes.error;
      } else if (signUpError) {
        throw signUpError;
      }
      
      onAuthSuccess({ session: data.session, url, key });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container animate-slide-up">
      <div className="glass-panel auth-panel">
        <h1 className="gradient-text title">Novox Mentor AI</h1>
        <p className="subtitle text-muted">Sign in to access the dashboard</p>
        
        <form onSubmit={handleConnect} className="auth-form">
          
          <div className="input-group">
            <Mail className="input-icon" size={20} />
            <input 
              type="email" 
              className="input-field pl-10" 
              placeholder="Test Email" 
              value={email} 
              onChange={e => setEmail(e.target.value)} 
            />
          </div>
          
          <div className="input-group">
            <Lock className="input-icon" size={20} />
            <input 
              type="password" 
              className="input-field pl-10" 
              placeholder="Test Password" 
              value={pass} 
              onChange={e => setPass(e.target.value)} 
            />
          </div>

          {error && <div className="error-message">{error}</div>}
          
          <button type="submit" className="btn-primary" disabled={loading}>
            <LogIn size={20} />
            {loading ? 'Connecting...' : 'Connect & Sign Up / In'}
          </button>
        </form>
      </div>
    </div>
  );
}
