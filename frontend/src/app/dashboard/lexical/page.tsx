"use client"

import { useEffect, useMemo, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { ChartConfig, ChartContainer, ChartTooltipContent } from "@/components/ui/chart"
import { CartesianGrid, Line, LineChart, XAxis, YAxis, Legend, Tooltip, BarChart, Bar, LabelList, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ComposedChart, Area } from "recharts"

type QARecord = {
  patient_id: string
  week_label: string
  session_type: string
  condition: string
  filename: string
  caregiver_turns: number
  plwd_turns: number
  caregiver_words: number
  plwd_words: number
  caregiver_questions: number
  plwd_questions: number
}

type LexicalRow = QARecord & {
  word_ratio: number
  caregiver_density: number
  plwd_density: number
  question_word_ratio: number
}

export default function LexicalDiversityPage() {
  const [rows, setRows] = useState<LexicalRow[]>([])
  const [loading, setLoading] = useState(true)

  const [selectedParticipants, setSelectedParticipants] = useState<string[]>([])
  const [selectedSessions, setSelectedSessions] = useState<string[]>([])
  const [selectedConditions, setSelectedConditions] = useState<string[]>([])

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/questions-analysis")
        if (!res.ok) throw new Error("Failed to load questions analysis")
        const data: QARecord[] = await res.json()
        const computed: LexicalRow[] = Array.isArray(data) ? data.map((r) => {
          const totalWords = r.caregiver_words + r.plwd_words
          const totalQuestions = r.caregiver_questions + r.plwd_questions
          const word_ratio = totalWords > 0 ? r.plwd_words / totalWords : 0
          const caregiver_density = r.caregiver_turns > 0 ? r.caregiver_words / r.caregiver_turns : 0
          const plwd_density = r.plwd_turns > 0 ? r.plwd_words / r.plwd_turns : 0
          const question_word_ratio = totalWords > 0 ? totalQuestions / totalWords : 0
          return { ...r, word_ratio, caregiver_density, plwd_density, question_word_ratio }
        }) : []
        setRows(computed)
      } catch (e) {
        console.error(e)
        setRows([])
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

  // Chart configs
  const densityConfig: ChartConfig = {
    caregiver: { label: "Caregiver Density", color: "var(--chart-1)" },
    plwd: { label: "PLWD Density", color: "var(--chart-2)" },
  }

  const ratioConfig: ChartConfig = {
    qwr: { label: "Question/Word Ratio", color: "var(--chart-3)" },
    wordRatio: { label: "PLWD Word Share", color: "var(--chart-2)" },
  }

  // Aggregations
  const byWeek = useMemo(() => {
    const m = new Map<string, { week: string; caregiver: number; plwd: number; cTurns: number; pTurns: number; totalWords: number; totalQuestions: number; count: number }>()
    filtered.forEach(r => {
      const key = r.week_label
      const cur = m.get(key) || { week: r.week_label, caregiver: 0, plwd: 0, cTurns: 0, pTurns: 0, totalWords: 0, totalQuestions: 0, count: 0 }
      cur.caregiver += r.caregiver_words
      cur.plwd += r.plwd_words
      cur.cTurns += r.caregiver_turns
      cur.pTurns += r.plwd_turns
      cur.totalWords += r.caregiver_words + r.plwd_words
      cur.totalQuestions += r.caregiver_questions + r.plwd_questions
      cur.count += 1
      m.set(key, cur)
    })
    const arr = Array.from(m.values()).map(v => ({
      week: v.week,
      caregiver: v.cTurns > 0 ? +(v.caregiver / v.cTurns).toFixed(2) : 0,
      plwd: v.pTurns > 0 ? +(v.plwd / v.pTurns).toFixed(2) : 0,
      qwr: v.totalWords > 0 ? +(v.totalQuestions / v.totalWords).toFixed(3) : 0,
      wordRatio: v.totalWords > 0 ? +(v.plwd / v.totalWords).toFixed(3) : 0,
      careWords: v.caregiver,
      plwdWords: v.plwd,
    }))
    // Custom sort Baseline -> Week* -> Final
    return arr.sort((a, b) => {
      if (a.week === 'Baseline') return -1
      if (b.week === 'Baseline') return 1
      if (a.week === 'Final') return 1
      if (b.week === 'Final') return -1
      return a.week.localeCompare(b.week)
    })
  }, [filtered])

  const byParticipant = useMemo(() => {
    const m = new Map<string, { participant: string; caregiver_density: number; plwd_density: number; qwr: number; count: number }>()
    filtered.forEach(r => {
      const id = r.patient_id
      const cur = m.get(id) || { participant: id, caregiver_density: 0, plwd_density: 0, qwr: 0, count: 0 }
      cur.caregiver_density += r.caregiver_density
      cur.plwd_density += r.plwd_density
      cur.qwr += r.question_word_ratio
      cur.count += 1
      m.set(id, cur)
    })
    return Array.from(m.values()).map(v => ({
      participant: v.participant,
      caregiver_density: +(v.caregiver_density / v.count).toFixed(2),
      plwd_density: +(v.plwd_density / v.count).toFixed(2),
      qwr: +(v.qwr / v.count).toFixed(3),
    }))
  }, [filtered])

  if (loading) return <div className="p-6">Loading lexical diversity...</div>

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Lexical Diversity</h1>
      </div>

      {/* Filters */}
      <div className="flex gap-4 mb-6">
        <select
          multiple
          value={selectedParticipants}
          onChange={(e) => setSelectedParticipants(Array.from(e.target.selectedOptions, o => o.value))}
          className="px-3 py-2 border rounded-md min-w-48 h-32"
        >
          {uniqueParticipants.map(p => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>

        <select
          multiple
          value={selectedSessions}
          onChange={(e) => setSelectedSessions(Array.from(e.target.selectedOptions, o => o.value))}
          className="px-3 py-2 border rounded-md min-w-48 h-32"
        >
          {uniqueSessions.map(s => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>

        <select
          multiple
          value={selectedConditions}
          onChange={(e) => setSelectedConditions(Array.from(e.target.selectedOptions, o => o.value))}
          className="px-3 py-2 border rounded-md min-w-48 h-32"
        >
          {uniqueConditions.map(c => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>

      {/* Row 1: Density Trend + Question Ratio by Week */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Speech Density Over Time</CardTitle>
            <CardDescription>Average words per turn by week</CardDescription>
          </CardHeader>
          <CardContent>
            <ChartContainer config={densityConfig}>
              <LineChart data={byWeek}>
                <CartesianGrid vertical={false} />
                <XAxis dataKey="week" tickLine={false} axisLine={false} />
                <YAxis tickLine={false} axisLine={false} />
                <Tooltip cursor={false} content={<ChartTooltipContent />} />
                <Legend />
                <Line dataKey="caregiver" name="Caregiver" stroke="var(--chart-1)" strokeWidth={2} dot={false} />
                <Line dataKey="plwd" name="PLWD" stroke="var(--chart-2)" strokeWidth={2} dot={false} />
              </LineChart>
            </ChartContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Engagement Ratios Over Time</CardTitle>
            <CardDescription>Question/Word and PLWD word share</CardDescription>
          </CardHeader>
          <CardContent>
            <ChartContainer config={ratioConfig}>
              <ComposedChart data={byWeek}>
                <CartesianGrid vertical={false} />
                <XAxis dataKey="week" tickLine={false} axisLine={false} />
                <YAxis tickLine={false} axisLine={false} />
                <Tooltip cursor={false} content={<ChartTooltipContent />} />
                <Legend />
                <Bar dataKey="qwr" name="Question/Word Ratio" fill="var(--chart-3)">
                  <LabelList position="top" dataKey="qwr" />
                </Bar>
                <Line dataKey="wordRatio" name="PLWD Word Share" stroke="var(--chart-2)" strokeWidth={2} dot={false} />
              </ComposedChart>
            </ChartContainer>
          </CardContent>
        </Card>
      </div>

      {/* Row 2: Participant Radar + Words Stacked */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Participant Lexical Profile</CardTitle>
            <CardDescription>Average densities and engagement</CardDescription>
          </CardHeader>
          <CardContent>
            <ChartContainer config={{ caregiver_density: { label: "Caregiver Density" }, plwd_density: { label: "PLWD Density" }, qwr: { label: "Q/W Ratio" } }}>
              <RadarChart data={byParticipant}>
                <PolarGrid />
                <PolarAngleAxis dataKey="participant" />
                <PolarRadiusAxis />
                <Tooltip cursor={false} content={<ChartTooltipContent />} />
                <Legend />
                <Radar dataKey="caregiver_density" name="Caregiver Density" stroke="var(--chart-1)" fill="var(--chart-1)" fillOpacity={0.1} />
                <Radar dataKey="plwd_density" name="PLWD Density" stroke="var(--chart-2)" fill="var(--chart-2)" fillOpacity={0.1} />
                <Radar dataKey="qwr" name="Q/W Ratio" stroke="var(--chart-3)" fill="var(--chart-3)" fillOpacity={0.1} />
              </RadarChart>
            </ChartContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Total Words by Week</CardTitle>
            <CardDescription>Caregiver vs PLWD contribution</CardDescription>
          </CardHeader>
          <CardContent>
            <ChartContainer config={{ careWords: { label: "Caregiver Words" }, plwdWords: { label: "PLWD Words" } }}>
              <BarChart data={byWeek}>
                <CartesianGrid vertical={false} />
                <XAxis dataKey="week" tickLine={false} axisLine={false} />
                <YAxis tickLine={false} axisLine={false} />
                <Tooltip cursor={false} content={<ChartTooltipContent />} />
                <Legend />
                <Bar dataKey="careWords" name="Caregiver Words" stackId="w" fill="var(--chart-1)" />
                <Bar dataKey="plwdWords" name="PLWD Words" stackId="w" fill="var(--chart-2)" />
              </BarChart>
            </ChartContainer>
          </CardContent>
        </Card>
      </div>

      {/* File-wise Detailed Table */}
      <Card>
        <CardHeader>
          <CardTitle>Detailed Lexical Analysis</CardTitle>
          <CardDescription>File-wise lexical metrics and counts</CardDescription>
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
                  <TableHead>Caregiver Density</TableHead>
                  <TableHead>PLWD Density</TableHead>
                  <TableHead>Q/W Ratio</TableHead>
                  <TableHead>PLWD Word Share</TableHead>
                  <TableHead>Total Words</TableHead>
                  <TableHead>Total Turns</TableHead>
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
                    <TableCell className="text-blue-700">{row.caregiver_density.toFixed(2)}</TableCell>
                    <TableCell className="text-green-700">{row.plwd_density.toFixed(2)}</TableCell>
                    <TableCell className="text-amber-700">{row.question_word_ratio.toFixed(3)}</TableCell>
                    <TableCell className="text-indigo-700">{row.word_ratio.toFixed(3)}</TableCell>
                    <TableCell className="font-medium">{(row.caregiver_words + row.plwd_words).toLocaleString()}</TableCell>
                    <TableCell>{row.caregiver_turns + row.plwd_turns}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}


