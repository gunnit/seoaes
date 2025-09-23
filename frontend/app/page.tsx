'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'
import { Search, Zap, TrendingUp, Shield, CheckCircle, XCircle, AlertTriangle, ArrowRight, BarChart3, Globe, Cpu, Users } from 'lucide-react'
import axios from 'axios'
import toast from 'react-hot-toast'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function HomePage() {
  const [url, setUrl] = useState('')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const router = useRouter()

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!url) {
      toast.error('Please enter a URL to analyze')
      return
    }

    // Validate URL format
    try {
      new URL(url.startsWith('http') ? url : `https://${url}`)
    } catch {
      toast.error('Please enter a valid URL')
      return
    }

    setIsAnalyzing(true)

    try {
      const formattedUrl = url.startsWith('http') ? url : `https://${url}`
      const response = await axios.post(`${API_URL}/api/analyze/free`, {
        url: formattedUrl,
        depth: 1
      })

      // Navigate to analysis page with the analysis ID
      router.push(`/analyze/${response.data.id}`)
    } catch (error) {
      console.error('Analysis failed:', error)
      toast.error('Failed to start analysis. Please try again.')
      setIsAnalyzing(false)
    }
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
          <nav className="hidden md:flex items-center space-x-8">
            <a href="#features" className="text-gray-600 hover:text-primary-600 transition">Features</a>
            <a href="#pricing" className="text-gray-600 hover:text-primary-600 transition">Pricing</a>
            <a href="/login" className="text-gray-600 hover:text-primary-600 transition">Login</a>
            <a href="/signup" className="btn-primary">Get Started</a>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="pt-20 pb-32 px-4">
        <div className="container mx-auto max-w-6xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-center"
          >
            <div className="inline-flex items-center gap-2 bg-amber-100 text-amber-800 px-4 py-2 rounded-full mb-6">
              <AlertTriangle className="w-5 h-5" />
              <span className="font-semibold">Is ChatGPT ignoring your website?</span>
            </div>

            <h1 className="text-5xl md:text-7xl font-bold mb-6">
              Your Website is <span className="gradient-text">Invisible</span> to AI
            </h1>

            <p className="text-xl md:text-2xl text-gray-600 mb-12 max-w-3xl mx-auto">
              90% of websites are blocked from AI search results. Find out why ChatGPT, Perplexity, and Claude can't see your content — and fix it in minutes.
            </p>

            {/* URL Analysis Form */}
            <form onSubmit={handleAnalyze} className="max-w-2xl mx-auto mb-8">
              <div className="flex flex-col md:flex-row gap-4">
                <div className="flex-1 relative">
                  <Globe className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                  <input
                    type="text"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="Enter your website URL..."
                    className="input-field pl-12 text-lg"
                    disabled={isAnalyzing}
                  />
                </div>
                <button
                  type="submit"
                  disabled={isAnalyzing}
                  className="btn-primary flex items-center justify-center gap-2 px-8"
                >
                  {isAnalyzing ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <Search className="w-5 h-5" />
                      Analyze Now
                    </>
                  )}
                </button>
              </div>
            </form>

            <p className="text-sm text-gray-500">
              No signup required • Get results in 60 seconds • 100% free analysis
            </p>

            {/* Trust Indicators */}
            <div className="flex flex-wrap justify-center gap-8 mt-12">
              <div className="flex items-center gap-2 text-gray-600">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <span>50+ Technical Checks</span>
              </div>
              <div className="flex items-center gap-2 text-gray-600">
                <Zap className="w-5 h-5 text-yellow-500" />
                <span>10-Second Insights</span>
              </div>
              <div className="flex items-center gap-2 text-gray-600">
                <Shield className="w-5 h-5 text-blue-500" />
                <span>Enterprise Security</span>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Problem Section */}
      <section className="py-20 bg-gray-50">
        <div className="container mx-auto max-w-6xl px-4">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl font-bold mb-4">The AI Visibility Crisis</h2>
            <p className="text-xl text-gray-600">Most websites are completely invisible to AI search engines</p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: XCircle,
                title: 'Blocked by robots.txt',
                description: '73% of sites unknowingly block ChatGPT and other AI crawlers',
                color: 'text-red-500'
              },
              {
                icon: AlertTriangle,
                title: 'Missing AI Signals',
                description: 'No direct answers, poor structure, missing schema markup',
                color: 'text-yellow-500'
              },
              {
                icon: TrendingUp,
                title: 'Lost Traffic',
                description: 'Missing 40% of future search traffic from AI platforms',
                color: 'text-orange-500'
              }
            ].map((problem, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="card text-center"
              >
                <problem.icon className={`w-16 h-16 mx-auto mb-4 ${problem.color}`} />
                <h3 className="text-xl font-bold mb-2">{problem.title}</h3>
                <p className="text-gray-600">{problem.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20">
        <div className="container mx-auto max-w-6xl px-4">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl font-bold mb-4">Complete AI Visibility Analysis</h2>
            <p className="text-xl text-gray-600">Everything you need to dominate AI search results</p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              {
                title: 'AI Bot Access',
                description: 'Check if ChatGPT, Claude, and Perplexity can access your site',
                icon: Shield
              },
              {
                title: 'Content Structure',
                description: 'Analyze headings, direct answers, and semantic markup',
                icon: BarChart3
              },
              {
                title: 'Technical SEO',
                description: 'Page speed, mobile optimization, and Core Web Vitals',
                icon: Zap
              },
              {
                title: 'AI Readiness Score',
                description: 'Get scored on ChatGPT, Perplexity, and Claude compatibility',
                icon: TrendingUp
              }
            ].map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, scale: 0.95 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.05 }}
                className="card hover:shadow-lg transition-shadow"
              >
                <feature.icon className="w-12 h-12 text-primary-600 mb-4" />
                <h3 className="font-bold mb-2">{feature.title}</h3>
                <p className="text-sm text-gray-600">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 bg-gray-50">
        <div className="container mx-auto max-w-6xl px-4">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl font-bold mb-4">Simple, Transparent Pricing</h2>
            <p className="text-xl text-gray-600">Choose the plan that fits your needs</p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                name: 'Free',
                price: '$0',
                period: '/month',
                features: [
                  '10 website scans per month',
                  '1 page depth analysis',
                  'Basic recommendations',
                  'Email support'
                ],
                cta: 'Start Free',
                highlighted: false
              },
              {
                name: 'Professional',
                price: '$397',
                period: '/month',
                features: [
                  'Unlimited website scans',
                  '50 page depth analysis',
                  'Advanced AI recommendations',
                  'Priority support',
                  'PDF reports',
                  'API access'
                ],
                cta: 'Start Pro Trial',
                highlighted: true
              },
              {
                name: 'Agency',
                price: '$1,497',
                period: '/month',
                features: [
                  'Everything in Professional',
                  '100 page depth analysis',
                  'White-label reports',
                  'Bulk analysis',
                  'Custom integrations',
                  'Dedicated account manager'
                ],
                cta: 'Contact Sales',
                highlighted: false
              }
            ].map((plan, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className={`card ${plan.highlighted ? 'border-primary-500 border-2 shadow-xl' : ''}`}
              >
                {plan.highlighted && (
                  <div className="bg-primary-500 text-white text-sm font-semibold px-3 py-1 rounded-full inline-block mb-4">
                    Most Popular
                  </div>
                )}
                <h3 className="text-2xl font-bold mb-2">{plan.name}</h3>
                <div className="mb-6">
                  <span className="text-4xl font-bold">{plan.price}</span>
                  <span className="text-gray-600">{plan.period}</span>
                </div>
                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <CheckCircle className="w-5 h-5 text-green-500 mt-0.5" />
                      <span className="text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>
                <button className={plan.highlighted ? 'btn-primary w-full' : 'btn-secondary w-full'}>
                  {plan.cta}
                </button>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-primary-600">
        <div className="container mx-auto max-w-4xl px-4 text-center text-white">
          <h2 className="text-4xl font-bold mb-4">
            Stop Being Invisible to AI
          </h2>
          <p className="text-xl mb-8 opacity-90">
            Join 10,000+ websites that have fixed their AI visibility issues
          </p>
          <button
            onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
            className="bg-white text-primary-600 px-8 py-4 rounded-lg font-semibold hover:bg-gray-100 transition inline-flex items-center gap-2"
          >
            Analyze Your Site Now
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-12">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <Cpu className="w-6 h-6 text-primary-400" />
                <span className="text-xl font-bold text-white">AIVisibility.pro</span>
              </div>
              <p className="text-sm">
                The first platform dedicated to AI search optimization.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Product</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#features" className="hover:text-white transition">Features</a></li>
                <li><a href="#pricing" className="hover:text-white transition">Pricing</a></li>
                <li><a href="/api" className="hover:text-white transition">API</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Company</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="/about" className="hover:text-white transition">About</a></li>
                <li><a href="/blog" className="hover:text-white transition">Blog</a></li>
                <li><a href="/contact" className="hover:text-white transition">Contact</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-white mb-4">Legal</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="/privacy" className="hover:text-white transition">Privacy Policy</a></li>
                <li><a href="/terms" className="hover:text-white transition">Terms of Service</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-8 pt-8 text-center text-sm">
            © 2024 AIVisibility.pro. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  )
}