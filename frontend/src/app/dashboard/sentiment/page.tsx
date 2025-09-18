"use client"

import { useEffect, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { TrendingUp } from "lucide-react"
import { CartesianGrid, Line, LineChart, XAxis, YAxis, Legend, Tooltip, BarChart, Bar, Cell, LabelList } from "recharts"
import { PolarGrid, RadialBar, RadialBarChart } from "recharts"
import { ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { TiltedScroll } from "@/components/ui/tilted-scroll"

interface SentimentData {
  patient_id: string
  week_label: string
  session_type: string
  condition: string
  filename: string
  positive: number
  negative: number
  neutral: number
  total_chunks: number
  positive_pct: number
  negative_pct: number
  neutral_pct: number
  avg_polarity: number
  avg_confidence: number
  net_sentiment: number
}

interface SentimentExample {
  text: string
  confidence: number
  speaker: string
  filename: string
  patient_id: string
}

export default function SentimentPage() {
  const [data, setData] = useState<SentimentData[]>([])
  const [examples, setExamples] = useState<Record<string, SentimentExample[]>>({})
  const [loading, setLoading] = useState(true)
  const [selectedParticipants, setSelectedParticipants] = useState<string[]>([])
  const [selectedSessions, setSelectedSessions] = useState<string[]>([])
  const [selectedConditions, setSelectedConditions] = useState<string[]>([])

  useEffect(() => {
    const fetchData = async () => {
      try {
        console.log('Fetching sentiment data...')
        const [sentimentResponse, examplesResponse] = await Promise.all([
          fetch('http://localhost:8000/api/sentiment-analysis'),
          fetch('http://localhost:8000/api/sentiment-examples')
        ])
        
        if (!sentimentResponse.ok || !examplesResponse.ok) {
          throw new Error('Failed to fetch data')
        }
        
        const sentimentResult = await sentimentResponse.json()
        const examplesResult = await examplesResponse.json()
        
        console.log('Data received:', sentimentResult?.length || 0, 'records')
        setData(Array.isArray(sentimentResult) ? sentimentResult : [])
        setExamples(examplesResult || {})
      } catch (error) {
        console.error('Error fetching data:', error)
        setData([])
        setExamples({})
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const filteredData = Array.isArray(data) ? data.filter(item =>
    (selectedParticipants.length === 0 || selectedParticipants.includes(item.patient_id)) &&
    (selectedSessions.length === 0 || selectedSessions.includes(item.session_type)) &&
    (selectedConditions.length === 0 || selectedConditions.includes(item.condition))
  ) : []

  // Prepare data for line chart
  const trendData = Array.isArray(filteredData) ? (() => {
    const weekMap = new Map()
    filteredData.forEach(item => {
      const week = item.week_label
      if (!weekMap.has(week)) {
        weekMap.set(week, { week, positive: 0, negative: 0, neutral: 0, count: 0 })
      }
      const weekData = weekMap.get(week)
      weekData.positive += item.positive
      weekData.negative += item.negative
      weekData.neutral += item.neutral
      weekData.count += 1
    })
    return Array.from(weekMap.values()).sort((a, b) => {
      if (a.week === 'Baseline') return -1
      if (b.week === 'Baseline') return 1
      if (a.week === 'Final') return 1
      if (b.week === 'Final') return -1
      return a.week.localeCompare(b.week)
    })
  })() : []

  // Prepare data for radial chart
  const radialData = Array.isArray(filteredData) ? (() => {
    const totals = filteredData.reduce((acc, item) => {
      acc.positive += item.positive
      acc.negative += item.negative
      acc.neutral += item.neutral
      return acc
    }, { positive: 0, negative: 0, neutral: 0 })
    
    return [
      { sentiment: "Positive", count: totals.positive, fill: "var(--chart-1)" },
      { sentiment: "Negative", count: totals.negative, fill: "var(--chart-2)" },
      { sentiment: "Neutral", count: totals.neutral, fill: "var(--chart-3)" }
    ]
  })() : []

  // Get unique filter options
  const uniqueParticipants = Array.isArray(data) ? [...new Set(data.map(item => item.patient_id))].sort() : []
  const uniqueSessions = Array.isArray(data) ? [...new Set(data.map(item => item.session_type))].sort() : []
  const uniqueConditions = Array.isArray(data) ? [...new Set(data.map(item => item.condition))].sort() : []

  // Prepare tilted scroll cards
  const tiltedCards = Object.entries(examples).flatMap(([sentiment, exampleList]) =>
    exampleList.slice(0, 15).map((example, index) => ({
      id: `${sentiment}-${index}`,
      title: `${sentiment} Sentiment`,
      content: example.text,
      confidence: example.confidence,
      speaker: example.speaker,
      sentiment: sentiment as 'positive' | 'negative' | 'neutral'
    }))
  )

  const chartConfig = {
    positive: {
      label: "Positive",
      color: "var(--chart-1)",
    },
    negative: {
      label: "Negative",
      color: "var(--chart-2)",
    },
    neutral: {
      label: "Neutral",
      color: "var(--chart-3)",
    },
    count: {
      label: "Count",
    },
  } satisfies ChartConfig

  // Participant-level aggregates for additional visuals
  const participantBars = Array.isArray(filteredData) ? (() => {
    const map = new Map<string, { participant: string; positive: number; negative: number }>()
    filteredData.forEach(row => {
      const id = row.patient_id
      const current = map.get(id)
      if (current) {
        current.positive += row.positive
        current.negative += row.negative
      } else {
        map.set(id, { participant: id, positive: row.positive, negative: row.negative })
      }
    })
    // Convert negatives to negative values for plotting below axis
    const arr = Array.from(map.values()).map(v => ({
      participant: v.participant,
      positive: v.positive,
      negative: -v.negative,
    }))
    // Sort by total magnitude descending
    arr.sort((a, b) => (b.positive + Math.abs(b.negative)) - (a.positive + Math.abs(a.negative)))
    return arr
  })() : []

  // (Removed: scatterData; scatter visual dropped)

  if (loading) {
    return <div className="p-6">Loading sentiment analysis...</div>
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Sentiment Analysis</h1>
      </div>

      {/* Filters */}
      <div className="flex gap-4 mb-6">
        <select
          multiple
          value={selectedParticipants}
          onChange={(e) => setSelectedParticipants(Array.from(e.target.selectedOptions, o => o.value))}
          className="px-3 py-2 border rounded-md min-w-48 h-32"
        >
          {uniqueParticipants.map(participant => (
            <option key={participant} value={participant}>{participant}</option>
          ))}
        </select>

        <select
          multiple
          value={selectedSessions}
          onChange={(e) => setSelectedSessions(Array.from(e.target.selectedOptions, o => o.value))}
          className="px-3 py-2 border rounded-md min-w-48 h-32"
        >
          {uniqueSessions.map(session => (
            <option key={session} value={session}>{session}</option>
          ))}
        </select>

        <select
          multiple
          value={selectedConditions}
          onChange={(e) => setSelectedConditions(Array.from(e.target.selectedOptions, o => o.value))}
          className="px-3 py-2 border rounded-md min-w-48 h-32"
        >
          {uniqueConditions.map(condition => (
            <option key={condition} value={condition}>{condition}</option>
          ))}
        </select>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Line Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Sentiment Trends Over Time</CardTitle>
            <CardDescription>Sentiment distribution across weeks</CardDescription>
          </CardHeader>
          <CardContent>
            <ChartContainer config={chartConfig}>
              <LineChart
                accessibilityLayer
                data={trendData}
                margin={{
                  left: 12,
                  right: 12,
                }}
              >
                <CartesianGrid vertical={false} />
                <XAxis
                  dataKey="week"
                  tickLine={false}
                  axisLine={false}
                  tickMargin={8}
                  tickFormatter={(value) => value.slice(0, 8)}
                />
                <Tooltip cursor={false} content={<ChartTooltipContent />} />
                <Line
                  dataKey="positive"
                  type="monotone"
                  stroke="var(--color-positive)"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  dataKey="negative"
                  type="monotone"
                  stroke="var(--color-negative)"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  dataKey="neutral"
                  type="monotone"
                  stroke="var(--color-neutral)"
                  strokeWidth={2}
                  dot={false}
                />
                <Legend verticalAlign="top" height={24} />
              </LineChart>
            </ChartContainer>
          </CardContent>
        </Card>

        {/* Radial Chart */}
        <Card className="flex flex-col">
          <CardHeader className="items-center pb-0">
            <CardTitle>Overall Sentiment Distribution</CardTitle>
            <CardDescription>Total sentiment breakdown</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 pb-0">
            <ChartContainer
              config={chartConfig}
              className="mx-auto aspect-square max-h-[250px]"
            >
              <RadialBarChart data={radialData} innerRadius={30} outerRadius={100}>
                <Tooltip cursor={false} content={<ChartTooltipContent />} />
                <PolarGrid gridType="circle" />
                <RadialBar dataKey="count" />
              </RadialBarChart>
            </ChartContainer>
          </CardContent>
          <CardContent className="flex-col gap-2 text-sm">
            <div className="flex items-center gap-2 leading-none font-medium">
              Sentiment analysis across all conversations <TrendingUp className="h-4 w-4" />
            </div>
            <div className="text-muted-foreground leading-none">
              Based on {filteredData.length} conversation files
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Additional Charts */}
      <div className="grid grid-cols-1 gap-6">
        {/* Participant Net Sentiment Bar (Negative/Positive) - full width */}
        <Card>
          <CardHeader>
            <CardTitle>Net Sentiment by Participant</CardTitle>
            <CardDescription>Total positive minus negative counts</CardDescription>
          </CardHeader>
          <CardContent>
            <ChartContainer config={{
              positive: { label: "Positive" },
              negative: { label: "Negative" },
            } as ChartConfig}>
              <BarChart accessibilityLayer data={participantBars}>
                <CartesianGrid vertical={false} />
                <XAxis dataKey="participant" tickLine={false} axisLine={false} />
                <YAxis tickLine={false} axisLine={false} />
                <Tooltip cursor={false} content={<ChartTooltipContent hideIndicator />} />
                <Bar name="Positive" dataKey="positive" fill="var(--color-positive)">
                  <LabelList position="top" dataKey="positive" />
                </Bar>
                <Bar name="Negative" dataKey="negative" fill="var(--color-negative)">
                  <LabelList position="bottom" dataKey="negative" />
                </Bar>
              </BarChart>
            </ChartContainer>
          </CardContent>
        </Card>
      </div>

      {/* Detailed Table */}
      <Card>
        <CardHeader>
          <CardTitle>Detailed Sentiment Analysis</CardTitle>
          <CardDescription>File-wise sentiment breakdown</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Participant</TableHead>
                <TableHead>Session</TableHead>
                <TableHead>Week</TableHead>
                <TableHead>Condition</TableHead>
                <TableHead>Positive</TableHead>
                <TableHead>Negative</TableHead>
                <TableHead>Neutral</TableHead>
                <TableHead>Net Sentiment</TableHead>
                <TableHead>Avg Polarity</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredData.map((row, index) => (
                <TableRow key={index}>
                  <TableCell>{row.patient_id}</TableCell>
                  <TableCell>{row.session_type}</TableCell>
                  <TableCell>{row.week_label}</TableCell>
                  <TableCell>{row.condition}</TableCell>
                  <TableCell className="text-green-600">{row.positive}</TableCell>
                  <TableCell className="text-red-600">{row.negative}</TableCell>
                  <TableCell className="text-blue-600">{row.neutral}</TableCell>
                  <TableCell className={row.net_sentiment > 0 ? "text-green-600" : row.net_sentiment < 0 ? "text-red-600" : "text-gray-600"}>
                    {row.net_sentiment}
                  </TableCell>
                  <TableCell>{row.avg_polarity}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Tilted Scroll Examples */}
      <Card>
        <CardHeader>
          <CardTitle>Sentiment Examples</CardTitle>
          <CardDescription>Real conversation excerpts showing different sentiment types</CardDescription>
        </CardHeader>
        <CardContent>
          <TiltedScroll cards={tiltedCards} />
        </CardContent>
      </Card>
    </div>
  )
}
