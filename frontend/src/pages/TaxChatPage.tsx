import React, { useState, useRef, useEffect } from 'react';
import { useTax } from '../context/TaxContext';
import { api } from '../api/client';
import {
  MessageSquare,
  Send,
  Sparkles,
  Bot,
  User,
  ShieldAlert,
  BookOpen,
} from 'lucide-react';

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  citations?: string[];
  disclaimer?: string;
  timestamp: string;
}

export const TaxChatPage: React.FC = () => {
  const { financialYear, regime } = useTax();

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      text: `Hello! I am your explainable Indian Tax Assistant for FY ${financialYear}. I can explain why a specific regime won for you, provide step-by-step HRA calculations, explain Section 80C/80D/80CCD rules, or analyze your tax savings. How can I help you today?`,
      citations: ['Income-tax Act, 1961', 'Income-tax Act, 2025', 'Finance Act 2024/2025/2026'],
      disclaimer: 'Estimate only; not professional tax advice.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);

  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const quickPrompts = [
    'Why did the New Regime win for me?',
    'How is my Section 10(13A) HRA exemption calculated?',
    'Explain difference between 80CCD(1B) and 80CCD(2)',
    'How does Section 87A rebate and marginal relief work?',
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (messageText?: string) => {
    const textToSend = messageText || input;
    if (!textToSend.trim()) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!messageText) setInput('');
    setIsSending(true);

    try {
      const res = await api.chat.ask(textToSend, financialYear, regime);
      const botMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: res.answer,
        citations: res.citations,
        disclaimer: res.disclaimer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        text: 'I encountered an error retrieving your tax breakdown. Please ensure your profile is refreshed.',
        disclaimer: 'Estimate only; not professional tax advice.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="space-y-4 max-w-4xl mx-auto flex flex-col h-[calc(100vh-170px)]">
      {/* Header */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-indigo-100 text-indigo-700">
            <MessageSquare className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-slate-800">
              Tax-Grounded Explainable Chat Assistant
            </h1>
            <p className="text-[11px] text-slate-400">
              Answers are strictly grounded in your computed records and statutory JSON configs.
            </p>
          </div>
        </div>
        <span className="text-[10px] bg-slate-100 text-slate-700 font-semibold px-2 py-0.5 rounded">
          FY {financialYear} • {regime.toUpperCase()} Regime
        </span>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 bg-white rounded-xl border border-slate-200 shadow-2xs p-4 overflow-y-auto space-y-4">
        {messages.map((m) => {
          const isUser = m.sender === 'user';
          return (
            <div
              key={m.id}
              className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
            >
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 text-xs font-bold ${
                  isUser ? 'bg-indigo-600 text-white' : 'bg-indigo-100 text-indigo-700'
                }`}
              >
                {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              <div
                className={`max-w-xl rounded-xl p-3.5 text-xs space-y-2 leading-relaxed ${
                  isUser
                    ? 'bg-indigo-600 text-white rounded-tr-none'
                    : 'bg-slate-50 border border-slate-200/80 text-slate-800 rounded-tl-none'
                }`}
              >
                <p className="whitespace-pre-line">{m.text}</p>

                {m.citations && m.citations.length > 0 && (
                  <div className="pt-2 border-t border-slate-200/60 text-[10px] text-slate-500 space-y-0.5">
                    <div className="flex items-center gap-1 font-semibold text-slate-700">
                      <BookOpen className="w-3 h-3 text-indigo-600" />
                      <span>Statutory Citations:</span>
                    </div>
                    <div className="flex flex-wrap gap-1 mt-0.5">
                      {m.citations.map((c, i) => (
                        <span key={i} className="bg-white border px-1.5 py-0.5 rounded text-slate-600">
                          {c}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {m.disclaimer && (
                  <p className="text-[10px] text-slate-400 italic pt-1 border-t border-slate-100">
                    {m.disclaimer}
                  </p>
                )}

                <span
                  className={`text-[9px] block text-right ${
                    isUser ? 'text-indigo-200' : 'text-slate-400'
                  }`}
                >
                  {m.timestamp}
                </span>
              </div>
            </div>
          );
        })}
        {isSending && (
          <div className="flex items-center gap-2 text-xs text-slate-400 p-2">
            <Bot className="w-4 h-4 animate-bounce text-indigo-600" />
            <span>Consulting statutory engine and formula traces...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Quick Prompt Pills */}
      <div className="flex flex-wrap gap-2">
        {quickPrompts.map((p, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(p)}
            disabled={isSending}
            className="text-[11px] font-medium px-3 py-1 bg-white hover:bg-indigo-50 hover:text-indigo-700 hover:border-indigo-200 border border-slate-200 rounded-full transition-colors text-slate-600 shadow-2xs cursor-pointer"
          >
            {p}
          </button>
        ))}
      </div>

      {/* Input Box */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="flex items-center gap-2 bg-white p-2 rounded-xl border border-slate-200 shadow-2xs"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask anything about your income, deductions, or regime choice..."
          className="flex-1 text-xs p-2 focus:outline-none"
        />
        <button
          type="submit"
          disabled={isSending || !input.trim()}
          className="p-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg shadow-xs transition-colors disabled:opacity-40 cursor-pointer"
          title="Send message"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};
