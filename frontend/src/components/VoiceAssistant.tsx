'use client';

import { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Video, VideoOff, MessageSquare, ScreenShare, PhoneOff } from 'lucide-react';
import { useVoice } from '../lib/useVoice';
import { chatAPI } from '../lib/api';
import AudioVisualizer from './audioVisualizer';
import Image from 'next/image';
import FloatingVideoEye from './floatingVideo';

export default function VoiceAssistant() {
  const {
    isListening,
    isSpeaking,
    transcript,
    error: voiceError,
    startListening,
    stopListening,
    speak,
    isSupported,
  } = useVoice();

  const [conversationId, setConversationId] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentTranscript, setCurrentTranscript] = useState<string>('');
  const [agentResponse, setAgentResponse] = useState<string>('');
  const [cameraEnabled, setCameraEnabled] = useState(false);
  const [showTextInput, setShowTextInput] = useState(false);
  const [textInput, setTextInput] = useState('');
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

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

  // Camera handling
  useEffect(() => {
    if (cameraEnabled) {
      startCamera();
    } else {
      stopCamera();
    }

    return () => {
      stopCamera();
    };
  }, [cameraEnabled]);

  // Clear agent response when it stops speaking
  useEffect(() => {
    if (!isSpeaking && agentResponse) {
      // Keep response visible for 2 seconds after speaking ends
      const timer = setTimeout(() => {
        setAgentResponse('');
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [isSpeaking, agentResponse]);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { width: 320, height: 180 },
        audio: false 
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err) {
      console.error('Error accessing camera:', err);
      setCameraEnabled(false);
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  };

  const handleProcessVoice = async (message: string) => {
    if (!message.trim()) return;

    setIsProcessing(true);
    setAgentResponse(''); // Clear previous response

    try {
      const response = await chatAPI.send({
        message,
        conversation_id: conversationId || undefined,
      });

      if (!conversationId) {
        setConversationId(response.conversation_id);
      }

      // Set agent response for caption display
      setAgentResponse(response.response);
      
      // Speak the response
      speak(response.response);
      
    } catch (err: any) {
      console.error('Error:', err);
      const errorMsg = "I encountered an error. Please try again.";
      setAgentResponse(errorMsg);
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
      setAgentResponse(''); // Clear agent response when starting to listen
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

  const handleEndCall = () => {
    stopListening();
    stopCamera();
    window.location.reload();
  };

  if (!isSupported) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-black">
        <div className="text-center text-white p-8">
          <h2 className="text-2xl font-bold mb-4">Browser Not Supported</h2>
          <p className="text-gray-400">Please use Chrome, Edge, or Safari.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative flex flex-col min-h-screen bg-[#0a0a0a] text-white">
      <div className="absolute top-0 left-0 right-0 z-20 flex items-center justify-between px-6 py-4">
        <div className="flex items-center gap-3">
          {/* <Image 
            src="/assets/pixelated-logo.png" 
            alt="Bob Logo" 
            width={50}
            height={30}
            quality={100}
            className="rounded-lg"
          /> */}
          <Image 
            src="/assets/Bob.png" 
            alt="Bob Name" 
            width={110}
            height={90}
            quality={100}
            className="rounded-lg"
          />
        </div>

        {/* Built with tag */}
        <div className="text-[10px] text-gray-500 tracking-wider">
          Be careful with him, This thing can talk!
        </div>
      </div>

      {/* Main Content - Audio Visualizer */}
      <div className="flex-1 flex items-center justify-center">
        <AudioVisualizer 
          isActive={isListening || isSpeaking || isProcessing}
          mode={
            isListening ? 'listening' : 
            isSpeaking ? 'speaking' : 
            isProcessing ? 'processing' : 
            'idle'
          }
        />
      </div>

      <FloatingVideoEye />

      {/* Bottom Control Bar */}
      <div className="absolute bottom-0 left-0 right-0 z-30">
        <div className="w-full px-8 pb-8">
          <div className="flex items-center justify-between bg-[#1a1a1a]/95 backdrop-blur-xl rounded-3xl px-8 py-4 border border-white/10 shadow-2xl">
            
            {/* Left Section - Controls */}
            <div className="flex items-center gap-2">
              {/* Microphone with Dropdown */}
              <div className="flex items-center bg-[#2a2a2a] rounded-full">
                <button
                  onClick={handleVoiceToggle}
                  disabled={isProcessing || isSpeaking}
                  className={`p-4 rounded-l-full transition-all ${
                    isListening
                      ? 'bg-white/10 text-green-400'
                      : 'text-white hover:bg-white/5'
                  } disabled:opacity-50`}
                >
                  {isListening ? (
                    <Mic className="w-5 h-5" />
                  ) : (
                    <MicOff className="w-5 h-5" />
                  )}
                </button>
                <button className="px-2 py-4 rounded-r-full hover:bg-white/5 transition-all">
                  <svg className="w-3 h-3 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>

              {/* Camera with Dropdown */}
              <div className="flex items-center bg-[#2a2a2a] rounded-full">
                <button
                  onClick={() => setCameraEnabled(!cameraEnabled)}
                  className={`p-4 rounded-l-full transition-all ${
                    cameraEnabled
                      ? 'bg-white/10 text-white'
                      : 'text-white hover:bg-white/5'
                  }`}
                >
                  {cameraEnabled ? (
                    <Video className="w-5 h-5" />
                  ) : (
                    <VideoOff className="w-5 h-5" />
                  )}
                </button>
                <button className="px-2 py-4 rounded-r-full hover:bg-white/5 transition-all">
                  <svg className="w-3 h-3 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>

              {/* Screen Share */}
              <button className="p-4 bg-[#2a2a2a] rounded-full hover:bg-white/5 transition-all text-white">
                <ScreenShare className="w-5 h-5" />
              </button>

              {/* Text Chat */}
              <button
                onClick={() => setShowTextInput(!showTextInput)}
                className="p-4 bg-[#2a2a2a] rounded-full hover:bg-white/5 transition-all text-white"
              >
                <MessageSquare className="w-5 h-5" />
              </button>
            </div>

            {/* Right Section - End Call */}
            <button
              onClick={handleEndCall}
              className="flex items-center gap-3 px-8 py-4 bg-[#dc2626] hover:bg-[#b91c1c] rounded-full transition-all shadow-lg"
            >
              <PhoneOff className="w-5 h-5" />
              <span className="text-sm font-semibold tracking-wide">END CALL</span>
            </button>
          </div>
        </div>
      </div>

      {/* Text Input Modal */}
      {showTextInput && (
        <div className="absolute bottom-32 left-1/2 -translate-x-1/2 w-96 z-40">
          <div className="bg-[#1a1a1a] rounded-xl border border-gray-800 p-4 shadow-2xl">
            <form onSubmit={handleTextSubmit} className="flex gap-2">
              <input
                type="text"
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                placeholder="Type a message..."
                className="flex-1 bg-transparent border border-gray-700 rounded-lg px-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-gray-600"
                autoFocus
              />
              <button
                type="submit"
                disabled={!textInput.trim()}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                Send
              </button>
            </form>
          </div>
        </div>
      )}

      {/* User Transcript Display (what you said) */}
      {currentTranscript && !agentResponse && (
        <div className="absolute top-24 left-1/2 -translate-x-1/2 max-w-2xl w-full px-6 z-20">
          <div className="bg-black/80 backdrop-blur-sm border border-blue-800 rounded-lg px-6 py-4">
            <p className="text-sm text-blue-400 mb-1">You said:</p>
            <p className="text-white">{currentTranscript}</p>
          </div>
        </div>
      )}

      {/* Agent Response Display (what Bob is saying) */}
      {agentResponse && (isSpeaking || isProcessing) && (
        <div className="absolute top-24 left-1/2 -translate-x-1/2 max-w-2xl w-full px-6 z-20">
          <div className="bg-black/80 backdrop-blur-sm border border-green-800 rounded-lg px-6 py-4">
            <p className="text-sm text-green-400 mb-1">Bob:</p>
            <p className="text-white">{agentResponse}</p>
          </div>
        </div>
      )}

      {/* Status Indicator */}
      {(isListening || isSpeaking || isProcessing) && (
        <div className="absolute top-24 left-6 z-20">
          <div className="flex items-center gap-2 bg-black/80 backdrop-blur-sm border border-gray-800 rounded-full px-4 py-2">
            <div className={`w-2 h-2 rounded-full animate-pulse ${
              isListening ? 'bg-blue-500' : 
              isSpeaking ? 'bg-green-500' : 
              'bg-yellow-500'
            }`} />
            <span className="text-xs text-gray-400">
              {isListening ? 'Listening' : isSpeaking ? 'Speaking' : 'Processing'}
            </span>
          </div>
        </div>
      )}

      {/* Error Display */}
      {voiceError && (
        <div className="absolute top-6 left-1/2 -translate-x-1/2 z-50">
          <div className="bg-red-900/90 backdrop-blur-sm border border-red-700 rounded-lg px-6 py-3">
            <p className="text-red-200 text-sm">{voiceError}</p>
          </div>
        </div>
      )}
    </div>
  );
}