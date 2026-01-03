'use client';
import { useState } from "react";
import VideoEye from "./videoDisplay";
import { Eye, Minus } from "lucide-react";

export default function FloatingVideoEye() {
    const [open, setOpen] = useState(false);
  
    return (
      <div className="absolute bottom-40 right-6 z-20 flex flex-col items-end gap-3">
        
        <button
            onClick={() => setOpen(prev => !prev)}
            className="w-10 h-10 flex items-center justify-center rounded-xl
                    hover:bg-gray-700 transition"
            aria-label={open ? "Minimize video" : "Show video"}
        >
            {open ? <Minus size={18} /> : <Eye size={20} />}
        </button>
  
        {open && (
          <div className="relative w-48 h-36 bg-gray-900 rounded-full overflow-hidden border-4 border-gray-700">
            <VideoEye />
          </div>
        )}
      </div>
    );
  }
  