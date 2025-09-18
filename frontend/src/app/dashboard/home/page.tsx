"use client"

import Link from "next/link"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { AnimatedGradientBackground } from "@/components/ui/animated-gradient"

type PageInfo = {
  title: string
  route: string
  description: string
  calculations?: Record<string, string>
  data_sources?: Record<string, string>
  metrics?: string[]
}

const PAGES: PageInfo[] = [
  {
    title: "Summary",
    route: "/dashboard",
    description: "Patient-by-patient breakdown showing all key conversation metrics in expandable sections.",
    calculations: {
      "Patient Grouping": "Organizes all metrics by participant ID",
      "Turn Counting": "From transcript_insight.py: participant_id_c: and participant_id_p: patterns",
      "Word Counting": "From word_count_updater.py: excludes disfluencies and [bracketed content]",
      "Question/Disfluency Counting": "From enhanced_transcript_analysis.json turn-level data",
    },
    data_sources: {
      "transcript_insights_updated.json": "Cleaned word counts and turn data",
      "enhanced_transcript_analysis.json": "Turn-level question and disfluency counts",
      "classified_output_1.json": "Session and condition metadata",
    },
    metrics: [
      "Per-patient session statistics",
      "Week-by-week progression",
      "Condition and session type breakdowns",
    ],
  },
  {
    title: "Questions & Answers",
    route: "/dashboard/questions",
    description: "Comprehensive analysis of question-asking patterns and conversational engagement.",
    calculations: {
      "Question Rates": "(questions / words) × 100 for each speaker",
      "Question Balance": "0.1–0.9 score for evenness of questioning (0.5 balanced)",
      "Engagement Index": "Composite participation measure",
      "Question Detection": "Turn-level is_question flags from enhanced_transcript_analysis.json",
    },
    data_sources: {
      "enhanced_transcript_analysis.json": "Turn-level question identification",
      "transcript_insights_updated.json": "Word counts for rate calculations",
      "classified_output_1.json": "Session metadata and filters",
    },
    metrics: [
      "Question rates per 100 words",
      "Question balance ratios",
      "Engagement indices",
    ],
  },
  {
    title: "Sentiment Analysis",
    route: "/dashboard/sentiment",
    description: "Sentiment analysis across conversations with examples and trends.",
    calculations: {
      "Sentiment Counts": "Aggregates sentiment classifications by week/session",
      "Temporal Trends": "Line charts showing sentiment progression",
    },
    data_sources: {
      "enhanced_transcript_analysis.json": "Turn-level sentiment (from pipeline)",
      "classified_output_1.json": "Session type and week metadata",
    },
    metrics: [
      "Sentiment distribution",
      "Weekly trends",
      "Participant bars",
    ],
  },
  {
    title: "Lexical Diversity",
    route: "/dashboard/lexical",
    description: "Language analysis measuring interactivity and speech complexity.",
    calculations: {
      "Question Word Ratio": "total_questions / total_words",
      "Speech Density": "words / turns per speaker",
      "Caregiver Density": "caregiver_words / caregiver_turns",
      "PLWD Density": "plwd_words / plwd_turns",
    },
    data_sources: {
      "transcript_insights_updated.json": "Cleaned word & turn counts",
      "enhanced_transcript_analysis.json": "is_question flags",
      "classified_output_1.json": "Session & condition metadata",
    },
    metrics: [
      "Speech density by speaker",
      "Question-to-word ratios",
      "Condition comparisons",
    ],
  },
  {
    title: "Nonverbal Communication",
    route: "/dashboard/nonverbal",
    description: "Normalized non-verbal cues (laughter, sighs, pauses).",
    calculations: {
      "Nonverbal Rate": "(total_nonverbal / total_words) × 100",
      "Cue Normalization": "fix_nonverbal_cues.py standardizes variations",
    },
    data_sources: {
      "enhanced_transcript_analysis_fixed.json": "Normalized nonverbal cues",
      "transcript_insights_updated.json": "Word counts for rates",
      "classified_output_1.json": "Session & week metadata",
    },
    metrics: [
      "Cue counts by type",
      "Rates per speaker",
      "Weekly progression",
    ],
  },
  {
    title: "Disfluency Analysis",
    route: "/dashboard/disfluency",
    description: "Disfluencies and filled pauses using pattern matching.",
    calculations: {
      "Disfluency Rate": "(disfluency_count / total_words) × 100",
      "Detection": "Regex for 'um', 'uh', 'er', 'ah', 'hmm', etc.",
    },
    data_sources: {
      "enhanced_transcript_analysis.json": "Turn-level disfluency detection",
      "transcript_insights_updated.json": "Cleaned word counts (denominator)",
      "classified_output_1.json": "Session & participant metadata",
    },
    metrics: [
      "Disfluency rates",
      "Type breakdowns",
      "Weekly progression",
    ],
  },
  {
    title: "Word Repeat Analysis",
    route: "/dashboard/word-repeats",
    description: "Immediate word repetitions (back-to-back identical words).",
    calculations: {
      "Repeat Rate": "(word_repeats / total_words) × 100",
      "Filtering": "Excludes common disfluencies",
    },
    data_sources: {
      "word_repeats.json": "Immediate repeat counts & contexts",
      "classified_output_1.json": "Session metadata",
    },
    metrics: [
      "Repeat counts & rates",
      "Top repeated words",
      "Examples in context",
    ],
  },
  {
    title: "Turn Taking Ratio",
    route: "/dashboard/turn-taking",
    description: "Conversation balance and overlapping speech instances.",
    calculations: {
      "Overlapping Speech": "Counts '/' occurrences per file",
      "Dominance Ratio": "caregiver_turns / (plwd_turns + 1e-9)",
      "Turn Difference": "caregiver_turns - plwd_turns",
    },
    data_sources: {
      "enhanced_transcript_analysis_fixed.json": "Turn text for '/' counting",
      "transcript_insights_updated.json": "Turn & word counts",
    },
    metrics: [
      "Turn counts",
      "Overlap totals",
      "Dominance ratios",
    ],
  },
  {
    title: "Total View",
    route: "/dashboard/total-view",
    description: "Comprehensive aggregation across key metrics.",
    calculations: {
      "Turn Counting": "participant_id_c:/participant_id_p: patterns",
      "Word Counting": "Excludes disfluencies and [bracketed]",
      "Question/Disfluency": "Turn-level enhanced analysis",
    },
    data_sources: {
      "transcript_insights_updated.json": "Cleaned word counts & turns",
      "enhanced_transcript_analysis.json": "Questions & disfluencies",
      "classified_output_1.json": "Session & condition metadata",
    },
    metrics: [
      "File-level details",
      "Week/Condition/Session summaries",
    ],
  },
]

