'use client';

import { useState, useRef, useEffect } from 'react';

interface TextInputBarProps {
  onSubmit: (message: string) => void;
  isProcessing: boolean;
  onClose: () => void;
}

export default function TextInputBar({ onSubmit, isProcessing, onClose }: TextInputBarProps) {
  const [textInput, setTextInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-focus on mount
  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  // Auto-resize textarea
  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setTextInput(e.target.value);
    
    const textarea = e.target;
    textarea.style.height = 'auto';
    textarea.style.height = `${Math.min(textarea.scrollHeight, 160)}px`;
  };

  // Handle Enter to submit (Shift+Enter for new line)
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (textInput.trim()) {
        handleSubmit();
      }
    }
    
    // ESC to close
    if (e.key === 'Escape') {
      onClose();
    }
  };

  const handleSubmit = () => {
    if (textInput.trim() && !isProcessing) {
      onSubmit(textInput.trim());
      setTextInput('');
      
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
      
      onClose();
    }
  };

  return (
    <div className="absolute bottom-28 left-0 right-0 z-40 px-8 pb-5">
      <div className="max-w-4xl mx-auto">
        {/* Keyboard hints - Above input box */}
        <div className="flex items-center justify-center mb-2 gap-3 text-xs text-gray-500">
          <div className="flex items-center gap-1">
            <kbd className="px-2 py-1 border border-gray-500 rounded text-gray-400 font-mono text-[10px]">
              Enter
            </kbd>
            <span>to send</span>
          </div>
          <span className="text-gray-700">•</span>
          <div className="flex items-center gap-1">
            <kbd className="px-2 py-1  border border-gray-700 rounded text-gray-400 font-mono text-[10px]">
              Shift
            </kbd>
            <span>+</span>
            <kbd className="px-2 py-1  border border-gray-700 rounded text-gray-400 font-mono text-[10px]">
              Enter
            </kbd>
            <span>for new line</span>
          </div>
          <span className="text-gray-700">•</span>
          <div className="flex items-center gap-1">
            <kbd className="px-2 py-1  border border-gray-700 rounded text-gray-400 font-mono text-[10px]">
              Esc
            </kbd>
            <span>to close</span>
          </div>
        </div>

        <div className="relative bg-[#1a1a1a] rounded-2xl shadow-2xl border border-gray-800 overflow-hidden">
          <div className="flex items-end gap-2 p-2">
            <div className="flex-1 relative">
              <textarea
                ref={textareaRef}
                value={textInput}
                onChange={handleTextareaChange}
                onKeyDown={handleKeyDown}
                placeholder="Type your message..."
                rows={1}
                className="w-full bg-transparent text-white placeholder-gray-500 resize-none outline-none px-4 py-3 text-[15px] leading-relaxed max-h-40 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent"
                style={{
                  minHeight: '48px',
                  height: 'auto',
                }}
              />
            </div>

            <button
              onClick={handleSubmit}
              disabled={!textInput.trim() || isProcessing}
              className="flex-shrink-0 p-3 bg-white/10 hover:bg-white/20 rounded-xl transition-all disabled:opacity-40 disabled:cursor-not-allowed group relative"
              title="Send message (Enter)"
            >
              <svg 
                className="w-5 h-5 text-white group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" 
                />
              </svg>
            </button>
          </div>

          {/* Character count (shows when typing a lot) */}
          {textInput.length > 50 && (
            <div className="absolute bottom-2 right-16 text-[10px] text-gray-500 font-mono  px-2 py-0.5 rounded">
              {textInput.length}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}