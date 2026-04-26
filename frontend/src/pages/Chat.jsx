import { useState, useEffect } from 'react';
import axios from 'axios';
import LayersPanel from '../components/chat/LayersPanel';
import ChatBox from '../components/chat/ChatBox';

export default function ChatPage() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pipelineStatus, setPipelineStatus] = useState('idle'); // idle, processing, PASSED, BLOCKED
  const [blockedReason, setBlockedReason] = useState(null);

  useEffect(() => {
    // Load historical chats on page mount
    axios.get('http://127.0.0.1:8000/chat/history')
      .then(res => {
        setMessages(res.data);
      })
      .catch(err => console.error("Failed to load chat history:", err));
  }, []);

  const handleSendMessage = async (input) => {
    // 1. Add user message to UI immediately
    const userMsg = { role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);

    // 2. Set processing state
    setLoading(true);
    setPipelineStatus('processing');
    setBlockedReason(null);

    try {
      // 3. Hit the backend
      const res = await axios.post(`http://127.0.0.1:8000/chat`, { message: input });
      const data = res.data;

      // 4. Handle response
      setPipelineStatus(data.status);

      if (data.status === 'BLOCKED') {
        setBlockedReason(data.reason);
        setMessages(prev => [...prev, {
          role: 'system',
          content: 'Payload intercepted and destroyed by security pipeline.',
          status: 'BLOCKED',
          reason: data.reason
        }]);
      } else {
        setMessages(prev => [...prev, {
          role: 'system',
          content: data.response,
          status: 'PASSED'
        }]);
      }

    } catch (err) {
      const errorDetail = err.response?.data?.detail || err.message || 'Connection Error';
      console.error("Chat Error:", err);
      setPipelineStatus('BLOCKED');
      setMessages(prev => [...prev, {
        role: 'system',
        content: `System error during payload analysis: ${errorDetail}`,
        status: 'BLOCKED',
        reason: errorDetail
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleClearHistory = async () => {
    if (!window.confirm("Are you sure you want to clear your chat history? This cannot be undone.")) return;

    try {
      await axios.delete('http://127.0.0.1:8000/chat/history');
      setMessages([]);
    } catch (err) {
      console.error("Failed to clear history:", err);
      alert("Failed to clear chat history. See console for details.");
    }
  };

  return (
    <div className="flex h-full w-full bg-white dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
      <LayersPanel currentStatus={pipelineStatus} blockedReason={blockedReason} />
      <ChatBox
        messages={messages}
        onSendMessage={handleSendMessage}
        onClearHistory={handleClearHistory}
        loading={loading}
      />
    </div>
  );
}
