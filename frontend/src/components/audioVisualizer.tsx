'use client';

import { useEffect, useRef } from 'react';

interface AudioVisualizerProps {
  isActive: boolean;
  mode: 'listening' | 'speaking' | 'processing' | 'idle';
}

export default function AudioVisualizer({ isActive, mode }: AudioVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();
  const capsulesRef = useRef<Capsule[]>([]);

  class Capsule {
    x: number;
    baseY: number;
    width: number;
    baseHeight: number;
    currentHeight: number;
    targetHeight: number;
    color: string;
    speed: number;
    phase: number;

    constructor(x: number, y: number, width: number, baseHeight: number, color: string, index: number) {
      this.x = x;
      this.baseY = y;
      this.width = width;
      this.baseHeight = baseHeight;
      this.currentHeight = baseHeight;
      this.targetHeight = baseHeight;
      this.color = color;
      this.speed = 0.15;
      this.phase = index * 0.5; // Stagger animation
    }

    update(isActive: boolean, time: number) {
      if (isActive) {
        // Dynamic height based on sine wave with phase offset
        const wave = Math.sin(time * 0.003 + this.phase);
        const intensity = 0.6 + Math.abs(wave) * 0.8; // 0.6 to 1.4 multiplier
        this.targetHeight = this.baseHeight * intensity;
      } else {
        // Return to base height when idle
        this.targetHeight = this.baseHeight * 0.4;
      }

      // Smooth transition to target height
      this.currentHeight += (this.targetHeight - this.currentHeight) * this.speed;
    }

    draw(ctx: CanvasRenderingContext2D) {
      const radius = this.width / 2;
      const x = this.x;
      const y = this.baseY - this.currentHeight / 2;
      const height = this.currentHeight;

      ctx.save();
      ctx.fillStyle = this.color;

      // Draw rounded capsule (pill shape)
      ctx.beginPath();
      
      // Top semicircle
      ctx.arc(x, y, radius, Math.PI, 0, false);
      
      // Right side
      ctx.lineTo(x + radius, y + height);
      
      // Bottom semicircle
      ctx.arc(x, y + height, radius, 0, Math.PI, false);
      
      // Left side
      ctx.lineTo(x - radius, y);
      
      ctx.closePath();
      ctx.fill();

      ctx.restore();
    }
  }

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    const updateSize = () => {
      const dpr = window.devicePixelRatio || 1;
      canvas.width = 400 * dpr;
      canvas.height = 200 * dpr;
      canvas.style.width = '400px';
      canvas.style.height = '200px';
      ctx.scale(dpr, dpr);
    };
    updateSize();

    // Create 4 capsules
    const createCapsules = () => {
      const centerY = 100;
      const spacing = 80;
      const startX = 80;
      const baseHeights = [60, 80, 80, 60]; // Middle capsules taller
      const widths = [30, 35, 35, 30]; // Middle slightly wider

      capsulesRef.current = baseHeights.map((height, i) => {
        return new Capsule(
          startX + i * spacing,
          centerY,
          widths[i],
          height,
          '#ffffff',
          i
        );
      });
    };

    if (capsulesRef.current.length === 0) {
      createCapsules();
    }

    // Animation loop
    const animate = () => {
      const time = Date.now();
      
      // Clear with fade effect for smooth trails
      ctx.fillStyle = 'rgba(10, 10, 10, 0.3)';
      ctx.fillRect(0, 0, 400, 200);

      // Update and draw capsules
      capsulesRef.current.forEach(capsule => {
        capsule.update(isActive, time);
        capsule.draw(ctx);
      });

      // Add subtle glow when active
      if (isActive) {
        ctx.save();
        ctx.globalCompositeOperation = 'lighter';
        ctx.shadowBlur = 30;
        ctx.shadowColor = 
          mode === 'listening' ? 'rgba(59, 130, 246, 0.5)' :
          mode === 'speaking' ? 'rgba(34, 197, 94, 0.5)' :
          'rgba(234, 179, 8, 0.5)';
        
        capsulesRef.current.forEach(capsule => {
          capsule.draw(ctx);
        });
        
        ctx.restore();
      }

      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isActive, mode]);

  return (
    <div className="flex items-center justify-center">
      <canvas
        ref={canvasRef}
        className="opacity-90"
        style={{ width: '400px', height: '200px' }}
      />
    </div>
  );
}