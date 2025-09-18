"use client"

import { useEffect, useMemo, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartConfig, ChartContainer, ChartTooltipContent } from "@/components/ui/chart"
import { CartesianGrid, Line, LineChart, XAxis, YAxis, Legend, Tooltip, BarChart, Bar, LabelList, RadialBarChart, RadialBar, PolarGrid } from "recharts"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

type NonverbalRecord = {
  patient_id: string
  week_label: string
  session_type: string
  condition: string
  filename: string
  caregiver_nonverbal: number
  plwd_nonverbal: number
  total_nonverbal: number
  total_words: number
  nonverbal_rate: number
  cue_counts: Record<string, number>
}

type NonverbalExample = {
  cue_type: string
  text: string
  speaker: string
  filename: string
  patient_id: string
  week_label: string
  session_type: string
  condition: string
}

export default function NonVerbalPage() {
  const [rows, setRows] = useState<NonverbalRecord[]>([])
  const [examples, setExamples] = useState<Record<string, NonverbalExample[]>>({})
  const [loading, setLoading] = useState(true)

  const [selectedParticipants, setSelectedParticipants] = useState<string[]>([])
  const [selectedSessions, setSelectedSessions] = useState<string[]>([])
  const [selectedConditions, setSelectedConditions] = useState<string[]>([])

  useEffect(() => {
    const load = async () => {
      try {
        const [s1, s2] = await Promise.all([
          fetch("http://localhost:8000/api/nonverbal"),
          fetch("http://localhost:8000/api/nonverbal-examples"),
        ])
        if (!s1.ok || !s2.ok) throw new Error("Failed to load nonverbal data")
        const d1: NonverbalRecord[] = await s1.json()
        const d2: Record<string, NonverbalExample[]> = await s2.json()
        setRows(Array.isArray(d1) ? d1 : [])
        setExamples(d2 || {})
      } catch (e) {
        console.error(e)
        setRows([])
        setExamples({})
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
      cur.caregiver += r.caregiver_nonverbal
      cur.plwd += r.plwd_nonverbal
      cur.total += r.total_nonverbal
      cur.words += r.total_words
      m.set(r.week_label, cur)
    })
    return Array.from(m.values()).map(v => ({
      week: v.week,
      caregiver: v.caregiver,
      plwd: v.plwd,
      total: v.total,
      rate: v.words > 0 ? +(v.total / v.words * 100).toFixed(2) : 0,
    })).sort((a, b) => {
      if (a.week === 'Baseline') return -1
      if (b.week === 'Baseline') return 1
      if (a.week === 'Final') return 1
      if (b.week === 'Final') return -1
      return a.week.localeCompare(b.week)
    })
  }, [filtered])

  const topCues = useMemo(() => {
    const counts: Record<string, number> = {}
    filtered.forEach(r => {
      Object.entries(r.cue_counts || {}).forEach(([k, v]) => {
        counts[k] = (counts[k] || 0) + (v || 0)
      })
    })
    return Object.entries(counts).map(([cue, count]) => ({ cue, count }))
      .sort((a, b) => b.count - a.count).slice(0, 10)
  }, [filtered])

  const donutData = useMemo(() => topCues.map(c => ({ cue: c.cue, value: c.count })), [topCues])

  if (loading) return <div className="p-6">Loading nonverbal analysis...</div>

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Non Verbal Analysis</h1>
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
            <CardTitle>Nonverbal Trends Over Time</CardTitle>
            <CardDescription>Counts and overall rate by week</CardDescription>
          </CardHeader>
          <CardContent>
            <ChartContainer config={{ caregiver: { label: "Caregiver"}, plwd: { label: "PLWD" }, total: { label: "Total" }, rate: { label: "Rate (%)" } } as ChartConfig}>
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
            <CardTitle>Top Nonverbal Cues</CardTitle>
            <CardDescription>Distribution of most frequent cues</CardDescription>
          </CardHeader>
          <CardContent className="flex-1 pb-0">
            <ChartContainer config={{ value: { label: "Count" } } as ChartConfig} className="mx-auto aspect-square max-h-[260px]">
              <RadialBarChart data={donutData} innerRadius={30} outerRadius={100}>
                <Tooltip cursor={false} content={<ChartTooltipContent />} />
                <PolarGrid gridType="circle" />
                <RadialBar dataKey="value" nameKey="cue" />
                <Legend />
              </RadialBarChart>
            </ChartContainer>
          </CardContent>
        </Card>
      </div>

      {/* Row 2: Participant Bars + Weekly Rate Bars */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Nonverbal by Participant</CardTitle>
            <CardDescription>Caregiver vs PLWD counts</CardDescription>
          </CardHeader>
          <CardContent>
            <ChartContainer config={{ caregiver: { label: "Caregiver" }, plwd: { label: "PLWD" } } as ChartConfig}>
              <BarChart data={[...new Map(filtered.map(r=>[r.patient_id, { participant: r.patient_id, caregiver: 0, plwd: 0 }])).values()].map(v=>{
                filtered.filter(x=>x.patient_id===v.participant).forEach(x=>{ v.caregiver+=x.caregiver_nonverbal; v.plwd+=x.plwd_nonverbal })
                return v
              })}>
                <CartesianGrid vertical={false} />
                <XAxis dataKey="participant" tickLine={false} axisLine={false} />
                <YAxis tickLine={false} axisLine={false} />
                <Tooltip cursor={false} content={<ChartTooltipContent />} />
                <Legend />
                <Bar dataKey="caregiver" name="Caregiver" fill="var(--chart-1)">
                  <LabelList position="top" dataKey="caregiver" />
                </Bar>
                <Bar dataKey="plwd" name="PLWD" fill="var(--chart-2)">
                  <LabelList position="top" dataKey="plwd" />
                </Bar>
              </BarChart>
            </ChartContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Weekly Nonverbal Rate</CardTitle>
            <CardDescription>Total nonverbal cues per 100 words</CardDescription>
          </CardHeader>
          <CardContent>
            <ChartContainer config={{ rate: { label: "Rate (%)" } } as ChartConfig}>
              <BarChart data={byWeek}>
                <CartesianGrid vertical={false} />
                <XAxis dataKey="week" tickLine={false} axisLine={false} />
                <YAxis tickLine={false} axisLine={false} />
                <Tooltip cursor={false} content={<ChartTooltipContent />} />
                <Legend />
                <Bar dataKey="rate" name="Rate (%)" fill="var(--chart-3)">
                  <LabelList position="top" dataKey="rate" />
                </Bar>
              </BarChart>
            </ChartContainer>
          </CardContent>
        </Card>
      </div>

      {/* File-wise Detailed Table */}
      <Card>
        <CardHeader>
          <CardTitle>Detailed Nonverbal by File</CardTitle>
          <CardDescription>Normalized cues and rates</CardDescription>
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
                  <TableHead>Caregiver NV</TableHead>
                  <TableHead>PLWD NV</TableHead>
                  <TableHead>Total NV</TableHead>
                  <TableHead>Total Words</TableHead>
                  <TableHead>NV Rate (%)</TableHead>
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
                    <TableCell className="text-blue-700">{row.caregiver_nonverbal}</TableCell>
                    <TableCell className="text-green-700">{row.plwd_nonverbal}</TableCell>
                    <TableCell className="font-medium">{row.total_nonverbal}</TableCell>
                    <TableCell>{row.total_words.toLocaleString()}</TableCell>
                    <TableCell className="text-amber-700">{row.nonverbal_rate.toFixed(2)}</TableCell>
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
          <CardDescription>Sample excerpts grouped by cue type</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {Object.entries(examples).map(([cue, list]) => (
              <div key={cue} className="rounded-md border p-3">
                <div className="text-sm font-semibold mb-2">{cue}</div>
                <ul className="space-y-2">
                  {list.slice(0, 10).map((ex, i) => (
                    <li key={i} className="text-sm">
                      <span className="text-muted-foreground mr-2">[{ex.speaker}]</span>
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
    </div>
  )
}


