"use client"

import { useState, useEffect } from "react"
import { CartesianGrid, Line, LineChart, XAxis, PolarAngleAxis, PolarGrid, Radar, RadarChart } from "recharts"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ChartConfig, ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"

interface QuestionData {
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
  total_questions: number
  caregiver_question_rate: number
  plwd_question_rate: number
  overall_question_rate: number
  answer_ratio: number
}

const chartConfig = {
  caregiver: {
    label: "Caregiver Questions",
    color: "var(--chart-1)",
  },
  plwd: {
    label: "PLWD Questions", 
    color: "var(--chart-2)",
  },
  totalQuestions: {
    label: "Question Volume",
    color: "var(--chart-1)",
  },
  engagement: {
    label: "Engagement Score",
    color: "var(--chart-2)",
  },
} satisfies ChartConfig

export default function QuestionsPage() {
  const [data, setData] = useState<QuestionData[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedParticipant, setSelectedParticipant] = useState<string>("all")
  const [selectedSession, setSelectedSession] = useState<string>("all")
  const [selectedCondition, setSelectedCondition] = useState<string>("all")

  useEffect(() => {
    const fetchData = async () => {
      try {
        console.log('Fetching questions data...')
        const response = await fetch('http://localhost:8000/api/questions-analysis')
        console.log('Response status:', response.status)
        if (!response.ok) {
          throw new Error(`Failed to fetch data: ${response.status}`)
        }
        const result = await response.json()
        console.log('Data received:', result?.length || 0, 'records')
        setData(Array.isArray(result) ? result : [])
      } catch (error) {
        console.error('Error fetching data:', error)
        setData([])
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const filteredData = Array.isArray(data) ? data.filter(item => 
    (selectedParticipant === "all" || item.patient_id === selectedParticipant) &&
    (selectedSession === "all" || item.session_type === selectedSession) &&
    (selectedCondition === "all" || item.condition === selectedCondition)
  ) : []

  const trendData = filteredData.length > 0 ? filteredData.reduce((acc, item) => {
    const existing = acc.find(d => d.week === item.week_label)
    if (existing) {
      existing.caregiver += item.caregiver_questions
      existing.plwd += item.plwd_questions
      existing.count += 1
    } else {
      acc.push({
        week: item.week_label,
        caregiver: item.caregiver_questions,
        plwd: item.plwd_questions,
        count: 1
      })
    }
    return acc
  }, [] as any[]).map(d => ({
    ...d,
    caregiver: Math.round(d.caregiver / d.count),
    plwd: Math.round(d.plwd / d.count)
  })) : []

  const radarData = filteredData.length > 0 ? [...new Set(filteredData.map(d => d.patient_id))].map(patientId => {
    const patientData = filteredData.filter(d => d.patient_id === patientId)
    const totalQuestions = patientData.reduce((sum, d) => sum + d.total_questions, 0)
    const avgRatio = patientData.length > 0 ? patientData.reduce((sum, d) => sum + d.answer_ratio, 0) / patientData.length : 0
    const avgRate = patientData.length > 0 ? patientData.reduce((sum, d) => sum + d.overall_question_rate, 0) / patientData.length : 0
    
    return {
      patient: patientId.toUpperCase(),
      totalQuestions: Math.min(totalQuestions / 10, 100),
      balance: avgRatio * 100,
      rate: avgRate,
      engagement: Math.min(avgRatio * Math.log(totalQuestions + 1) * 10, 100),
      sessions: patientData.length
    }
  }) : []

  const uniqueParticipants = Array.isArray(data) ? [...new Set(data.map(d => d.patient_id))] : []
  const uniqueSessions = Array.isArray(data) ? [...new Set(data.map(d => d.session_type))] : []
  const uniqueConditions = Array.isArray(data) ? [...new Set(data.map(d => d.condition))] : []

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      <div className="space-y-6 p-6">
        <div className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-slate-800">Questions & Answers Analysis</h2>
          <p className="text-slate-600 mt-2">Interactive question patterns and engagement analysis</p>
        </div>

        <div className="flex gap-4 justify-center">
          <select 
            value={selectedParticipant} 
            onChange={(e) => setSelectedParticipant(e.target.value)}
            className="px-3 py-2 border rounded-md w-48"
          >
            <option value="all">All Participants</option>
            {uniqueParticipants.map(p => (
              <option key={p} value={p}>{p.toUpperCase()}</option>
            ))}
          </select>

          <select 
            value={selectedSession} 
            onChange={(e) => setSelectedSession(e.target.value)}
            className="px-3 py-2 border rounded-md w-48"
          >
            <option value="all">All Sessions</option>
            {uniqueSessions.map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>

          <select 
            value={selectedCondition} 
            onChange={(e) => setSelectedCondition(e.target.value)}
            className="px-3 py-2 border rounded-md w-48"
          >
            <option value="all">All Conditions</option>
            {uniqueConditions.map(c => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>

        <div className="grid gap-6 md:grid-cols-2 max-w-7xl mx-auto">
          <Card>
            <CardHeader>
              <CardTitle>Question Trends Over Time</CardTitle>
              <CardDescription>Average questions per session by week</CardDescription>
            </CardHeader>
            <CardContent>
              <ChartContainer config={chartConfig} className="h-[300px]">
                <LineChart data={trendData}>
                  <CartesianGrid vertical={false} />
                  <XAxis dataKey="week" tickLine={false} axisLine={false} />
                  <ChartTooltip
                    content={<ChartTooltipContent />}
                  />
                  <Line dataKey="caregiver" stroke="var(--color-caregiver)" strokeWidth={2} dot={{ r: 4 }} />
                  <Line dataKey="plwd" stroke="var(--color-plwd)" strokeWidth={2} dot={{ r: 4 }} />
                </LineChart>
              </ChartContainer>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Multi-Dimensional Analysis</CardTitle>
              <CardDescription>Question patterns across multiple metrics</CardDescription>
            </CardHeader>
            <CardContent>
              <ChartContainer config={chartConfig} className="h-[300px]">
                <RadarChart data={radarData}>
                  <ChartTooltip
                    cursor={false}
                    content={<ChartTooltipContent indicator="line" />}
                  />
                  <PolarAngleAxis dataKey="patient" />
                  <PolarGrid radialLines={false} />
                  <Radar
                    dataKey="totalQuestions"
                    fill="var(--color-caregiver)"
                    fillOpacity={0}
                    stroke="var(--color-caregiver)"
                    strokeWidth={2}
                  />
                  <Radar
                    dataKey="engagement"
                    fill="var(--color-plwd)"
                    fillOpacity={0}
                    stroke="var(--color-plwd)"
                    strokeWidth={2}
                  />
                </RadarChart>
              </ChartContainer>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Questions & Answers Summary by Week</CardTitle>
            <CardDescription>Weekly aggregated question patterns and statistics</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-auto max-h-[400px]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Week</TableHead>
                    <TableHead>Condition</TableHead>
                    <TableHead>Files</TableHead>
                    <TableHead>Patients</TableHead>
                    <TableHead>Caregiver Q</TableHead>
                    <TableHead>PLWD Q</TableHead>
                    <TableHead>Total Q</TableHead>
                    <TableHead>Caregiver %</TableHead>
                    <TableHead>PLWD %</TableHead>
                    <TableHead>Avg C Rate</TableHead>
                    <TableHead>Avg P Rate</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(() => {
                    const summary = filteredData.reduce((acc, row) => {
                      const key = `${row.week_label}-${row.condition}`
                      if (!acc[key]) {
                        acc[key] = {
                          week_label: row.week_label,
                          condition: row.condition,
                          files: 0,
                          patients: new Set(),
                          caregiver_questions: 0,
                          plwd_questions: 0,
                          total_questions: 0,
                          caregiver_words: 0,
                          plwd_words: 0
                        }
                      }
                      acc[key].files += 1
                      acc[key].patients.add(row.patient_id)
                      acc[key].caregiver_questions += row.caregiver_questions
                      acc[key].plwd_questions += row.plwd_questions
                      acc[key].total_questions += row.total_questions
                      acc[key].caregiver_words += row.caregiver_words
                      acc[key].plwd_words += row.plwd_words
                      return acc
                    }, {} as any)

                    return Object.values(summary).map((item: any, idx) => (
                      <TableRow key={idx}>
                        <TableCell className="font-medium">{item.week_label}</TableCell>
                        <TableCell>
                          <span className={`px-2 py-1 text-xs rounded ${item.condition === "VR" ? "bg-blue-100 text-blue-800" : "bg-gray-100 text-gray-800"}`}>
                            {item.condition}
                          </span>
                        </TableCell>
                        <TableCell>{item.files}</TableCell>
                        <TableCell>{item.patients.size}</TableCell>
                        <TableCell>{item.caregiver_questions}</TableCell>
                        <TableCell>{item.plwd_questions}</TableCell>
                        <TableCell className="font-medium">{item.total_questions}</TableCell>
                        <TableCell>{item.total_questions > 0 ? ((item.caregiver_questions / item.total_questions) * 100).toFixed(1) : 0}%</TableCell>
                        <TableCell>{item.total_questions > 0 ? ((item.plwd_questions / item.total_questions) * 100).toFixed(1) : 0}%</TableCell>
                        <TableCell>{item.caregiver_words > 0 ? ((item.caregiver_questions / item.caregiver_words) * 100).toFixed(2) : 0}%</TableCell>
                        <TableCell>{item.plwd_words > 0 ? ((item.plwd_questions / item.plwd_words) * 100).toFixed(2) : 0}%</TableCell>
                      </TableRow>
                    ))
                  })()}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Detailed Analysis Table</CardTitle>
            <CardDescription>File-wise question analysis with calculated metrics</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-auto max-h-[600px]">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Patient</TableHead>
                    <TableHead>Week</TableHead>
                    <TableHead>Session</TableHead>
                    <TableHead>Condition</TableHead>
                    <TableHead>Caregiver Q</TableHead>
                    <TableHead>PLWD Q</TableHead>
                    <TableHead>Total Q</TableHead>
                    <TableHead>C Rate %</TableHead>
                    <TableHead>P Rate %</TableHead>
                    <TableHead>Balance</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredData.map((row, idx) => (
                    <TableRow key={idx}>
                      <TableCell className="font-medium">{row.patient_id.toUpperCase()}</TableCell>
                      <TableCell>{row.week_label}</TableCell>
                      <TableCell>
                        <span className="px-2 py-1 text-xs border rounded">{row.session_type}</span>
                      </TableCell>
                      <TableCell>
                        <span className={`px-2 py-1 text-xs rounded ${row.condition === "VR" ? "bg-blue-100 text-blue-800" : "bg-gray-100 text-gray-800"}`}>
                          {row.condition}
                        </span>
                      </TableCell>
                      <TableCell>{row.caregiver_questions}</TableCell>
                      <TableCell>{row.plwd_questions}</TableCell>
                      <TableCell className="font-medium">{row.total_questions}</TableCell>
                      <TableCell>{row.caregiver_question_rate}%</TableCell>
                      <TableCell>{row.plwd_question_rate}%</TableCell>
                      <TableCell>{(row.answer_ratio * 100).toFixed(1)}%</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
