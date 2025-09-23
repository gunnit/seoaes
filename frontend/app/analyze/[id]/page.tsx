'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import {
  CheckCircle, XCircle, AlertTriangle, Loader2, ArrowRight,
  Shield, Zap, Globe, BarChart3, FileText, Download, Cpu
} from 'lucide-react'
import axios from 'axios'
import toast from 'react-hot-toast'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface AnalysisResult {
  check_name: string
  check_category: string
  status: 'pass' | 'warn' | 'fail'
  score: number
  recommendations?: string
  impact_level?: string
}

interface AnalysisData {
  analysis_id: string
  status: string
  progress: number
  overall_score?: number
  partial_results?: AnalysisResult[]
  total_issues_found?: number
}

const statusIcons = {
  pass: CheckCircle,
  warn: AlertTriangle,
  fail: XCircle
}

const statusColors = {
  pass: 'text-green-500',
  warn: 'text-yellow-500',
  fail: 'text-red-500'
}

const categoryIcons = {
  ai_readiness: Shield,
  technical: Zap,
  content: FileText,
  structure: Globe
}

export default function AnalyzePage() {
  const params = useParams()
  const router = useRouter()
  const analysisId = params.id as string

  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [eventSource, setEventSource] = useState<EventSource | null>(null)
  const [showSignupPrompt, setShowSignupPrompt] = useState(false)

  useEffect(() => {
    if (!analysisId) return

    // Connect to SSE endpoint for real-time updates
    const es = new EventSource(`${API_URL}/api/analyze/${analysisId}/progress`)

    es.addEventListener('progress', (event) => {
      const data = JSON.parse(event.data)
      setAnalysisData(data)
      setIsLoading(false)

      // Show signup prompt after showing 3 issues
      if (data.partial_results && data.partial_results.length >= 3) {
        setShowSignupPrompt(true)
      }
    })

    es.addEventListener('complete', (event) => {
      const data = JSON.parse(event.data)

      // Fetch preview results for free users
      fetchPreviewResults()

      es.close()
      setEventSource(null)
    })

    es.addEventListener('error', (event) => {
      console.error('SSE error:', event)
      toast.error('Connection lost. Retrying...')
      setIsLoading(false)
    })

    setEventSource(es)

    // Also fetch initial preview data
    fetchPreviewResults()

    return () => {
      if (es) {
        es.close()
      }
    }
  }, [analysisId])

  const fetchPreviewResults = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/analyze/${analysisId}/preview`)
      setAnalysisData({
        analysis_id: analysisId,
        status: response.data.status,
        progress: response.data.progress,
        overall_score: response.data.overall_score,
        partial_results: response.data.preview_results,
        total_issues_found: response.data.total_issues_found
      })
      setShowSignupPrompt(true)
      setIsLoading(false)
    } catch (error) {
      console.error('Failed to fetch preview:', error)
    }
  }

  const getScoreColor = (score?: number) => {
    if (!score) return 'text-gray-400'
    if (score >= 80) return 'text-green-500'
    if (score >= 60) return 'text-yellow-500'
    if (score >= 40) return 'text-orange-500'
    return 'text-red-500'
  }

  const getScoreLabel = (score?: number) => {
    if (!score) return 'Analyzing...'
    if (score >= 80) return 'Excellent'
    if (score >= 60) return 'Good'
    if (score >= 40) return 'Needs Work'
    return 'Critical'
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-md sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <Cpu className="w-8 h-8 text-primary-600" />
            <span className="text-2xl font-bold gradient-text">AIVisibility.pro</span>
          </div>
          <nav className="flex items-center space-x-4">
            <a href="/" className="text-gray-600 hover:text-primary-600 transition">New Analysis</a>
            <a href="/signup" className="btn-primary">Sign Up for Full Report</a>
          </nav>
        </div>
      </header>

      <div className="container mx-auto max-w-6xl px-4 py-8">
        {/* Progress Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-3xl font-bold mb-4">AI Visibility Analysis</h1>

          {/* Progress Bar */}
          <div className="bg-gray-200 rounded-full h-4 overflow-hidden mb-2">
            <motion.div
              className="bg-gradient-to-r from-primary-500 to-primary-600 h-full rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${analysisData?.progress || 0}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>

          <div className="flex justify-between text-sm text-gray-600">
            <span>Progress: {analysisData?.progress || 0}%</span>
            <span>
              {analysisData?.status === 'analyzing' && 'Analyzing your website...'}
              {analysisData?.status === 'complete' && 'Analysis complete!'}
              {analysisData?.status === 'failed' && 'Analysis failed'}
            </span>
          </div>
        </motion.div>

        {/* Overall Score */}
        {analysisData?.overall_score !== undefined && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="card mb-8"
          >
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold mb-2">Overall AI Visibility Score</h2>
                <p className="text-gray-600">
                  Your website scored {analysisData.overall_score} out of 100
                </p>
              </div>
              <div className="text-center">
                <div className={`text-6xl font-bold ${getScoreColor(analysisData.overall_score)}`}>
                  {analysisData.overall_score}
                </div>
                <div className={`text-lg font-semibold ${getScoreColor(analysisData.overall_score)}`}>
                  {getScoreLabel(analysisData.overall_score)}
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* Analysis Stages */}
        <div className="grid md:grid-cols-4 gap-4 mb-8">
          {[
            { name: 'Instant Checks', progress: analysisData?.progress || 0 >= 20 ? 100 : 0, icon: Zap },
            { name: 'Technical Analysis', progress: analysisData?.progress || 0 >= 45 ? 100 : 0, icon: BarChart3 },
            { name: 'Content Analysis', progress: analysisData?.progress || 0 >= 70 ? 100 : 0, icon: FileText },
            { name: 'AI Analysis', progress: analysisData?.progress || 0 >= 95 ? 100 : 0, icon: Shield }
          ].map((stage, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className={`card ${stage.progress === 100 ? 'border-green-500' : 'border-gray-200'}`}
            >
              <stage.icon className={`w-8 h-8 mb-2 ${stage.progress === 100 ? 'text-green-500' : 'text-gray-400'}`} />
              <h3 className="font-semibold">{stage.name}</h3>
              <p className="text-sm text-gray-600">
                {stage.progress === 100 ? 'Complete' : 'Pending'}
              </p>
            </motion.div>
          ))}
        </div>

        {/* Results Section */}
        <div className="space-y-4">
          <h2 className="text-2xl font-bold mb-4">
            Analysis Results {analysisData?.total_issues_found && `(${analysisData.total_issues_found} issues found)`}
          </h2>

          <AnimatePresence>
            {analysisData?.partial_results?.slice(0, showSignupPrompt ? 3 : undefined).map((result, index) => {
              const StatusIcon = statusIcons[result.status]
              const CategoryIcon = categoryIcons[result.check_category as keyof typeof categoryIcons] || Globe

              return (
                <motion.div
                  key={result.check_name}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="card"
                >
                  <div className="flex items-start gap-4">
                    <StatusIcon className={`w-6 h-6 mt-1 ${statusColors[result.status]}`} />

                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <CategoryIcon className="w-4 h-4 text-gray-400" />
                        <span className="text-sm text-gray-500 capitalize">
                          {result.check_category.replace('_', ' ')}
                        </span>
                        {result.impact_level && (
                          <span className={`text-xs px-2 py-1 rounded-full font-semibold
                            ${result.impact_level === 'critical' ? 'bg-red-100 text-red-700' :
                              result.impact_level === 'high' ? 'bg-orange-100 text-orange-700' :
                              result.impact_level === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                              'bg-gray-100 text-gray-700'}`}>
                            {result.impact_level.toUpperCase()}
                          </span>
                        )}
                      </div>

                      <h3 className="font-semibold text-lg mb-2">{result.check_name}</h3>

                      {result.recommendations && (
                        <p className="text-gray-600 mb-2">{result.recommendations}</p>
                      )}

                      <div className="flex items-center gap-4 text-sm">
                        <span className="text-gray-500">Score: {result.score}/100</span>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )
            })}
          </AnimatePresence>

          {/* Signup Prompt */}
          {showSignupPrompt && analysisData?.total_issues_found && analysisData.total_issues_found > 3 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-gradient-to-r from-primary-600 to-purple-600 text-white rounded-xl p-8 text-center"
            >
              <h3 className="text-2xl font-bold mb-4">
                🔒 {analysisData.total_issues_found - 3} More Critical Issues Found
              </h3>
              <p className="text-lg mb-6 opacity-90">
                Sign up now to see all issues, get specific fixes, and download your complete AI visibility report
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <a
                  href="/signup"
                  className="bg-white text-primary-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition inline-flex items-center justify-center gap-2"
                >
                  Create Free Account
                  <ArrowRight className="w-5 h-5" />
                </a>
                <a
                  href="/login"
                  className="border-2 border-white text-white px-8 py-3 rounded-lg font-semibold hover:bg-white/10 transition"
                >
                  Already have an account?
                </a>
              </div>
            </motion.div>
          )}

          {/* Loading State */}
          {isLoading && (
            <div className="text-center py-12">
              <Loader2 className="w-12 h-12 animate-spin text-primary-600 mx-auto mb-4" />
              <p className="text-gray-600">Starting analysis...</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}