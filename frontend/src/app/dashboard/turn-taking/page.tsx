"use client"

import { useEffect, useMemo, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { ChartConfig, ChartContainer, ChartTooltipContent } from "@/components/ui/chart"
import { CartesianGrid, Line, LineChart, XAxis, YAxis, Legend, Tooltip, ScatterChart, Scatter, ZAxis, ReferenceLine } from "recharts"

type TTRow = {
  patient_id: string
  week_label: string
  session_type: string
  condition: string
  filename: string
  caregiver_turns: number
  plwd_turns: number
  caregiver_words: number
  plwd_words: number
  overlapping_speech: number
  turn_diff: number
  word_diff: number
  dominance_ratio: number
}

export default function TurnTakingPage() {
  const [rows, setRows] = useState<TTRow[]>([])
  const [loading, setLoading] = useState(true)

  const [selectedParticipants, setSelectedParticipants] = useState<string[]>([])
  const [selectedSessions, setSelectedSessions] = useState<string[]>([])
  const [selectedConditions, setSelectedConditions] = useState<string[]>([])
  const [aggLevel, setAggLevel] = useState<"File" | "Week">("Week")
  const [colorBy, setColorBy] = useState<"condition" | "session_type" | "patient_id">("condition")
  const [sizeBy, setSizeBy] = useState<"overlap" | "turn_diff_abs" | "total_words">("overlap")
  const [selectedWeek, setSelectedWeek] = useState<string>("All")
  const [bubbleMax, setBubbleMax] = useState<number>(180)

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/turn-taking")
        if (!res.ok) throw new Error("Failed to load turn taking")
        const data: TTRow[] = await res.json()
        setRows(Array.isArray(data) ? data : [])
      } catch (e) {
        console.error(e)
        setRows([])
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const prefiltered = useMemo(() => rows.filter(r => r.session_type !== "Final Interview"), [rows])

  const uniqueParticipants = useMemo(() => [...new Set(prefiltered.map(r => r.patient_id))].sort(), [prefiltered])
  const uniqueSessions = useMemo(() => [...new Set(prefiltered.map(r => r.session_type))].sort(), [prefiltered])
  const uniqueConditions = useMemo(() => [...new Set(prefiltered.map(r => r.condition))].sort(), [prefiltered])

  const filtered = useMemo(() => prefiltered.filter(r =>
    (selectedParticipants.length === 0 || selectedParticipants.includes(r.patient_id)) &&
    (selectedSessions.length === 0 || selectedSessions.includes(r.session_type)) &&
    (selectedConditions.length === 0 || selectedConditions.includes(r.condition))
  ), [prefiltered, selectedParticipants, selectedSessions, selectedConditions])

  // Weekly summary
  const weekly = useMemo(() => {
    const m = new Map<string, any>()
    filtered.forEach(r => {
      const key = r.week_label
      const cur = m.get(key) || { week: r.week_label, cTurns: 0, pTurns: 0, cWords: 0, pWords: 0, overlap: 0 }
      cur.cTurns += r.caregiver_turns
      cur.pTurns += r.plwd_turns
      cur.cWords += r.caregiver_words
      cur.pWords += r.plwd_words
      cur.overlap += r.overlapping_speech
      m.set(key, cur)
    })
    return Array.from(m.values()).map(v => ({
      ...v,
      dominance_ratio: v.pTurns > 0 ? +(v.cTurns / v.pTurns).toFixed(2) : (v.cTurns > 0 ? Infinity : 1.0)
    })).sort((a, b) => {
      if (a.week === 'Baseline') return -1
      if (b.week === 'Baseline') return 1
      if (a.week === 'Final') return 1
      if (b.week === 'Final') return -1
      return a.week.localeCompare(b.week)
    })
  }, [filtered])

  const weeksList = useMemo(() => ["All", ...new Set(weekly.map(w => w.week))], [weekly])

  // Build scatter data based on controls
  const scatterGroups = useMemo(() => {
    type Pt = { x: number; y: number; size: number }
    const groups = new Map<string, Pt[]>()
    if (aggLevel === "Week") {
      const source = weekly
      source.forEach(w => {
        const key = "Weekly"
        const arr = groups.get(key) || []
        const sizeVal = sizeBy === "overlap" ? Math.max(1, w.overlap)
          : sizeBy === "turn_diff_abs" ? Math.abs(w.cTurns - w.pTurns)
          : (w.cWords + w.pWords)
        arr.push({ x: w.cTurns, y: w.pTurns, size: sizeVal })
        groups.set(key, arr)
      })
      return groups
    }
    // File-level
    const src = selectedWeek === "All" ? filtered : filtered.filter(r => r.week_label === selectedWeek)
    src.forEach(r => {
      const key = String((r as any)[colorBy])
      const arr = groups.get(key) || []
      const totalWords = r.caregiver_words + r.plwd_words
      const sizeVal = sizeBy === "overlap" ? Math.max(1, r.overlapping_speech)
        : sizeBy === "turn_diff_abs" ? Math.abs(r.turn_diff)
        : Math.max(1, totalWords)
      arr.push({ x: r.caregiver_turns, y: r.plwd_turns, size: sizeVal })
      groups.set(key, arr)
    })
    return groups
  }, [aggLevel, colorBy, sizeBy, selectedWeek, filtered, weekly])

  const legendConfig = useMemo(() => {
    const entries = Array.from(scatterGroups.keys()).map((key, i) => ([`series_${i}`, { label: key }]))
    return Object.fromEntries(entries) as ChartConfig
  }, [scatterGroups])

  if (loading) return <div className="p-6">Loading Turn Taking...</div>

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Turn-Taking and Engagement</h1>
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

      {/* Detailed File Table */}
      <Card>
        <CardHeader>
          <CardTitle>Detailed Engagement by File</CardTitle>
          <CardDescription>Overlapping speech is exact count of '/' in transcript text</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-auto max-h-[600px] rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Week</TableHead>
                  <TableHead>Patient</TableHead>
                  <TableHead>Session</TableHead>
                  <TableHead>Condition</TableHead>
                  <TableHead>Filename</TableHead>
                  <TableHead>Caregiver Turns</TableHead>
                  <TableHead>PLWD Turns</TableHead>
                  <TableHead>Caregiver Words</TableHead>
                  <TableHead>PLWD Words</TableHead>
                  <TableHead>Overlapping Speech</TableHead>
                  <TableHead>Turn Diff</TableHead>
                  <TableHead>Word Diff</TableHead>
                  <TableHead>Dominance Ratio</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.sort((a,b)=> a.week_label.localeCompare(b.week_label) || a.patient_id.localeCompare(b.patient_id)).map((row, idx) => (
                  <TableRow key={idx} className="hover:bg-muted/30">
                    <TableCell className="font-medium">{row.week_label}</TableCell>
                    <TableCell>{row.patient_id.toUpperCase()}</TableCell>
                    <TableCell>{row.session_type}</TableCell>
                    <TableCell>
                      <span className={`${row.condition === "VR" ? "bg-blue-100 text-blue-800" : "bg-gray-100 text-gray-800"} px-2 py-1 text-xs rounded`}>
                        {row.condition}
                      </span>
                    </TableCell>
                    <TableCell className="text-xs">{row.filename}</TableCell>
                    <TableCell>{row.caregiver_turns}</TableCell>
                    <TableCell>{row.plwd_turns}</TableCell>
                    <TableCell>{row.caregiver_words}</TableCell>
                    <TableCell>{row.plwd_words}</TableCell>
                    <TableCell className="text-amber-700">{row.overlapping_speech}</TableCell>
                    <TableCell>{row.turn_diff}</TableCell>
                    <TableCell>{row.word_diff}</TableCell>
                    <TableCell>{Number.isFinite(row.dominance_ratio) ? row.dominance_ratio.toFixed(2) : "∞"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Weekly Aggregated Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Weekly Aggregated Engagement</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-auto max-h-[500px] rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Week</TableHead>
                  <TableHead>Caregiver Turns</TableHead>
                  <TableHead>PLWD Turns</TableHead>
                  <TableHead>Caregiver Words</TableHead>
                  <TableHead>PLWD Words</TableHead>
                  <TableHead>Overlapping Speech</TableHead>
                  <TableHead>Dominance Ratio</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {weekly.map((w, idx) => (
                  <TableRow key={idx}>
                    <TableCell className="font-medium">{w.week}</TableCell>
                    <TableCell>{w.cTurns}</TableCell>
                    <TableCell>{w.pTurns}</TableCell>
                    <TableCell>{w.cWords}</TableCell>
                    <TableCell>{w.pWords}</TableCell>
                    <TableCell className="text-amber-700">{w.overlap}</TableCell>
                    <TableCell>{Number.isFinite(w.dominance_ratio) ? w.dominance_ratio.toFixed(2) : "∞"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Turn Balance Scatter (Dynamic) */}
      <Card>
        <CardHeader>
          <CardTitle>Turn Balance Scatter</CardTitle>
          <CardDescription>Diagonal line denotes balanced turns (Caregiver = PLWD)</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3 mb-4">
            <select value={aggLevel} onChange={(e)=>setAggLevel(e.target.value as any)} className="px-3 py-2 border rounded-md">
              <option value="Week">Aggregate: Week</option>
              <option value="File">Aggregate: File</option>
            </select>
            {aggLevel === "File" && (
              <select value={selectedWeek} onChange={(e)=>setSelectedWeek(e.target.value)} className="px-3 py-2 border rounded-md">
                {weeksList.map(w => <option key={w} value={w}>{w}</option>)}
              </select>
            )}
            <select value={colorBy} onChange={(e)=>setColorBy(e.target.value as any)} className="px-3 py-2 border rounded-md">
              <option value="condition">Color by: Condition</option>
              <option value="session_type">Color by: Session</option>
              <option value="patient_id">Color by: Patient</option>
            </select>
            <select value={sizeBy} onChange={(e)=>setSizeBy(e.target.value as any)} className="px-3 py-2 border rounded-md">
              <option value="overlap">Size by: Overlap ('/')</option>
              <option value="turn_diff_abs">Size by: |Turn Diff|</option>
              <option value="total_words">Size by: Total Words</option>
            </select>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">Bubble max</span>
              <input type="range" min={80} max={260} value={bubbleMax} onChange={(e)=>setBubbleMax(parseInt(e.target.value))} />
              <span className="text-xs">{bubbleMax}</span>
            </div>
          </div>
          <ChartContainer config={legendConfig}>
            <ScatterChart>
              <CartesianGrid />
              <XAxis type="number" dataKey="x" name="Caregiver Turns" />
              <YAxis type="number" dataKey="y" name="PLWD Turns" />
              <Tooltip cursor={false} content={<ChartTooltipContent />} />
              <Legend />
              <ReferenceLine segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]} ifOverflow="extendDomain" stroke="var(--muted-foreground)" strokeDasharray="5 5" />
              <ZAxis dataKey="size" range={[40, bubbleMax]} />
              {Array.from(scatterGroups.entries()).map(([key, pts], i) => (
                <Scatter key={key} name={key} data={pts} dataKey={`series_${i}`} fill={`var(--chart-${(i % 5) + 1})`} />
              ))}
            </ScatterChart>
          </ChartContainer>
        </CardContent>
      </Card>
    </div>
  )
}


