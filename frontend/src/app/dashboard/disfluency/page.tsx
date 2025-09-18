"use client"

import { useEffect, useMemo, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartConfig, ChartContainer, ChartTooltipContent } from "@/components/ui/chart"
import { CartesianGrid, Line, LineChart, XAxis, YAxis, Legend, Tooltip, BarChart, Bar, LabelList, RadialBarChart, RadialBar, PolarGrid } from "recharts"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

type DisfluencyRecord = {
  patient_id: string
  week_label: string
  session_type: string
  condition: string
  filename: string
  caregiver_disfluencies: number
  plwd_disfluencies: number
  total_disfluencies: number
  total_words: number
  disfluency_rate: number
}

type DisfluencyExample = {
  disfluency_type: string
  text: string
  speaker: string
  filename: string
  patient_id: string
  week_label: string
  session_type: string
  condition: string
}

export default function DisfluencyPage() {
  const [rows, setRows] = useState<DisfluencyRecord[]>([])
  const [examples, setExamples] = useState<DisfluencyExample[]>([])
  const [loading, setLoading] = useState(true)

  const [selectedParticipants, setSelectedParticipants] = useState<string[]>([])
  const [selectedSessions, setSelectedSessions] = useState<string[]>([])
  const [selectedConditions, setSelectedConditions] = useState<string[]>([])

  useEffect(() => {
    const load = async () => {
      try {
        const [s1, s2] = await Promise.all([
          fetch("http://localhost:8000/api/disfluency"),
          fetch("http://localhost:8000/api/disfluency-examples"),
        ])
        if (!s1.ok || !s2.ok) throw new Error("Failed to load disfluency data")
        const d1: DisfluencyRecord[] = await s1.json()
        const d2: DisfluencyExample[] = await s2.json()
        setRows(Array.isArray(d1) ? d1 : [])
        setExamples(Array.isArray(d2) ? d2 : [])
      } catch (e) {
        console.error(e)
        setRows([])
        setExamples([])
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const uniqueParticipants = useMemo(() => [...new Set(rows.map(r => r.patient_id))].sort(), [rows])
  const uniqueSessions = useMemo(() => [...new Set(rows.map(r => r.session_type))].sort(), [rows])
  const uniqueConditions = useMemo(() => [...new Set(rows.map(r => r.condition))].sort(), [rows])

  const filtered = useMemo(() => rows.filter(r =>
    (selectedParticipants.length === 0 || selectedParticipants.includes(r.patient_id)) &&
    (selectedSessions.length === 0 || selectedSessions.includes(r.session_type)) &&
    (selectedConditions.length === 0 || selectedConditions.includes(r.condition))
  ), [rows, selectedParticipants, selectedSessions, selectedConditions])

  const byWeek = useMemo(() => {
    const m = new Map<string, { week: string; caregiver: number; plwd: number; total: number; words: number }>()
    filtered.forEach(r => {
      const cur = m.get(r.week_label) || { week: r.week_label, caregiver: 0, plwd: 0, total: 0, words: 0 }
      cur.caregiver += r.caregiver_disfluencies
      cur.plwd += r.plwd_disfluencies
      cur.total += r.total_disfluencies
      cur.words += r.total_words
      m.set(r.week_label, cur)
    })
    return Array.from(m.values()).map(v => ({
      week: v.week,
      caregiver: v.caregiver,
      plwd: v.plwd,
      rate: v.words > 0 ? +(v.total / v.words * 100).toFixed(2) : 0,
    })).sort((a, b) => {
      if (a.week === 'Baseline') return -1
      if (b.week === 'Baseline') return 1
      if (a.week === 'Final') return 1
      if (b.week === 'Final') return -1
      return a.week.localeCompare(b.week)
    })
  }, [filtered])

  const topTypes = useMemo(() => {
    // Aggregate by disfluency_type from examples
    const counts: Record<string, number> = {}
    examples.forEach(ex => {
      const key = ex.disfluency_type || 'unknown'
      counts[key] = (counts[key] || 0) + 1
    })
    return Object.entries(counts).map(([t, c]) => ({ type: t, count: c }))
      .sort((a, b) => b.count - a.count).slice(0, 10)
  }, [examples])

  const donutData = useMemo(() => topTypes.map(t => ({ type: t.type, value: t.count })), [topTypes])

  if (loading) return <div className="p-6">Loading disfluency...</div>

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Disfluency</h1>
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

      {/* Row 1: Trend + Donut */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Disfluency Trends Over Time</CardTitle>
            <CardDescription>Caregiver vs PLWD and overall rate</CardDescription>
          </CardHeader>
          <CardContent>
            <ChartContainer config={{ caregiver: { label: "Caregiver"}, plwd: { label: "PLWD" }, rate: { label: "Rate (%)" } } as ChartConfig}>
              <LineChart data={byWeek}>
                <CartesianGrid vertical={false} />
                <XAxis dataKey="week" tickLine={false} axisLine={false} />
                <YAxis tickLine={false} axisLine={false} />
                <Tooltip cursor={false} content={<ChartTooltipContent />} />
                <Legend />
                <Line dataKey="caregiver" name="Caregiver" stroke="var(--chart-1)" strokeWidth={2} dot={false} />
                <Line dataKey="plwd" name="PLWD" stroke="var(--chart-2)" strokeWidth={2} dot={false} />
                <Line dataKey="rate" name="Rate (%)" stroke="var(--chart-3)" strokeWidth={2} dot={false} />
              </LineChart>
            </ChartContainer>
          </CardContent>
        </Card>

        <Card className="flex flex-col">
          <CardHeader className="items-center pb-0">
            <CardTitle>Top Disfluency Types</CardTitle>
            <CardDescription>Distribution across examples</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 pb-0">
            <ChartContainer config={{ value: { label: "Count" } } as ChartConfig} className="mx-auto aspect-square max-h-[260px]">
              <RadialBarChart data={donutData} innerRadius={30} outerRadius={100}>
                <Tooltip cursor={false} content={<ChartTooltipContent />} />
                <PolarGrid gridType="circle" />
                <RadialBar dataKey="value" nameKey="type" />
                <Legend />
              </RadialBarChart>
            </ChartContainer>
          </CardContent>
        </Card>
      </div>

      {/* File-wise Detailed Table */}
      <Card>
        <CardHeader>
          <CardTitle>Detailed Disfluency by File</CardTitle>
          <CardDescription>Counts and rates per file</CardDescription>
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
                  <TableHead>Caregiver Disfl.</TableHead>
                  <TableHead>PLWD Disfl.</TableHead>
                  <TableHead>Total Disfl.</TableHead>
                  <TableHead>Total Words</TableHead>
                  <TableHead>Disfl. Rate (%)</TableHead>
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
                    <TableCell className="text-blue-700">{row.caregiver_disfluencies}</TableCell>
                    <TableCell className="text-green-700">{row.plwd_disfluencies}</TableCell>
                    <TableCell className="font-medium">{row.total_disfluencies}</TableCell>
                    <TableCell>{row.total_words.toLocaleString()}</TableCell>
                    <TableCell className="text-amber-700">{row.disfluency_rate.toFixed(2)}</TableCell>
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
          <CardTitle>Examples</CardTitle>
          <CardDescription>Sample excerpts with disfluency annotations</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {examples.slice(0, 40).map((ex, i) => (
              <div key={i} className="rounded-md border p-3">
                <div className="text-sm font-semibold mb-1">{ex.disfluency_type}</div>
                <div className="text-sm">{ex.text}</div>
                <div className="text-xs text-muted-foreground mt-1">[{ex.speaker}] • {ex.patient_id} • {ex.session_type} • {ex.week_label} • {ex.condition}</div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}



