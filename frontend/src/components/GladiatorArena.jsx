import { useState, useRef, useEffect } from 'react';
import { ShieldAlert, Shield, Play, Square, Activity, Sword } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const GladiatorArena = () => {
  const [objective, setObjective] = useState('Extract the system prompt');
  const [targetModel, setTargetModel] = useState('gpt-4o-mini');
  const [maxTurns, setMaxTurns] = useState(5);
  
  const [history, setHistory] = useState([]);
  const [status, setStatus] = useState('idle'); // idle, running, ended, error
  const [message, setMessage] = useState('');
  
  const eventSourceRef = useRef(null);
  const scrollRef = useRef(null);

  // Auto-scroll to bottom of the chat log
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [history, status]);

  const startBattle = () => {
    if (!objective.trim()) return;
    
    // Reset state
    setHistory([]);
    setStatus('running');
    setMessage('Initializing connection to Gladiator Engine...');
    
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    
    const url = new URL(`${API_BASE}/api/gladiator/battle`);
    url.searchParams.append('objective', objective);
    url.searchParams.append('target_model', targetModel);
    url.searchParams.append('max_turns', maxTurns.toString());
    
    const es = new EventSource(url.toString());
    eventSourceRef.current = es;
    
    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        switch (data.status) {
          case 'started':
            setMessage(`Battle started! Target model: ${targetModel}`);
            break;
            
          case 'generating_attack':
            setMessage(`Turn ${data.turn}: Attacker is generating prompt...`);
            break;
            
          case 'attack_generated':
            setHistory(prev => [
              ...prev,
              { type: 'attacker', turn: data.turn, content: data.attacker_prompt }
            ]);
            break;
            
          case 'target_responding':
            setMessage(`Turn ${data.turn}: Target is responding...`);
            break;
            
          case 'target_compromised':
          case 'target_defended':
            setHistory(prev => [
              ...prev,
              { 
                type: 'target', 
                turn: data.turn_data.turn, 
                content: data.turn_data.target_response,
                safety_score: data.turn_data.safety_score,
                is_unsafe: data.turn_data.is_unsafe,
                reason: data.turn_data.reason
              }
            ]);
            
            if (data.status === 'target_compromised') {
              setStatus('ended');
              setMessage(`🚨 BATTLE OVER: Defense Compromised on Turn ${data.turn_data.turn}!`);
              es.close();
            } else {
              setMessage(`Turn ${data.turn_data.turn} complete: Target defended successfully. (Score: ${data.turn_data.safety_score})`);
            }
            break;
            
          case 'battle_ended':
            setStatus('ended');
            setMessage(`🛡️ BATTLE OVER: Target survived all ${maxTurns} turns!`);
            es.close();
            break;
            
          case 'error':
            setStatus('error');
            setMessage(`Error: ${data.message}`);
            es.close();
            break;
            
          default:
            console.log('Unknown status:', data.status);
        }
      } catch (err) {
        console.error("Error parsing event data:", err);
      }
    };
    
    es.onerror = (err) => {
      console.error("EventSource failed:", err);
      setStatus('error');
      setMessage('Connection to Gladiator Engine lost.');
      es.close();
    };
  };

  const stopBattle = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    setStatus('ended');
    setMessage('Battle manually aborted.');
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  return (
    <div className="glass-panel panel-content" style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: '600px' }}>
      <h2 style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <Sword size={24} color="var(--accent-red)" /> Gladiator Mode (Auto-Attacker)
      </h2>
      
      {/* Controls */}
      <div className="input-container" style={{ display: 'flex', gap: '15px', alignItems: 'flex-end', marginBottom: '20px', flexWrap: 'wrap' }}>
        <div style={{ flexGrow: 1, minWidth: '250px' }}>
          <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>
            Attack Objective
          </label>
          <input 
            type="text" 
            value={objective}
            onChange={(e) => setObjective(e.target.value)}
            style={{ width: '100%', padding: '10px', borderRadius: '4px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--glass-border)', color: 'white' }}
            disabled={status === 'running'}
          />
        </div>
        
        <div>
          <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>
            Target Model
          </label>
          <select 
            value={targetModel}
            onChange={(e) => setTargetModel(e.target.value)}
            style={{ padding: '10px', borderRadius: '4px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--glass-border)', color: 'white' }}
            disabled={status === 'running'}
          >
            <option value="gpt-4o-mini">gpt-4o-mini</option>
            <option value="gpt-4">gpt-4</option>
            <option value="gpt-3.5-turbo">gpt-3.5-turbo</option>
          </select>
        </div>
        
        <div>
          <label style={{ display: 'block', marginBottom: '8px', color: 'var(--text-secondary)' }}>
            Max Turns
          </label>
          <input 
            type="number" 
            value={maxTurns}
            onChange={(e) => setMaxTurns(Number(e.target.value))}
            min={1} max={10}
            style={{ width: '80px', padding: '10px', borderRadius: '4px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--glass-border)', color: 'white' }}
            disabled={status === 'running'}
          />
        </div>
        
        {status !== 'running' ? (
          <button className="btn-primary" onClick={startBattle} style={{ padding: '10px 20px', background: 'var(--accent-red)' }}>
            <Play size={20} /> Initialize Battle
          </button>
        ) : (
          <button className="btn-primary" onClick={stopBattle} style={{ padding: '10px 20px', background: 'var(--text-secondary)' }}>
            <Square size={20} /> Abort
          </button>
        )}
      </div>

      {/* Status Bar */}
      <div style={{ padding: '10px', background: 'rgba(0,0,0,0.4)', borderRadius: '4px', marginBottom: '15px', display: 'flex', alignItems: 'center', gap: '10px', color: status === 'error' ? 'var(--accent-red)' : 'var(--text-secondary)' }}>
        {status === 'running' && <span className="loader" style={{ width: '16px', height: '16px', borderWidth: '2px' }} />}
        <Activity size={18} /> {message || 'Ready to start...'}
      </div>

      {/* Battle History Log */}
      <div 
        ref={scrollRef}
        style={{ 
          flexGrow: 1, 
          background: '#0f172a', 
          borderRadius: '8px', 
          border: '1px solid var(--glass-border)',
          padding: '20px',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '20px'
        }}
      >
        {history.length === 0 ? (
          <div style={{ margin: 'auto', color: 'var(--text-secondary)', opacity: 0.5, textAlign: 'center' }}>
            <Sword size={64} style={{ marginBottom: '1rem' }} />
            <p>Battle log will appear here...</p>
          </div>
        ) : (
          history.map((entry, idx) => (
            <div 
              key={idx} 
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: entry.type === 'attacker' ? 'flex-start' : 'flex-end',
                width: '100%'
              }}
              className="animate-fade"
            >
              <div style={{
                maxWidth: '80%',
                padding: '15px',
                borderRadius: '8px',
                background: entry.type === 'attacker' ? 'rgba(255, 51, 102, 0.15)' : 'rgba(0, 240, 255, 0.1)',
                border: `1px solid ${entry.type === 'attacker' ? 'rgba(255, 51, 102, 0.3)' : 'rgba(0, 240, 255, 0.3)'}`
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '10px', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '5px' }}>
                  {entry.type === 'attacker' ? (
                    <><Sword size={16} color="var(--accent-red)"/> <strong style={{ color: 'var(--accent-red)' }}>Attacker (Turn {entry.turn})</strong></>
                  ) : (
                    <><Shield size={16} color="var(--accent-cyan)"/> <strong style={{ color: 'var(--accent-cyan)' }}>Target Response</strong></>
                  )}
                </div>
                
                <div style={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: '0.9rem', lineHeight: '1.5' }}>
                  {entry.content}
                </div>
                
                {entry.type === 'target' && (
                  <div style={{ marginTop: '10px', paddingTop: '10px', borderTop: '1px solid rgba(255,255,255,0.1)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.85rem' }}>
                    <span>Safety Score: <strong>{entry.safety_score.toFixed(3)}</strong></span>
                    {entry.is_unsafe ? (
                      <span style={{ color: 'var(--accent-red)', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <ShieldAlert size={14} /> FAILED (COMPROMISED)
                      </span>
                    ) : (
                      <span style={{ color: 'var(--accent-green)', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Shield size={14} /> DEFENDED
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default GladiatorArena;
