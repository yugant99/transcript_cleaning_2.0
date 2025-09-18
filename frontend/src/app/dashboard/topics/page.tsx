"use client"

import { useEffect, useMemo, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartConfig, ChartContainer, ChartTooltipContent } from "@/components/ui/chart"
import { CartesianGrid, BarChart, Bar, LabelList, Legend, Tooltip, XAxis, YAxis, LineChart, Line, RadialBarChart, RadialBar, PolarGrid } from "recharts"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

type Topic = { id: number; label: string; top_terms: string[]; size: number }
type TopicRow = {
  patient_id: string
  week_label: string
  session_type: string
  condition: string
  filename: string
  top_topics: number[]
  topic_share: Record<string, number>
  total_chunks: number
  switch_count: number
}

type ExamplesPayload = {
  by_topic: Record<string, { text: string; filename: string; patient_id: string; week_label: string; session_type: string; condition: string }[]>
  switches: Record<string, { snippet: string; filename: string; patient_id: string; week_label: string; session_type: string; condition: string }[]>
}

export default function TopicsPage() {
  const [topics, setTopics] = useState<Topic[]>([])
  const [rows, setRows] = useState<TopicRow[]>([])
  const [examples, setExamples] = useState<ExamplesPayload>({ by_topic: {}, switches: {} })
  const [loading, setLoading] = useState(true)

  const [selectedParticipants, setSelectedParticipants] = useState<string[]>([])
  const [selectedSessions, setSelectedSessions] = useState<string[]>([])
  const [selectedConditions, setSelectedConditions] = useState<string[]>([])

  useEffect(() => {
    const load = async () => {
      try {
        const [s1, s2] = await Promise.all([
          fetch("http://localhost:8000/api/topics-summary"),
          fetch("http://localhost:8000/api/topics-examples"),
        ])
        if (!s1.ok || !s2.ok) throw new Error("Failed to load topics")
        const d1 = await s1.json()
        const d2 = await s2.json()
        setTopics(d1.topics || [])
        setRows(d1.rows || [])
        setExamples(d2 || { by_topic: {}, switches: {} })
      } catch (e) {
        console.error(e)
        setTopics([])
        setRows([])
        setExamples({ by_topic: {}, switches: {} })
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const topicLabel = useMemo(() => Object.fromEntries(topics.map(t => [String(t.id), t.label])), [topics])

  const uniqueParticipants = useMemo(() => [...new Set(rows.map(r => r.patient_id))].sort(), [rows])
  const uniqueSessions = useMemo(() => [...new Set(rows.map(r => r.session_type))].sort(), [rows])
  const uniqueConditions = useMemo(() => [...new Set(rows.map(r => r.condition))].sort(), [rows])

  const filtered = useMemo(() => rows.filter(r =>
    (selectedParticipants.length === 0 || selectedParticipants.includes(r.patient_id)) &&
    (selectedSessions.length === 0 || selectedSessions.includes(r.session_type)) &&
    (selectedConditions.length === 0 || selectedConditions.includes(r.condition))
  ), [rows, selectedParticipants, selectedSessions, selectedConditions])

  const topTopicIds = useMemo(() => topics
    .sort((a,b)=>b.size-a.size)
    .slice(0,5)
    .map(t=>String(t.id)), [topics])

  const stackedByWeek = useMemo(() => {
    const m = new Map<string, any>()
    filtered.forEach(r => {
      const wk = r.week_label
      const cur = m.get(wk) || { week: wk }
      topTopicIds.forEach(id => {
        const share = r.topic_share?.[id] || 0
        cur[id] = (cur[id] || 0) + share
      })
      m.set(wk, cur)
    })
    const arr = Array.from(m.values()) as any[]
    return arr.sort((a: any, b: any) => {
      if (a.week === 'Baseline') return -1
      if (b.week === 'Baseline') return 1
      if (a.week === 'Final') return 1
      if (b.week === 'Final') return -1
      return a.week.localeCompare(b.week)
    })
  }, [filtered, topTopicIds])

  const donutData = useMemo(() => {
    const count: Record<string, number> = {}
    filtered.forEach(r => {
      Object.entries(r.topic_share || {}).forEach(([id, pct]) => {
        count[id] = (count[id] || 0) + pct
      })
    })
    return Object.entries(count)
      .map(([id, value]) => ({ topic: topicLabel[id] || id, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 10)
  }, [filtered, topicLabel])

  const switchesByWeek = useMemo(() => {
    const m = new Map<string, { week: string; switches: number }>()
    filtered.forEach(r => {
      const c = m.get(r.week_label) || { week: r.week_label, switches: 0 }
      c.switches += r.switch_count
      m.set(r.week_label, c)
    })
    return Array.from(m.values()).sort((a,b)=>a.week.localeCompare(b.week))
  }, [filtered])

  const topTransitions = useMemo(() => {
    // Approximate: not stored per-row; we can reconstruct from examples.switches counts
    const map: Record<string, number> = {}
    Object.entries(examples.switches || {}).forEach(([k, list]) => {
      map[k] = (map[k] || 0) + (list?.length || 0)
    })
    return Object.entries(map).map(([key, count]) => ({ key, count }))
      .sort((a,b)=>b.count-a.count).slice(0,10)
  }, [examples])

  if (loading) return <div className="p-6">Loading topics...</div>

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Topic Explorer</h1>
      </div>

      {/* Filters */}
      <div className="flex gap-4 mb-6">
        <select multiple value={selectedParticipants} onChange={(e)=>setSelectedParticipants(Array.from(e.target.selectedOptions, o=>o.value))} className="px-3 py-2 border rounded-md min-w-48 h-32">
          {uniqueParticipants.map(p=> <option key={p} value={p}>{p}</option>)}
        </select>
        <select multiple value={selectedSessions} onChange={(e)=>setSelectedSessions(Array.from(e.target.selectedOptions, o=>o.value))} className="px-3 py-2 border rounded-md min-w-48 h-32">
          {uniqueSessions.map(s=> <option key={s} value={s}>{s}</option>)}
        </select>
        <select multiple value={selectedConditions} onChange={(e)=>setSelectedConditions(Array.from(e.target.selectedOptions, o=>o.value))} className="px-3 py-2 border rounded-md min-w-48 h-32">
          {uniqueConditions.map(c=> <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      {/* Row 1: Stacked topic shares + Donut */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Topic Share by Week (Top 5)</CardTitle>
            <CardDescription>Stacked shares across weeks</CardDescription>
          </CardHeader>
          <CardContent>
            <ChartContainer config={{} as ChartConfig}>
              <BarChart data={stackedByWeek}>
                <CartesianGrid vertical={false} />
                <XAxis dataKey="week" tickLine={false} axisLine={false} />
                <YAxis tickLine={false} axisLine={false} />
                <Tooltip cursor={false} content={<ChartTooltipContent />} />
                <Legend />
                {topTopicIds.map((id, idx) => (
                  <Bar key={id} dataKey={id} name={(topicLabel[id] || id)} stackId="a">
                    <LabelList position="top" dataKey={id} />
                  </Bar>
                ))}
              </BarChart>
            </ChartContainer>
          </CardContent>
        </Card>

        <Card className="flex flex-col">
          <CardHeader className="items-center pb-0">
            <CardTitle>Top Topics (Overall)</CardTitle>
            <CardDescription>Distribution across filtered files</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 pb-0">
            <ChartContainer config={{ value: { label: "Share" } } as ChartConfig} className="mx-auto aspect-square max-h-[260px]">
              <RadialBarChart data={donutData} innerRadius={30} outerRadius={100}>
                <Tooltip cursor={false} content={<ChartTooltipContent />} />
                <PolarGrid gridType="circle" />
                <RadialBar dataKey="value" nameKey="topic" />
                <Legend />
              </RadialBarChart>
            </ChartContainer>
          </CardContent>
        </Card>
      </div>

      {/* Row 2: Switches line + Top transitions bar */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Topic Switches Over Time</CardTitle>
            <CardDescription>Transitions between topics by week</CardDescription>
          </CardHeader>
          <CardContent>
            <ChartContainer config={{ switches: { label: "Switches" } } as ChartConfig}>
              <LineChart data={switchesByWeek}>
                <CartesianGrid vertical={false} />
                <XAxis dataKey="week" tickLine={false} axisLine={false} />
                <YAxis tickLine={false} axisLine={false} />
                <Tooltip cursor={false} content={<ChartTooltipContent />} />
                <Legend />
                <Line dataKey="switches" name="Switches" stroke="var(--chart-3)" strokeWidth={2} dot={false} />
              </LineChart>
            </ChartContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top Topic Transitions</CardTitle>
            <CardDescription>Most common A→B transitions</CardDescription>
          </CardHeader>
          <CardContent>
            <ChartContainer config={{ count: { label: "Count" } } as ChartConfig}>
              <BarChart data={topTransitions}>
                <CartesianGrid vertical={false} />
                <XAxis dataKey="key" tickLine={false} axisLine={false} />
                <YAxis tickLine={false} axisLine={false} />
                <Tooltip cursor={false} content={<ChartTooltipContent />} />
                <Legend />
                <Bar dataKey="count" name="Count" fill="var(--chart-1)">
                  <LabelList position="top" dataKey="count" />
                </Bar>
              </BarChart>
            </ChartContainer>
          </CardContent>
        </Card>
      </div>

      {/* File-wise Detailed Table */}
      <Card>
        <CardHeader>
          <CardTitle>Detailed Topics by File</CardTitle>
          <CardDescription>Top topics, shares, and switch counts</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-auto max-h-[600px] rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Patient</TableHead>
                  <TableHead>Session</TableHead>
                  <TableHead>Week</TableHead>
                  <TableHead>Condition</TableHead>
                  <TableHead>Filename</TableHead>
                  <TableHead>Top Topics</TableHead>
                  <TableHead>Shares (%)</TableHead>
                  <TableHead>Chunks</TableHead>
                  <TableHead>Switches</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((row, idx) => (
                  <TableRow key={idx} className="hover:bg-muted/30">
                    <TableCell className="font-medium">{row.patient_id.toUpperCase()}</TableCell>
                    <TableCell>{row.session_type}</TableCell>
                    <TableCell>{row.week_label}</TableCell>
                    <TableCell>
                      <span className={`${row.condition === "VR" ? "bg-blue-100 text-blue-800" : "bg-gray-100 text-gray-800"} px-2 py-1 text-xs rounded`}>
                        {row.condition}
                      </span>
                    </TableCell>
                    <TableCell className="text-xs">{row.filename}</TableCell>
                    <TableCell>
                      {(row.top_topics || []).map((id) => (
                        <span key={id} className="mr-2 px-2 py-0.5 text-xs rounded bg-slate-100">{topicLabel[String(id)] || id}</span>
                      ))}
                    </TableCell>
                    <TableCell>
                      {Object.entries(row.topic_share || {}).slice(0,5).map(([id, pct]) => (
                        <span key={id} className="mr-2 text-xs">{(topicLabel[id] || id)}: {pct}%</span>
                      ))}
                    </TableCell>
                    <TableCell className="font-medium">{row.total_chunks}</TableCell>
                    <TableCell>{row.switch_count}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Examples */}
      <Card>
        <CardHeader>
          <CardTitle>Topic Examples</CardTitle>
          <CardDescription>Representative snippets by topic</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(examples.by_topic || {}).map(([tid, list]) => (
              <div key={tid} className="rounded-md border p-3">
                <div className="text-sm font-semibold mb-2">{topicLabel[tid] || tid}</div>
                <ul className="space-y-2">
                  {list.slice(0, 8).map((ex, i) => (
                    <li key={i} className="text-sm">
                      {ex.text}
                      <div className="text-xs text-muted-foreground mt-1">{ex.patient_id} • {ex.session_type} • {ex.week_label} • {ex.condition}</div>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Topic Switch Examples</CardTitle>
          <CardDescription>Snippets around A→B transitions</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(examples.switches || {}).map(([key, list]) => (
              <div key={key} className="rounded-md border p-3">
                <div className="text-sm font-semibold mb-2">{key}</div>
                <ul className="space-y-2">
                  {list.slice(0, 8).map((ex, i) => (
                    <li key={i} className="text-sm">
                      {ex.snippet}
                      <div className="text-xs text-muted-foreground mt-1">{ex.patient_id} • {ex.session_type} • {ex.week_label} • {ex.condition}</div>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}


