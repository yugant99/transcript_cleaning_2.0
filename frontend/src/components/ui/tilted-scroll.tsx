"use client"

import React from 'react'
import { cn } from '@/lib/utils'

interface TiltedScrollCardProps {
  title: string
  content: string
  confidence?: number
  speaker?: string
  className?: string
  sentiment: 'positive' | 'negative' | 'neutral'
}

const TiltedScrollCard: React.FC<TiltedScrollCardProps> = ({
  title,
  content,
  confidence,
  speaker,
  className,
  sentiment
}) => {
  const getSentimentColors = (sentiment: string) => {
    switch (sentiment) {
      case 'positive':
        return 'bg-green-50 border-green-200 hover:bg-green-100'
      case 'negative':
        return 'bg-red-50 border-red-200 hover:bg-red-100'
      case 'neutral':
        return 'bg-blue-50 border-blue-200 hover:bg-blue-100'
      default:
        return 'bg-gray-50 border-gray-200 hover:bg-gray-100'
    }
  }

  return (
    <div
      className={cn(
        "relative p-6 rounded-lg border-2 transition-all duration-300 hover:shadow-lg hover:-translate-y-1",
        getSentimentColors(sentiment),
        className
      )}
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-lg capitalize">{title}</h3>
        {confidence && (
          <span className="text-sm bg-white/70 px-2 py-1 rounded-full">
            {Math.round(confidence * 100)}%
          </span>
        )}
      </div>
      
      <p className="text-gray-700 mb-3 leading-relaxed">{content}</p>
      
      {speaker && (
        <div className="text-sm text-gray-500 border-t pt-2">
          Speaker: {speaker}
        </div>
      )}
    </div>
  )
}

interface TiltedScrollProps {
  cards: Array<{
    id: string
    title: string
    content: string
    confidence?: number
    speaker?: string
    sentiment: 'positive' | 'negative' | 'neutral'
  }>
  className?: string
}

const TiltedScroll: React.FC<TiltedScrollProps> = ({ cards, className }) => {
  return (
    <div className={cn("relative overflow-hidden", className)}>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 p-4">
        {cards.map((card, index) => (
          <div
            key={card.id}
            className={cn(
              "transform transition-all duration-500 hover:scale-105",
              index % 2 === 0 ? "rotate-1" : "-rotate-1",
              "hover:rotate-0"
            )}
          >
            <TiltedScrollCard
              title={card.title}
              content={card.content}
              confidence={card.confidence}
              speaker={card.speaker}
              sentiment={card.sentiment}
            />
          </div>
        ))}
      </div>
    </div>
  )
}

export { TiltedScroll, TiltedScrollCard }
