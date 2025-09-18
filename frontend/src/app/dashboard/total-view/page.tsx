"use client"

import { useEffect, useMemo, useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { ChartConfig, ChartContainer, ChartTooltipContent } from "@/components/ui/chart"
import { CartesianGrid, Line, LineChart, XAxis, YAxis, Legend, Tooltip, BarChart, Bar, LabelList } from "recharts"

type MetricData = {
  patient_id: string
  week_label: string
  session_type: string
  condition: string
  filename: string
  caregiver_turns: number
  plwd_turns: number
  caregiver_words: number
  plwd_words: number
  caregiver_sentences: number
  plwd_sentences: number
  plwd_nonverbal: number
  caregiver_nonverbal: number
  pain_mentions?: number
  comfort_mentions?: number
  caregiver_questions: number
  plwd_questions: number
  caregiver_disfluencies: number
  plwd_disfluencies: number
  avg_words_per_turn: number
  caregiver_words_per_utterance: number
  plwd_words_per_utterance: number
}

type PatientSummary = {
  patient_id: string
  total_sessions: number
  total_weeks: number
  ep_sessions: number
  er_sessions: number
  total_words: number
  data: MetricData[]
}

export default function TotalViewPage() {
  const [patients, setPatients] = useState<PatientSummary[]>([])
  const [loading, setLoading] = useState(true)

  const [selectedParticipants, setSelectedParticipants] = useState<string[]>([])
  const [selectedSessions, setSelectedSessions] = useState<string[]>([])
  const [selectedConditions, setSelectedConditions] = useState<string[]>([])

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/patients")
        if (!res.ok) throw new Error("Failed to load patients")
        const data: PatientSummary[] = await res.json()
        setPatients(Array.isArray(data) ? data : [])
      } catch (e) {
        console.error(e)
        setPatients([])
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  // Flatten rows and apply exclusions + filters
  const allRows = useMemo(() => patients.flatMap(p => p.data || []), [patients])

  const prefiltered = useMemo(() => allRows.filter(r => r.session_type !== "Final Interview"), [allRows])

  const uniqueParticipants = useMemo(() => [...new Set(prefiltered.map(r => r.patient_id))].sort(), [prefiltered])
  const uniqueSessions = useMemo(() => [...new Set(prefiltered.map(r => r.session_type))].sort(), [prefiltered])
  const uniqueConditions = useMemo(() => [...new Set(prefiltered.map(r => r.condition))].sort(), [prefiltered])

  const filtered = useMemo(() => prefiltered.filter(r =>
    (selectedParticipants.length === 0 || selectedParticipants.includes(r.patient_id)) &&
    (selectedSessions.length === 0 || selectedSessions.includes(r.session_type)) &&
    (selectedConditions.length === 0 || selectedConditions.includes(r.condition))
  ), [prefiltered, selectedParticipants, selectedSessions, selectedConditions])

  // Aggregations
  const byWeek = useMemo(() => {
    const m = new Map<string, any>()
    filtered.forEach(r => {
      const key = r.week_label
      const cur = m.get(key) || {
        week: r.week_label,
        caregiver_turns: 0,
        plwd_turns: 0,
        caregiver_words: 0,
        plwd_words: 0,
        caregiver_sentences: 0,
        plwd_sentences: 0,
        caregiver_nonverbal: 0,
        plwd_nonverbal: 0,
        caregiver_questions: 0,
        plwd_questions: 0,
        caregiver_disfluencies: 0,
        plwd_disfluencies: 0,
        pain_mentions: 0,
        comfort_mentions: 0,
      }
      cur.caregiver_turns += r.caregiver_turns
      cur.plwd_turns += r.plwd_turns
      cur.caregiver_words += r.caregiver_words
      cur.plwd_words += r.plwd_words
      cur.caregiver_sentences += r.caregiver_sentences
      cur.plwd_sentences += r.plwd_sentences
      cur.caregiver_nonverbal += r.caregiver_nonverbal
      cur.plwd_nonverbal += r.plwd_nonverbal
      cur.caregiver_questions += r.caregiver_questions
      cur.plwd_questions += r.plwd_questions
      cur.caregiver_disfluencies += r.caregiver_disfluencies
      cur.plwd_disfluencies += r.plwd_disfluencies
      cur.pain_mentions += r.pain_mentions || 0
      cur.comfort_mentions += r.comfort_mentions || 0
      m.set(key, cur)
    })
    const arr = Array.from(m.values()).map(v => ({
      ...v,
      care_words_per_turn: v.caregiver_turns > 0 ? +(v.caregiver_words / v.caregiver_turns).toFixed(2) : 0,
      plwd_words_per_turn: v.plwd_turns > 0 ? +(v.plwd_words / v.plwd_turns).toFixed(2) : 0,
      avg_words_per_turn: (v.caregiver_turns + v.plwd_turns) > 0 ? +(((v.caregiver_words + v.plwd_words) / (v.caregiver_turns + v.plwd_turns)).toFixed(2)) : 0,
      care_words_per_utt: v.caregiver_sentences > 0 ? +(v.caregiver_words / v.caregiver_sentences).toFixed(2) : 0,
      plwd_words_per_utt: v.plwd_sentences > 0 ? +(v.plwd_words / v.plwd_sentences).toFixed(2) : 0,
    }))
    return arr.sort((a, b) => {
      if (a.week === 'Baseline') return -1
      if (b.week === 'Baseline') return 1
      if (a.week === 'Final') return 1
      if (b.week === 'Final') return -1
      return a.week.localeCompare(b.week)
    })
  }, [filtered])

  const byCondition = useMemo(() => {
    const m = new Map<string, any>()
    filtered.forEach(r => {
      const key = r.condition
      const cur = m.get(key) || {
        condition: r.condition,
        caregiver_turns: 0,
        plwd_turns: 0,
        caregiver_words: 0,
        plwd_words: 0,
        caregiver_sentences: 0,
        plwd_sentences: 0,
        caregiver_nonverbal: 0,
        plwd_nonverbal: 0,
        caregiver_questions: 0,
        plwd_questions: 0,
        caregiver_disfluencies: 0,
        plwd_disfluencies: 0,
        pain_mentions: 0,
        comfort_mentions: 0,
      }
      cur.caregiver_turns += r.caregiver_turns
      cur.plwd_turns += r.plwd_turns
      cur.caregiver_words += r.caregiver_words
      cur.plwd_words += r.plwd_words
      cur.caregiver_sentences += r.caregiver_sentences
      cur.plwd_sentences += r.plwd_sentences
      cur.caregiver_nonverbal += r.caregiver_nonverbal
      cur.plwd_nonverbal += r.plwd_nonverbal
      cur.caregiver_questions += r.caregiver_questions
      cur.plwd_questions += r.plwd_questions
      cur.caregiver_disfluencies += r.caregiver_disfluencies
      cur.plwd_disfluencies += r.plwd_disfluencies
      cur.pain_mentions += r.pain_mentions || 0
      cur.comfort_mentions += r.comfort_mentions || 0
      m.set(key, cur)
    })
    return Array.from(m.values()).map(v => ({
      ...v,
      care_words_per_turn: v.caregiver_turns > 0 ? +(v.caregiver_words / v.caregiver_turns).toFixed(2) : 0,
      plwd_words_per_turn: v.plwd_turns > 0 ? +(v.plwd_words / v.plwd_turns).toFixed(2) : 0,
      avg_words_per_turn: (v.caregiver_turns + v.plwd_turns) > 0 ? +(((v.caregiver_words + v.plwd_words) / (v.caregiver_turns + v.plwd_turns)).toFixed(2)) : 0,
      care_words_per_utt: v.caregiver_sentences > 0 ? +(v.caregiver_words / v.caregiver_sentences).toFixed(2) : 0,
      plwd_words_per_utt: v.plwd_sentences > 0 ? +(v.plwd_words / v.plwd_sentences).toFixed(2) : 0,
    }))
  }, [filtered])

  const bySession = useMemo(() => {
    const m = new Map<string, any>()
    filtered.forEach(r => {
      const key = r.session_type
      const cur = m.get(key) || {
        session_type: r.session_type,
        caregiver_turns: 0,
        plwd_turns: 0,
        caregiver_words: 0,
        plwd_words: 0,
        caregiver_sentences: 0,
        plwd_sentences: 0,
        caregiver_nonverbal: 0,
        plwd_nonverbal: 0,
        caregiver_questions: 0,
        plwd_questions: 0,
        caregiver_disfluencies: 0,
        plwd_disfluencies: 0,
        pain_mentions: 0,
        comfort_mentions: 0,
      }
      cur.caregiver_turns += r.caregiver_turns
      cur.plwd_turns += r.plwd_turns
      cur.caregiver_words += r.caregiver_words
      cur.plwd_words += r.plwd_words
      cur.caregiver_sentences += r.caregiver_sentences
      cur.plwd_sentences += r.plwd_sentences
      cur.caregiver_nonverbal += r.caregiver_nonverbal
      cur.plwd_nonverbal += r.plwd_nonverbal
      cur.caregiver_questions += r.caregiver_questions
      cur.plwd_questions += r.plwd_questions
      cur.caregiver_disfluencies += r.caregiver_disfluencies
      cur.plwd_disfluencies += r.plwd_disfluencies
      cur.pain_mentions += r.pain_mentions || 0
      cur.comfort_mentions += r.comfort_mentions || 0
      m.set(key, cur)
    })
    return Array.from(m.values()).map(v => ({
      ...v,
      care_words_per_turn: v.caregiver_turns > 0 ? +(v.caregiver_words / v.caregiver_turns).toFixed(2) : 0,
      plwd_words_per_turn: v.plwd_turns > 0 ? +(v.plwd_words / v.plwd_turns).toFixed(2) : 0,
      avg_words_per_turn: (v.caregiver_turns + v.plwd_turns) > 0 ? +(((v.caregiver_words + v.plwd_words) / (v.caregiver_turns + v.plwd_turns)).toFixed(2)) : 0,
      care_words_per_utt: v.caregiver_sentences > 0 ? +(v.caregiver_words / v.caregiver_sentences).toFixed(2) : 0,
      plwd_words_per_utt: v.plwd_sentences > 0 ? +(v.plwd_words / v.plwd_sentences).toFixed(2) : 0,
    }))
  }, [filtered])

  // Caregiver vs PLWD totals
  const totals = useMemo(() => {
    const sum = filtered.reduce((acc, r) => {
      acc.c_turns += r.caregiver_turns
      acc.p_turns += r.plwd_turns
      acc.c_words += r.caregiver_words
      acc.p_words += r.plwd_words
      acc.c_nonverbal += r.caregiver_nonverbal
      acc.p_nonverbal += r.plwd_nonverbal
      acc.c_questions += r.caregiver_questions
      acc.p_questions += r.plwd_questions
      acc.c_disf += r.caregiver_disfluencies
      acc.p_disf += r.plwd_disfluencies
      acc.pain += r.pain_mentions || 0
      acc.comfort += r.comfort_mentions || 0
      return acc
    }, { c_turns: 0, p_turns: 0, c_words: 0, p_words: 0, c_nonverbal: 0, p_nonverbal: 0, c_questions: 0, p_questions: 0, c_disf: 0, p_disf: 0, pain: 0, comfort: 0 })
    return sum
  }, [filtered])

  if (loading) return <div className="p-6">Loading Total View...</div>

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Total View</h1>
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

      {/* File-Level Data */}
      <Card>
        <CardHeader>
          <CardTitle>File-Level Data</CardTitle>
          <CardDescription>Pain/Comfort via semantic mentions; normalized nonverbal counts included</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-auto max-h-[600px] rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Patient ID</TableHead>
                  <TableHead>Session Type</TableHead>
                  <TableHead>Condition</TableHead>
                  <TableHead>Week</TableHead>
                  <TableHead>Filename</TableHead>
                  <TableHead>Caregiver Turns</TableHead>
                  <TableHead>PLWD Turns</TableHead>
                  <TableHead>Caregiver Words</TableHead>
                  <TableHead>PLWD Words</TableHead>
                  <TableHead>Caregiver Sentences</TableHead>
                  <TableHead>PLWD Sentences</TableHead>
                  <TableHead>PLWD Nonverbal</TableHead>
                  <TableHead>Caregiver Nonverbal</TableHead>
                  <TableHead>Pain Mentions</TableHead>
                  <TableHead>Comfort Mentions</TableHead>
                  <TableHead>Caregiver Questions</TableHead>
                  <TableHead>PLWD Questions</TableHead>
                  <TableHead>Caregiver Disfl.</TableHead>
                  <TableHead>PLWD Disfl.</TableHead>
                  <TableHead>Avg Words / Turn</TableHead>
                  <TableHead>Caregiver Words / Utt.</TableHead>
                  <TableHead>PLWD Words / Utt.</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((row, idx) => (
                  <TableRow key={idx} className="hover:bg-muted/30">
                    <TableCell className="font-medium">{row.patient_id.toUpperCase()}</TableCell>
                    <TableCell>{row.session_type}</TableCell>
                    <TableCell>
                      <span className={`${row.condition === "VR" ? "bg-blue-100 text-blue-800" : "bg-gray-100 text-gray-800"} px-2 py-1 text-xs rounded`}>
                        {row.condition}
                      </span>
                    </TableCell>
                    <TableCell>{row.week_label}</TableCell>
                    <TableCell className="text-xs">{row.filename}</TableCell>
                    <TableCell>{row.caregiver_turns}</TableCell>
                    <TableCell>{row.plwd_turns}</TableCell>
                    <TableCell>{row.caregiver_words}</TableCell>
                    <TableCell>{row.plwd_words}</TableCell>
                    <TableCell>{row.caregiver_sentences}</TableCell>
                    <TableCell>{row.plwd_sentences}</TableCell>
                    <TableCell>{row.plwd_nonverbal}</TableCell>
                    <TableCell>{row.caregiver_nonverbal}</TableCell>
                    <TableCell>{row.pain_mentions || 0}</TableCell>
                    <TableCell>{row.comfort_mentions || 0}</TableCell>
                    <TableCell>{row.caregiver_questions}</TableCell>
                    <TableCell>{row.plwd_questions}</TableCell>
                    <TableCell>{row.caregiver_disfluencies}</TableCell>
                    <TableCell>{row.plwd_disfluencies}</TableCell>
                    <TableCell>{row.avg_words_per_turn}</TableCell>
                    <TableCell>{row.caregiver_words_per_utterance}</TableCell>
                    <TableCell>{row.plwd_words_per_utterance}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Caregiver vs PLWD summary and Pain/Comfort */}
      <Card>
        <CardHeader>
          <CardTitle>Caregiver vs PLWD</CardTitle>
          <CardDescription>Totals across current selection</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-sm mb-3">Total Pain Mentions: <span className="font-medium">{totals.pain}</span> • Total Comfort Mentions: <span className="font-medium">{totals.comfort}</span></div>
          <ChartContainer config={{ caregiver: { label: "Caregiver" }, plwd: { label: "PLWD" } } as ChartConfig}>
            <BarChart data={[
              { metric: 'Turns', caregiver: totals.c_turns, plwd: totals.p_turns },
              { metric: 'Words', caregiver: totals.c_words, plwd: totals.p_words },
              { metric: 'Nonverbal', caregiver: totals.c_nonverbal, plwd: totals.p_nonverbal },
              { metric: 'Questions', caregiver: totals.c_questions, plwd: totals.p_questions },
              { metric: 'Disfluencies', caregiver: totals.c_disf, plwd: totals.p_disf },
            ]}>
              <CartesianGrid vertical={false} />
              <XAxis dataKey="metric" tickLine={false} axisLine={false} />
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

      {/* Week-wise Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Week-wise Summary</CardTitle>
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
                  <TableHead>Caregiver Sentences</TableHead>
                  <TableHead>PLWD Sentences</TableHead>
                  <TableHead>Caregiver NV</TableHead>
                  <TableHead>PLWD NV</TableHead>
                  <TableHead>Pain</TableHead>
                  <TableHead>Comfort</TableHead>
                  <TableHead>Caregiver Q</TableHead>
                  <TableHead>PLWD Q</TableHead>
                  <TableHead>Care W/Turn</TableHead>
                  <TableHead>PLWD W/Turn</TableHead>
                  <TableHead>Avg W/Turn</TableHead>
                  <TableHead>Care W/Utt</TableHead>
                  <TableHead>PLWD W/Utt</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {byWeek.map((row, idx) => (
                  <TableRow key={idx}>
                    <TableCell className="font-medium">{row.week}</TableCell>
                    <TableCell>{row.caregiver_turns}</TableCell>
                    <TableCell>{row.plwd_turns}</TableCell>
                    <TableCell>{row.caregiver_words}</TableCell>
                    <TableCell>{row.plwd_words}</TableCell>
                    <TableCell>{row.caregiver_sentences}</TableCell>
                    <TableCell>{row.plwd_sentences}</TableCell>
                    <TableCell>{row.caregiver_nonverbal}</TableCell>
                    <TableCell>{row.plwd_nonverbal}</TableCell>
                    <TableCell>{row.pain_mentions}</TableCell>
                    <TableCell>{row.comfort_mentions}</TableCell>
                    <TableCell>{row.caregiver_questions}</TableCell>
                    <TableCell>{row.plwd_questions}</TableCell>
                    <TableCell>{row.care_words_per_turn}</TableCell>
                    <TableCell>{row.plwd_words_per_turn}</TableCell>
                    <TableCell>{row.avg_words_per_turn}</TableCell>
                    <TableCell>{row.care_words_per_utt}</TableCell>
                    <TableCell>{row.plwd_words_per_utt}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Condition-wise Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Condition-wise Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-auto max-h-[500px] rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Condition</TableHead>
                  <TableHead>Caregiver Turns</TableHead>
                  <TableHead>PLWD Turns</TableHead>
                  <TableHead>Caregiver Words</TableHead>
                  <TableHead>PLWD Words</TableHead>
                  <TableHead>Caregiver Sentences</TableHead>
                  <TableHead>PLWD Sentences</TableHead>
                  <TableHead>Caregiver NV</TableHead>
                  <TableHead>PLWD NV</TableHead>
                  <TableHead>Pain</TableHead>
                  <TableHead>Comfort</TableHead>
                  <TableHead>Caregiver Q</TableHead>
                  <TableHead>PLWD Q</TableHead>
                  <TableHead>Care W/Turn</TableHead>
                  <TableHead>PLWD W/Turn</TableHead>
                  <TableHead>Avg W/Turn</TableHead>
                  <TableHead>Care W/Utt</TableHead>
                  <TableHead>PLWD W/Utt</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {byCondition.map((row, idx) => (
                  <TableRow key={idx}>
                    <TableCell className="font-medium">{row.condition}</TableCell>
                    <TableCell>{row.caregiver_turns}</TableCell>
                    <TableCell>{row.plwd_turns}</TableCell>
                    <TableCell>{row.caregiver_words}</TableCell>
                    <TableCell>{row.plwd_words}</TableCell>
                    <TableCell>{row.caregiver_sentences}</TableCell>
                    <TableCell>{row.plwd_sentences}</TableCell>
                    <TableCell>{row.caregiver_nonverbal}</TableCell>
                    <TableCell>{row.plwd_nonverbal}</TableCell>
                    <TableCell>{row.pain_mentions}</TableCell>
                    <TableCell>{row.comfort_mentions}</TableCell>
                    <TableCell>{row.caregiver_questions}</TableCell>
                    <TableCell>{row.plwd_questions}</TableCell>
                    <TableCell>{row.care_words_per_turn}</TableCell>
                    <TableCell>{row.plwd_words_per_turn}</TableCell>
                    <TableCell>{row.avg_words_per_turn}</TableCell>
                    <TableCell>{row.care_words_per_utt}</TableCell>
                    <TableCell>{row.plwd_words_per_utt}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Session Type Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Session Type Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-auto max-h-[500px] rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Session Type</TableHead>
                  <TableHead>Caregiver Turns</TableHead>
                  <TableHead>PLWD Turns</TableHead>
                  <TableHead>Caregiver Words</TableHead>
                  <TableHead>PLWD Words</TableHead>
                  <TableHead>Caregiver Sentences</TableHead>
                  <TableHead>PLWD Sentences</TableHead>
                  <TableHead>Caregiver NV</TableHead>
                  <TableHead>PLWD NV</TableHead>
                  <TableHead>Pain</TableHead>
                  <TableHead>Comfort</TableHead>
                  <TableHead>Caregiver Q</TableHead>
                  <TableHead>PLWD Q</TableHead>
                  <TableHead>Care W/Turn</TableHead>
                  <TableHead>PLWD W/Turn</TableHead>
                  <TableHead>Avg W/Turn</TableHead>
                  <TableHead>Care W/Utt</TableHead>
                  <TableHead>PLWD W/Utt</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {bySession.map((row, idx) => (
                  <TableRow key={idx}>
                    <TableCell className="font-medium">{row.session_type}</TableCell>
                    <TableCell>{row.caregiver_turns}</TableCell>
                    <TableCell>{row.plwd_turns}</TableCell>
                    <TableCell>{row.caregiver_words}</TableCell>
                    <TableCell>{row.plwd_words}</TableCell>
                    <TableCell>{row.caregiver_sentences}</TableCell>
                    <TableCell>{row.plwd_sentences}</TableCell>
                    <TableCell>{row.caregiver_nonverbal}</TableCell>
                    <TableCell>{row.plwd_nonverbal}</TableCell>
                    <TableCell>{row.pain_mentions}</TableCell>
                    <TableCell>{row.comfort_mentions}</TableCell>
                    <TableCell>{row.caregiver_questions}</TableCell>
                    <TableCell>{row.plwd_questions}</TableCell>
                    <TableCell>{row.care_words_per_turn}</TableCell>
                    <TableCell>{row.plwd_words_per_turn}</TableCell>
                    <TableCell>{row.avg_words_per_turn}</TableCell>
                    <TableCell>{row.care_words_per_utt}</TableCell>
                    <TableCell>{row.plwd_words_per_utt}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Trend Charts by Week */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Words per Turn by Week</CardTitle>
          </CardHeader>
          <CardContent>
            <ChartContainer config={{ caregiver: { label: "Caregiver" }, plwd: { label: "PLWD" } } as ChartConfig}>
              <LineChart data={byWeek}>
                <CartesianGrid vertical={false} />
                <XAxis dataKey="week" tickLine={false} axisLine={false} />
                <YAxis tickLine={false} axisLine={false} />
                <Tooltip cursor={false} content={<ChartTooltipContent />} />
                <Legend />
                <Line dataKey="care_words_per_turn" name="Caregiver" stroke="var(--chart-1)" strokeWidth={2} dot={false} />
                <Line dataKey="plwd_words_per_turn" name="PLWD" stroke="var(--chart-2)" strokeWidth={2} dot={false} />
              </LineChart>
            </ChartContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Pain and Comfort Mentions by Week</CardTitle>
          </CardHeader>
          <CardContent>
            <ChartContainer config={{ pain_mentions: { label: "Pain" }, comfort_mentions: { label: "Comfort" } } as ChartConfig}>
              <LineChart data={byWeek}>
                <CartesianGrid vertical={false} />
                <XAxis dataKey="week" tickLine={false} axisLine={false} />
                <YAxis tickLine={false} axisLine={false} />
                <Tooltip cursor={false} content={<ChartTooltipContent />} />
                <Legend />
                <Line dataKey="pain_mentions" name="Pain" stroke="var(--chart-1)" strokeWidth={2} dot={false} />
                <Line dataKey="comfort_mentions" name="Comfort" stroke="var(--chart-2)" strokeWidth={2} dot={false} />
              </LineChart>
            </ChartContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}


