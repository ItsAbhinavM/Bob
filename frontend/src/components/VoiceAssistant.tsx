'use client';

import { useState, useEffect } from 'react';
import { Mic, MicOff, Volume2, VolumeX, Loader2, Send } from 'lucide-react';
import { useVoice } from '../lib/useVoice';
import { chatAPI } from '../lib/api';

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
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant'; content: string }>>([]);
  const [error, setError] = useState<string | null>(null);
  const [currentTranscript, setCurrentTranscript] = useState<string>('');
  const [textInput, setTextInput] = useState<string>('');

  useEffect(() => {
    if (transcript && transcript !== currentTranscript) {
      setCurrentTranscript(transcript);
    }
  }, [transcript]);

  useEffect(() => {
    // Auto-submit after transcript is complete (when listening stops)
    if (currentTranscript && !isListening && !isProcessing) {
      const timer = setTimeout(() => {
        handleSendMessage(currentTranscript);
        setCurrentTranscript('');
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [currentTranscript, isListening, isProcessing]);

  const handleSendMessage = async (message: string) => {
    if (!message.trim()) return;

    setIsProcessing(true);
    setError(null);

    setMessages((prev) => [...prev, { role: 'user', content: message }]);

    try {
      const response = await chatAPI.send({
        message,
        conversation_id: conversationId || undefined,
      });

      if (!conversationId) {
        setConversationId(response.conversation_id);
      }

      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: response.response },
      ]);

      speak(response.response);
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to process message';
      setError(errorMessage);
      console.error('Error processing message:', err);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleVoiceToggle = () => {
    if (isListening) {
      stopListening();
    } else {
      setCurrentTranscript('');
      startListening();
    }
  };

  const handleSpeakToggle = () => {
    if (isSpeaking) {
      stopSpeaking();
    }
  };

  const handleTextSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (textInput.trim()) {
      handleSendMessage(textInput);
      setTextInput('');
    }
  };

  if (!isSupported) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-900">
        <div className="text-center text-white p-8 bg-red-900/30 rounded-lg max-w-md">
          <h2 className="text-2xl font-bold mb-4">Browser Not Supported</h2>
          <p className="text-gray-300">
            Your browser doesn't support the Web Speech API. Please use Chrome, Edge, or Safari.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900">
      <header className="bg-black/30 backdrop-blur-sm border-b border-white/10 px-6 py-4">
        <h1 className="text-2xl font-bold text-white">Bob - Voice AI Assistant</h1>
        <p className="text-gray-400 text-sm">Powered by Google Gemini</p>
      </header>

      <div className="flex-1 overflow-y-auto px-6 py-8 space-y-4">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center text-gray-400">
              <Mic className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p className="text-lg mb-2">Click the microphone to start talking</p>
              <p className="text-sm text-gray-500 mb-4">Or type your message below</p>
              <div className="bg-white/5 rounded-lg p-4 max-w-md mx-auto text-left">
                <p className="text-sm font-semibold mb-2">Try saying:</p>
                <ul className="text-sm space-y-1 text-gray-400">
                  <li>• "What's the weather in London?"</li>
                  <li>• "Add a task to buy groceries"</li>
                  <li>• "Show me my tasks"</li>
                  <li>• "What is artificial intelligence?"</li>
                </ul>
              </div>
            </div>
          </div>
        ) : (
          messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[70%] rounded-2xl px-6 py-3 ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white/10 text-gray-100 backdrop-blur-sm'
                }`}
              >
                <p className="text-sm font-medium mb-1 opacity-70">
                  {msg.role === 'user' ? 'You' : 'Bob'}
                </p>
                <p className="whitespace-pre-wrap">{msg.content}</p>
              </div>
            </div>
          ))
        )}

        {/* Show what's being transcribed in real-time */}
        {isListening && currentTranscript && (
          <div className="flex justify-end">
            <div className="max-w-[70%] rounded-2xl px-6 py-3 bg-blue-500/50 text-white border-2 border-blue-400">
              <p className="text-sm font-medium mb-1 opacity-70">Listening...</p>
              <p className="whitespace-pre-wrap italic">{currentTranscript}</p>
            </div>
          </div>
        )}

        {isProcessing && (
          <div className="flex justify-start">
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl px-6 py-3">
              <div className="flex items-center space-x-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                <p className="text-gray-300">Bob is thinking...</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {(error || voiceError) && (
        <div className="mx-6 mb-4 p-4 bg-red-900/30 border border-red-500/50 rounded-lg">
          <p className="text-red-200 text-sm">{error || voiceError}</p>
        </div>
      )}

      {/* Text Input Form */}
      <div className="px-6 pb-4">
        <form onSubmit={handleTextSubmit} className="flex gap-2">
          <input
            type="text"
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            placeholder="Or type your message here..."
            disabled={isProcessing || isListening}
            className="flex-1 px-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!textInput.trim() || isProcessing || isListening}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg text-white font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>

      {/* Voice Controls */}
      <div className="bg-black/30 backdrop-blur-sm border-t border-white/10 px-6 py-6">
        <div className="flex items-center justify-center space-x-6">
          <button
            onClick={handleVoiceToggle}
            disabled={isProcessing || isSpeaking}
            className={`relative p-6 rounded-full transition-all duration-300 ${
              isListening
                ? 'bg-red-600 hover:bg-red-700 shadow-lg shadow-red-500/50 animate-pulse-slow'
                : 'bg-blue-600 hover:bg-blue-700 shadow-lg shadow-blue-500/50'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            {isListening ? (
              <MicOff className="w-8 h-8 text-white" />
            ) : (
              <Mic className="w-8 h-8 text-white" />
            )}
            {isListening && (
              <span className="absolute -top-2 -right-2 w-4 h-4 bg-red-500 rounded-full animate-ping" />
            )}
          </button>

          <button
            onClick={handleSpeakToggle}
            disabled={!isSpeaking}
            className={`p-6 rounded-full transition-all duration-300 ${
              isSpeaking
                ? 'bg-green-600 hover:bg-green-700 shadow-lg shadow-green-500/50'
                : 'bg-gray-700 opacity-50'
            } disabled:cursor-not-allowed`}
          >
            {isSpeaking ? (
              <Volume2 className="w-8 h-8 text-white animate-pulse" />
            ) : (
              <VolumeX className="w-8 h-8 text-gray-400" />
            )}
          </button>
        </div>

        <div className="text-center mt-4">
          <p className="text-gray-300 text-sm font-medium">
            {isListening
              ? '🎤 Listening... Speak now'
              : isSpeaking
              ? '🔊 Bob is speaking...'
              : isProcessing
              ? '⏳ Processing your request...'
              : '💡 Click microphone or type below'}
          </p>
          {isListening && (
            <p className="text-gray-400 text-xs mt-1">
              Stop speaking to automatically submit
            </p>
          )}
        </div>
      </div>
    </div>
  );
}