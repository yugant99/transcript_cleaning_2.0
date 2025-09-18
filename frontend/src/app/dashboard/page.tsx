"use client"

import { useState, useEffect } from "react"
import { AnimatedGradientBackground } from "@/components/ui/animated-gradient"
import { motion } from "framer-motion"
import { EvervaultCard, Icon } from "@/components/ui/evervault-card"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Download, Users, Calendar, MessageSquare, Activity } from "lucide-react"

// Types
interface MetricData {
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
  caregiver_questions: number
  plwd_questions: number
  caregiver_disfluencies: number
  plwd_disfluencies: number
  avg_words_per_turn: number
  caregiver_words_per_utterance: number
  plwd_words_per_utterance: number
  pain_mentions?: number
  comfort_mentions?: number
}

interface PatientSummary {
  patient_id: string
  total_sessions: number
  total_weeks: number
  ep_sessions: number
  er_sessions: number
  total_words: number
  data: MetricData[]
}

export default function DashboardPage() {
  const [patients, setPatients] = useState<PatientSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedPatient, setSelectedPatient] = useState<PatientSummary | null>(null)

  useEffect(() => {
    const fetchPatients = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/patients')
        if (!response.ok) {
          throw new Error('Failed to fetch patients')
        }
        const data = await response.json()
        setPatients(data)
      } catch (error) {
        console.error('Error fetching patients:', error)
        // Fallback to empty array if API fails
        setPatients([])
      } finally {
        setLoading(false)
      }
    }

    fetchPatients()
  }, [])

  const downloadCSV = (patient: PatientSummary) => {
    const headers = [
      'Week Label', 'Session Type', 'Condition', 'Filename',
      'Caregiver Turns', 'PLWD Turns', 'Caregiver Words', 'PLWD Words',
      'Caregiver Sentences', 'PLWD Sentences', 'PLWD Nonverbal', 'Caregiver Nonverbal',
      'Pain Mentions', 'Comfort Mentions', 'Caregiver Questions', 'PLWD Questions',
      'Caregiver Disfluencies', 'PLWD Disfluencies', 'Avg Words per Turn',
      'Caregiver Words per Utterance', 'PLWD Words per Utterance'
    ]

    const csvContent = [
      headers.join(','),
      ...patient.data.map(row => [
        row.week_label, row.session_type, row.condition, row.filename,
        row.caregiver_turns, row.plwd_turns, row.caregiver_words, row.plwd_words,
        row.caregiver_sentences, row.plwd_sentences, row.plwd_nonverbal, row.caregiver_nonverbal,
        row.pain_mentions || 0, row.comfort_mentions || 0, row.caregiver_questions, row.plwd_questions,
        row.caregiver_disfluencies, row.plwd_disfluencies, row.avg_words_per_turn,
        row.caregiver_words_per_utterance, row.plwd_words_per_utterance
      ].join(','))
    ].join('\n')

    const blob = new Blob([csvContent], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${patient.patient_id}_analysis.csv`
    a.click()
    window.URL.revokeObjectURL(url)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="relative min-h-screen">
      <AnimatedGradientBackground />
      <div className="space-y-6 p-6">
        <div className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-slate-800">Patient Summary</h2>
          <p className="text-slate-600 mt-2">
            Overview of all patients with detailed metrics and analysis
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 max-w-7xl mx-auto">
        {patients.map((patient, index) => (
          <motion.div
            key={patient.patient_id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <Dialog>
              <DialogTrigger asChild>
                <div className="cursor-pointer group">
                  <div className="relative rounded-xl border-2 border-slate-200/50 bg-white/60 backdrop-blur-sm shadow-lg hover:shadow-xl transition-all duration-300 hover:border-blue-300/60 hover:-translate-y-1 overflow-hidden">
                    <EvervaultCard text={`Patient ${patient.patient_id.toUpperCase()}`}>
                      <div className="p-6 space-y-4 text-center">
                        <div className="mb-4">
                          <h3 className="text-xl font-bold text-white mb-2 group-hover:text-blue-100 transition-colors">
                            Patient {patient.patient_id.toUpperCase()}
                          </h3>
                          <p className="text-gray-300 text-sm">
                            Click to view detailed analysis
                          </p>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div className="flex flex-col items-center gap-1 text-white">
                            <Calendar className="h-4 w-4 text-blue-400" />
                            <span className="font-medium">{patient.total_sessions}</span>
                            <span className="text-gray-300 text-xs">Sessions</span>
                          </div>
                          <div className="flex flex-col items-center gap-1 text-white">
                            <Users className="h-4 w-4 text-green-400" />
                            <span className="font-medium">{patient.total_weeks}</span>
                            <span className="text-gray-300 text-xs">Weeks</span>
                          </div>
                          <div className="flex flex-col items-center gap-1 text-white">
                            <Activity className="h-4 w-4 text-purple-400" />
                            <span className="font-medium text-xs">EP: {patient.ep_sessions} | ER: {patient.er_sessions}</span>
                            <span className="text-gray-300 text-xs">Sessions</span>
                          </div>
                          <div className="flex flex-col items-center gap-1 text-white">
                            <MessageSquare className="h-4 w-4 text-orange-400" />
                            <span className="font-medium">{patient.total_words.toLocaleString()}</span>
                            <span className="text-gray-300 text-xs">Words</span>
                          </div>
                        </div>
                      </div>
                    </EvervaultCard>
                    
                    {/* Decorative border glow */}
                    <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-blue-400/20 via-purple-400/20 to-indigo-400/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />
                  </div>
                </div>
              </DialogTrigger>
              
              <DialogContent className="max-w-6xl max-h-[90vh] overflow-hidden">
                <DialogHeader className="text-center">
                  <DialogTitle className="flex items-center justify-between">
                    <span>Patient {patient.patient_id.toUpperCase()} - Detailed Analysis</span>
                    <Button onClick={() => downloadCSV(patient)} variant="outline" size="sm">
                      <Download className="h-4 w-4 mr-2" />
                      Download CSV
                    </Button>
                  </DialogTitle>
                </DialogHeader>
                
                <div className="overflow-auto max-h-[70vh] text-center">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Week Label</TableHead>
                        <TableHead>Session Type</TableHead>
                        <TableHead>Condition</TableHead>
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
                        <TableHead>Caregiver Disfluencies</TableHead>
                        <TableHead>PLWD Disfluencies</TableHead>
                        <TableHead>Avg Words per Turn</TableHead>
                        <TableHead>Caregiver Words per Utterance</TableHead>
                        <TableHead>PLWD Words per Utterance</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {patient.data.map((row, idx) => (
                        <TableRow key={idx}>
                          <TableCell className="font-medium">{row.week_label}</TableCell>
                          <TableCell>{row.session_type}</TableCell>
                          <TableCell>{row.condition}</TableCell>
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
              </DialogContent>
            </Dialog>
          </motion.div>
        ))}
        </div>
      </div>
    </div>
  )
}
    