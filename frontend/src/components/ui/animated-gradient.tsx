"use client"

import { memo } from "react"

export const AnimatedGradientBackground = memo(function AnimatedGradientBackground() {
  return (
    <div className="absolute inset-0 -z-10 overflow-hidden">
      <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none" viewBox="0 0 1200 800">
        <defs>
          <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#4f46e5" stopOpacity="0.25">
              <animate attributeName="offset" values="0;1;0" dur="14s" repeatCount="indefinite" />
            </stop>
            <stop offset="100%" stopColor="#06b6d4" stopOpacity="0.25">
              <animate attributeName="offset" values="1;0;1" dur="14s" repeatCount="indefinite" />
            </stop>
          </linearGradient>
          <linearGradient id="grad2" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#a855f7" stopOpacity="0.2">
              <animate attributeName="offset" values="0;1;0" dur="18s" repeatCount="indefinite" />
            </stop>
            <stop offset="100%" stopColor="#22d3ee" stopOpacity="0.2">
              <animate attributeName="offset" values="1;0;1" dur="18s" repeatCount="indefinite" />
            </stop>
          </linearGradient>
        </defs>
        <g opacity="0.8">
          <path d="M0,200 C300,100 900,300 1200,200 L1200,0 L0,0 Z" fill="url(#grad1)">
            <animateTransform attributeName="transform" type="translate" values="0 0; 0 30; 0 0" dur="16s" repeatCount="indefinite" />
          </path>
          <path d="M0,400 C300,300 900,500 1200,400 L1200,0 L0,0 Z" fill="url(#grad2)">
            <animateTransform attributeName="transform" type="translate" values="0 0; 0 -30; 0 0" dur="20s" repeatCount="indefinite" />
          </path>
        </g>
      </svg>
    </div>
  )
})


