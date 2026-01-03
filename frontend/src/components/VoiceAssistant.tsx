'use client';

import { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Settings, MessageSquare } from 'lucide-react';
import { useVoice } from '../lib/useVoice';
import { chatAPI } from '../lib/api';
import Image from 'next/image';

export default function VoiceAssistant() {
  const {
    isListening,
    isSpeaking,
    transcript,
    error: voiceError,
    startListening,
    stopListening,
    speak,
    stopSpeaking,
    isSupported,
  } = useVoice();

  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentTranscript, setCurrentTranscript] = useState<string>('');
  const [lastResponse, setLastResponse] = useState<string>('');
  const [showTextInput, setShowTextInput] = useState(false);
  const [textInput, setTextInput] = useState('');
  const [visualizerActive, setVisualizerActive] = useState(false);
  const [conversationLog, setConversationLog] = useState<Array<{role: string, text: string, timestamp: Date}>>([]);

  useEffect(() => {
    if (transcript && transcript !== currentTranscript) {
      setCurrentTranscript(transcript);
    }
  }, [transcript]);

  useEffect(() => {
    if (currentTranscript && !isListening && !isProcessing) {
      const timer = setTimeout(() => {
        handleProcessVoice(currentTranscript);
        setCurrentTranscript('');
      }, 800);
      return () => clearTimeout(timer);
    }
  }, [currentTranscript, isListening, isProcessing]);

  useEffect(() => {
    setVisualizerActive(isListening || isSpeaking || isProcessing);
  }, [isListening, isSpeaking, isProcessing]);

  const handleProcessVoice = async (message: string) => {
    if (!message.trim()) return;

    setIsProcessing(true);
    
    // Log user message
    setConversationLog(prev => [...prev, {
      role: 'user',
      text: message,
      timestamp: new Date()
    }]);

    try {
      const response = await chatAPI.send({
        message,
        conversation_id: conversationId || undefined,
      });

      if (!conversationId) {
        setConversationId(response.conversation_id);
      }

      setLastResponse(response.response);
      
      // Log assistant response
      setConversationLog(prev => [...prev, {
        role: 'assistant',
        text: response.response,
        timestamp: new Date()
      }]);

      // Speak response
      speak(response.response);
      
    } catch (err: any) {
      console.error('Error:', err);
      const errorMsg = "I encountered an error. Please try again.";
      setLastResponse(errorMsg);
      speak(errorMsg);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleVoiceToggle = () => {
    if (isListening) {
      stopListening();
    } else {
      setCurrentTranscript('');
      setLastResponse('');
      startListening();
    }
  };

  const handleTextSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (textInput.trim()) {
      handleProcessVoice(textInput);
      setTextInput('');
      setShowTextInput(false);
    }
  };

  if (!isSupported) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-900">
        <div className="text-center text-white p-8 bg-red-900/30 rounded-lg max-w-md">
          <h2 className="text-2xl font-bold mb-4">Browser Not Supported</h2>
          <p className="text-gray-300">
            Please use Chrome, Edge, or Safari for voice features.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen bg-black text-white">
      {/* Header */}
      <header className="flex items-center justify-between px-8 py-4 border-b border-gray-800">
        <div className="flex items-center gap-3">
            <Image src={'/assets/bob-logo.png'} alt='logo image' width={50} height={30} className='rounded-lg'/>
          <div>
            <h1 className="text-lg font-semibold">Bob</h1>
            <p className="text-xs text-gray-400">I can talk</p>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <button
            onClick={() => setShowTextInput(!showTextInput)}
            className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
            title="Text input"
          >
            <MessageSquare className="w-5 h-5 text-gray-400" />
          </button>
          <button className="p-2 hover:bg-gray-800 rounded-lg transition-colors">
            <Settings className="w-5 h-5 text-gray-400" />
          </button>
        </div>
      </header>

      {/* Main Voice Interface */}
      <div className="flex-1 flex flex-col items-center justify-center p-8">
        {/* Status Text */}
        <div className="mb-8 text-center">
          <p className="text-sm text-gray-400 mb-2">
            {isListening ? 'Listening...' : 
             isSpeaking ? 'Bob is speaking...' :
             isProcessing ? 'Processing...' :
             'Ready to assist'}
          </p>
          
          {/* Current Transcript Display */}
          {currentTranscript && (
            <div className="mt-4 px-6 py-3 bg-blue-900/30 border border-blue-700/50 rounded-lg max-w-2xl">
              <p className="text-blue-200 italic">"{currentTranscript}"</p>
            </div>
          )}
          
          {/* Last Response Display */}
          {lastResponse && !currentTranscript && (
            <div className="mt-4 px-6 py-3 bg-gray-800/50 border border-gray-700 rounded-lg max-w-2xl">
              <p className="text-gray-200">{lastResponse}</p>
            </div>
          )}
        </div>

        {/* Audio Visualizer / Avatar */}
        <div className="relative mb-12">
          {/* Animated circles when active */}
          {visualizerActive && (
            <>
              <div className="absolute inset-0 -m-8 bg-blue-500/20 rounded-full animate-ping" />
              <div className="absolute inset-0 -m-4 bg-blue-500/30 rounded-full animate-pulse" />
            </>
          )}
          
          {/* Center Circle */}
          <div className={`relative w-48 h-48 rounded-full flex items-center justify-center transition-all duration-300 ${
            visualizerActive 
              ? 'bg-gradient-to-br from-blue-500 to-purple-600 shadow-2xl shadow-blue-500/50' 
              : 'bg-gray-800 border-4 border-gray-700'
          }`}>
            {/* Waveform visualization */}
            {visualizerActive ? (
              <div className="flex items-center gap-1 h-16">
                {[...Array(5)].map((_, i) => (
                  <div
                    key={i}
                    className="w-1 bg-white rounded-full animate-pulse"
                    style={{
                      height: `${20 + Math.random() * 40}px`,
                      animationDelay: `${i * 0.1}s`,
                      animationDuration: '0.6s'
                    }}
                  />
                ))}
              </div>
            ) : (
              <div className="text-6xl">🎙️</div>
            )}
          </div>
        </div>

        {/* Main Microphone Button */}
        <button
          onClick={handleVoiceToggle}
          disabled={isProcessing || isSpeaking}
          className={`relative px-12 py-4 rounded-full font-semibold text-lg transition-all duration-300 ${
            isListening
              ? 'bg-red-600 hover:bg-red-700 shadow-lg shadow-red-500/50'
              : 'bg-blue-600 hover:bg-blue-700 shadow-lg shadow-blue-500/50'
          } disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          <div className="flex items-center gap-3">
            {isListening ? (
              <>
                <MicOff className="w-6 h-6" />
                <span>Stop Listening</span>
              </>
            ) : (
              <>
                <Mic className="w-6 h-6" />
                <span>Start Conversation</span>
              </>
            )}
          </div>
        </button>

        {/* Helper Text */}
        {!isListening && !isProcessing && !isSpeaking && (
          <div className="mt-8 text-center text-gray-400 text-sm max-w-md">
            <p>Click the button and speak naturally.</p>
            <p className="mt-2">Try: "What's the weather?" or "Add a task to buy groceries"</p>
          </div>
        )}

        {/* Text Input (Hidden by default) */}
        {showTextInput && (
          <form onSubmit={handleTextSubmit} className="mt-8 w-full max-w-2xl">
            <div className="flex gap-2 bg-gray-800 rounded-lg p-2 border border-gray-700">
              <input
                type="text"
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                placeholder="Type your message..."
                className="flex-1 bg-transparent px-4 py-2 text-white placeholder-gray-500 focus:outline-none"
                autoFocus
              />
              <button
                type="submit"
                disabled={!textInput.trim()}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Send
              </button>
            </div>
          </form>
        )}
      </div>

      {/* Conversation Log (Collapsible) */}
      {conversationLog.length > 0 && (
        <div className="border-t border-gray-800 bg-gray-900/50">
          <details className="group">
            <summary className="px-8 py-4 cursor-pointer text-sm text-gray-400 hover:text-gray-300 flex items-center justify-between">
              <span>Conversation History ({conversationLog.length} messages)</span>
              <span className="group-open:rotate-180 transition-transform">▼</span>
            </summary>
            <div className="px-8 pb-4 max-h-64 overflow-y-auto space-y-2">
              {conversationLog.map((msg, idx) => (
                <div
                  key={idx}
                  className={`text-xs p-3 rounded ${
                    msg.role === 'user' 
                      ? 'bg-blue-900/30 text-blue-200' 
                      : 'bg-gray-800 text-gray-300'
                  }`}
                >
                  <span className="font-semibold">
                    {msg.role === 'user' ? 'You' : 'Bob'}:
                  </span>{' '}
                  {msg.text}
                </div>
              ))}
            </div>
          </details>
        </div>
      )}

      {/* Error Display */}
      {voiceError && (
        <div className="fixed bottom-4 right-4 bg-red-900/90 border border-red-700 rounded-lg px-6 py-3 max-w-md">
          <p className="text-red-200 text-sm">{voiceError}</p>
        </div>
      )}
    </div>
  );
}