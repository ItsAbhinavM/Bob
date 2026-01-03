'use client';

import { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Video, VideoOff, MessageSquare, ScreenShare, PhoneOff } from 'lucide-react';
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
          <Image 
            src="/assets/pixelated-logo.png" 
            alt="Bob Logo" 
            width={50}
            height={30}
            quality={100}
            className="rounded-lg"
          />
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
          Voice assistant agent, This thing can talk!
        </div>
      </div>

      {/* Main Content - Audio Visualizer */}
      <div className="flex-1 flex items-center justify-center">
        {/* Audio Waveform Visualization */}
        <div className="flex items-center justify-center gap-2 h-48">
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              className={`bg-white rounded-full transition-all duration-150 ${
                isListening || isSpeaking || isProcessing ? 'animate-wave' : ''
              }`}
              style={{
                width: i === 2 ? '24px' : i === 1 || i === 3 ? '20px' : '16px',
                height: 
                  isListening || isSpeaking || isProcessing
                    ? i === 2 ? '160px' : i === 1 || i === 3 ? '120px' : '80px'
                    : i === 2 ? '120px' : i === 1 || i === 3 ? '80px' : '40px',
                animationDelay: `${i * 0.1}s`,
                opacity: isListening || isSpeaking || isProcessing ? 1 : 0.4,
              }}
            />
          ))}
        </div>
      </div>

      {/* User Camera Feed - Bottom Right */}
      <div className="absolute bottom-24 right-6 z-20">
        <div className="relative w-48 h-36 bg-gray-900 rounded-lg overflow-hidden border border-gray-800">
          {cameraEnabled ? (
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <div className="relative w-full h-full">
                <Image 
                  src="/assets/user.png" 
                  alt="Persona" 
                  fill
                  quality={100}
                  className="rounded-lg"
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Bottom Control Bar */}
      <div className="absolute bottom-0 left-0 right-0 z-30 pb-6">
        <div className="max-w-2xl mx-auto px-6">
          <div className="flex items-center justify-between bg-[#1a1a1a] rounded-2xl px-4 py-3 border border-gray-800">
            {/* Left Controls */}
            <div className="flex items-center gap-3">
              {/* Microphone */}
              <div className="relative">
                <button
                  onClick={handleVoiceToggle}
                  disabled={isProcessing || isSpeaking}
                  className={`p-3 rounded-lg transition-all ${
                    isListening
                      ? 'bg-transparent hover:bg-gray-800 border border-green-500'
                      : 'bg-transparent hover:bg-gray-800'
                  } disabled:opacity-50`}
                >
                  {isListening ? (
                    <Mic className="w-5 h-5" />
                  ) : (
                    <MicOff className="w-5 h-5" />
                  )}
                </button>
                {/* Dropdown indicator */}
                <button className="absolute -right-2 top-1/2 -translate-y-1/2 p-1">
                  <svg className="w-3 h-3 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>

              {/* Camera */}
              <div className="relative">
                <button
                  onClick={() => setCameraEnabled(!cameraEnabled)}
                  className="p-3 rounded-lg bg-transparent hover:bg-gray-800 transition-all"
                >
                  {cameraEnabled ? (
                    <Video className="w-5 h-5" />
                  ) : (
                    <VideoOff className="w-5 h-5" />
                  )}
                </button>
                <button className="absolute -right-2 top-1/2 -translate-y-1/2 p-1">
                  <svg className="w-3 h-3 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>

              <button className="p-3 rounded-lg bg-transparent hover:bg-gray-800 transition-all">
                <ScreenShare className="w-5 h-5" />
              </button>

              {/* Text Chat */}
              <button
                onClick={() => setShowTextInput(!showTextInput)}
                className="p-3 rounded-lg bg-transparent hover:bg-gray-800 transition-all"
              >
                <MessageSquare className="w-5 h-5" />
              </button>
            </div>

            {/* Right Control - End Call */}
            <button
              onClick={handleEndCall}
              className="flex items-center gap-2 px-5 py-2.5 bg-red-600 hover:bg-red-700 rounded-lg transition-all"
            >
              <PhoneOff className="w-4 h-4" />
              <span className="text-sm font-medium">END CALL</span>
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