export default function ExplanationsHome() {
  return (
    <div className="relative min-h-screen">
      <AnimatedGradientBackground />
      <div className="relative z-10 p-6 max-w-6xl mx-auto">
        <div className="mb-8 text-center">
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight">Analysis Guide</h1>
          <p className="text-muted-foreground mt-2">Overview of each dashboard page, its calculations, data sources, and metrics.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {PAGES.map((p) => (
            <Card key={p.title} className="backdrop-blur bg-white/70 dark:bg-neutral-900/60 border-white/40 dark:border-neutral-800/60">
              <CardHeader>
                <CardTitle>{p.title}</CardTitle>
                <CardDescription>{p.description}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {p.calculations && (
                  <div>
                    <div className="text-sm font-semibold mb-1">Key Calculations</div>
                    <ul className="text-sm list-disc pl-5 space-y-1">
                      {Object.entries(p.calculations).map(([k, v]) => (
                        <li key={k}><span className="font-medium">{k}:</span> {v}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {p.data_sources && (
                  <div>
                    <div className="text-sm font-semibold mb-1">Data Sources</div>
                    <ul className="text-sm list-disc pl-5 space-y-1">
                      {Object.entries(p.data_sources).map(([k, v]) => (
                        <li key={k}><span className="font-medium">{k}:</span> {v}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {p.metrics && (
                  <div>
                    <div className="text-sm font-semibold mb-1">Metrics Displayed</div>
                    <ul className="text-sm list-disc pl-5 space-y-1">
                      {p.metrics.map((m) => (
                        <li key={m}>{m}</li>
                      ))}
                    </ul>
                  </div>
                )}
                <div className="pt-2">
                  <Button asChild size="sm">
                    <Link href={p.route}>Open {p.title}</Link>
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}


