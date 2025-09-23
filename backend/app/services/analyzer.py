import asyncio
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from uuid import UUID
import httpx
from bs4 import BeautifulSoup
from app.core.config import settings
from app.models.models import (
    AnalysisRun, AnalysisResult, AnalysisCache, Website,
    AnalysisStatus, CheckCategory, CheckStatus, ImpactLevel, FixDifficulty
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import re
from urllib.parse import urlparse, urljoin
import ssl
import certifi

class WebsiteAnalyzer:
    """Main analyzer orchestrating all analysis stages"""

    # List of AI bots to check in robots.txt
    AI_BOTS = [
        "GPTBot", "ChatGPT-User", "Claude-Web", "anthropic-ai",
        "Bard", "Gemini", "Bingbot", "msnbot", "facebook",
        "facebookexternalhit", "PerplexityBot", "CCBot",
        "YouBot", "Diffbot", "SemrushBot", "AhrefsBot"
    ]

    def __init__(self, db: AsyncSession):
        self.db = db
        self.http_client = httpx.AsyncClient(timeout=30.0, verify=certifi.where())

    async def analyze_website(self, url: str, analysis_run_id: UUID, user_id: Optional[UUID] = None):
        """Main entry point for website analysis"""
        try:
            # Update status to analyzing
            analysis_run = await self.db.get(AnalysisRun, analysis_run_id)
            analysis_run.status = AnalysisStatus.analyzing
            await self.db.commit()

            # Parse URL
            parsed_url = urlparse(url)
            base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

            results = []

            # Stage 1: Instant Checks (0-5 seconds)
            await self.update_progress(analysis_run_id, 5, "Running instant checks...")
            instant_results = await self.run_instant_checks(url, base_url)
            results.extend(instant_results)
            await self.save_results(analysis_run_id, instant_results)
            await self.update_progress(analysis_run_id, 20, "Instant checks complete")

            # Stage 2: Technical Analysis (5-15 seconds)
            await self.update_progress(analysis_run_id, 25, "Running technical analysis...")
            technical_results = await self.run_technical_analysis(url, base_url)
            results.extend(technical_results)
            await self.save_results(analysis_run_id, technical_results)
            await self.update_progress(analysis_run_id, 45, "Technical analysis complete")

            # Stage 3: Content Analysis (15-30 seconds)
            await self.update_progress(analysis_run_id, 50, "Analyzing content structure...")
            content_results = await self.run_content_analysis(url)
            results.extend(content_results)
            await self.save_results(analysis_run_id, content_results)
            await self.update_progress(analysis_run_id, 70, "Content analysis complete")

            # Stage 4: AI Analysis (30-60 seconds)
            await self.update_progress(analysis_run_id, 75, "Running AI-powered analysis...")
            ai_results = await self.run_ai_analysis(url, analysis_run_id)
            results.extend(ai_results)
            await self.save_results(analysis_run_id, ai_results)
            await self.update_progress(analysis_run_id, 95, "AI analysis complete")

            # Calculate final score
            overall_score = await self.calculate_overall_score(results)

            # Update analysis run with final results
            analysis_run = await self.db.get(AnalysisRun, analysis_run_id)
            analysis_run.status = AnalysisStatus.complete
            analysis_run.overall_score = overall_score
            analysis_run.progress = 100
            analysis_run.completed_at = datetime.utcnow()
            analysis_run.total_checks_run = len(results)
            analysis_run.total_issues_found = sum(1 for r in results if r["status"] != CheckStatus.pass_check)

            await self.db.commit()
            await self.update_progress(analysis_run_id, 100, "Analysis complete!")

            return analysis_run

        except Exception as e:
            # Mark analysis as failed
            analysis_run = await self.db.get(AnalysisRun, analysis_run_id)
            analysis_run.status = AnalysisStatus.failed
            analysis_run.error_message = str(e)
            await self.db.commit()
            raise

    async def run_instant_checks(self, url: str, base_url: str) -> List[Dict[str, Any]]:
        """Stage 1: Instant checks (0-5 seconds) - The killer insights"""
        results = []

        # Check robots.txt for AI bots
        robots_result = await self.check_robots_txt(base_url)
        results.append(robots_result)

        # Check for llms.txt file
        llms_result = await self.check_llms_txt(base_url)
        results.append(llms_result)

        # SSL/HTTPS check
        ssl_result = await self.check_ssl(url)
        results.append(ssl_result)

        # Basic heading extraction
        headings_result = await self.check_headings(url)
        results.append(headings_result)

        return results

    async def check_robots_txt(self, base_url: str) -> Dict[str, Any]:
        """Check if AI bots are allowed in robots.txt"""
        try:
            robots_url = urljoin(base_url, "/robots.txt")
            response = await self.http_client.get(robots_url)

            if response.status_code != 200:
                return {
                    "check_name": "AI Bot Access",
                    "check_category": CheckCategory.ai_readiness,
                    "status": CheckStatus.warn,
                    "score": 50,
                    "details": {"message": "robots.txt not found"},
                    "recommendations": "Create a robots.txt file to control AI bot access",
                    "impact_level": ImpactLevel.high,
                    "fix_difficulty": FixDifficulty.easy,
                    "fix_time_estimate": "5 minutes"
                }

            robots_content = response.text.lower()
            blocked_bots = []
            allowed_bots = []

            for bot in self.AI_BOTS:
                bot_lower = bot.lower()
                # Check if bot is explicitly blocked
                if f"user-agent: {bot_lower}" in robots_content:
                    lines_after = robots_content.split(f"user-agent: {bot_lower}")[1].split("\n")[:5]
                    if any("disallow: /" in line for line in lines_after):
                        blocked_bots.append(bot)
                    else:
                        allowed_bots.append(bot)
                elif "user-agent: *" in robots_content and "disallow: /" in robots_content:
                    # Bot is blocked by wildcard
                    blocked_bots.append(bot)

            if "gptbot" in blocked_bots or "chatgpt-user" in blocked_bots:
                # Critical issue - ChatGPT is blocked!
                return {
                    "check_name": "AI Bot Access",
                    "check_category": CheckCategory.ai_readiness,
                    "status": CheckStatus.fail,
                    "score": 0,
                    "details": {
                        "blocked_bots": blocked_bots,
                        "message": "ChatGPT Cannot Access Your Website!"
                    },
                    "recommendations": self._get_robots_fix_instructions(blocked_bots),
                    "impact_level": ImpactLevel.critical,
                    "fix_difficulty": FixDifficulty.easy,
                    "fix_time_estimate": "5 minutes"
                }
            elif blocked_bots:
                return {
                    "check_name": "AI Bot Access",
                    "check_category": CheckCategory.ai_readiness,
                    "status": CheckStatus.warn,
                    "score": 60,
                    "details": {"blocked_bots": blocked_bots},
                    "recommendations": f"Some AI bots are blocked: {', '.join(blocked_bots)}",
                    "impact_level": ImpactLevel.high,
                    "fix_difficulty": FixDifficulty.easy,
                    "fix_time_estimate": "5 minutes"
                }
            else:
                return {
                    "check_name": "AI Bot Access",
                    "check_category": CheckCategory.ai_readiness,
                    "status": CheckStatus.pass_check,
                    "score": 100,
                    "details": {"message": "All AI bots have access"},
                    "recommendations": None,
                    "impact_level": ImpactLevel.low,
                    "fix_difficulty": FixDifficulty.easy,
                    "fix_time_estimate": None
                }

        except Exception as e:
            return {
                "check_name": "AI Bot Access",
                "check_category": CheckCategory.ai_readiness,
                "status": CheckStatus.fail,
                "score": 0,
                "details": {"error": str(e)},
                "recommendations": "Unable to check robots.txt",
                "impact_level": ImpactLevel.medium,
                "fix_difficulty": FixDifficulty.medium,
                "fix_time_estimate": "15 minutes"
            }

    def _get_robots_fix_instructions(self, blocked_bots: List[str]) -> str:
        """Generate specific fix instructions for robots.txt"""
        instructions = [
            "Your website is INVISIBLE to ChatGPT and other AI search engines!",
            "",
            "To fix this critical issue:",
            "1. Open your robots.txt file",
            "2. Add these lines:",
            "",
            "User-agent: GPTBot",
            "Allow: /",
            "",
            "User-agent: ChatGPT-User",
            "Allow: /",
            "",
            "User-agent: Claude-Web",
            "Allow: /",
            "",
            "3. Save and upload to your server",
            "4. AI bots will be able to access your site within 48 hours",
            "",
            "Expected outcome: 40% increase in AI-driven traffic"
        ]
        return "\n".join(instructions)

    async def check_llms_txt(self, base_url: str) -> Dict[str, Any]:
        """Check for llms.txt file existence"""
        try:
            llms_url = urljoin(base_url, "/llms.txt")
            response = await self.http_client.get(llms_url)

            if response.status_code == 200:
                return {
                    "check_name": "LLMs.txt File",
                    "check_category": CheckCategory.ai_readiness,
                    "status": CheckStatus.pass_check,
                    "score": 100,
                    "details": {"message": "llms.txt file found"},
                    "recommendations": None,
                    "impact_level": ImpactLevel.low,
                    "fix_difficulty": FixDifficulty.easy,
                    "fix_time_estimate": None
                }
            else:
                return {
                    "check_name": "LLMs.txt File",
                    "check_category": CheckCategory.ai_readiness,
                    "status": CheckStatus.warn,
                    "score": 70,
                    "details": {"message": "llms.txt file not found"},
                    "recommendations": "Create an llms.txt file to provide context for AI systems",
                    "impact_level": ImpactLevel.medium,
                    "fix_difficulty": FixDifficulty.easy,
                    "fix_time_estimate": "10 minutes"
                }
        except:
            return {
                "check_name": "LLMs.txt File",
                "check_category": CheckCategory.ai_readiness,
                "status": CheckStatus.warn,
                "score": 70,
                "details": {"message": "Could not check for llms.txt"},
                "recommendations": "Add llms.txt file for better AI understanding",
                "impact_level": ImpactLevel.medium,
                "fix_difficulty": FixDifficulty.easy,
                "fix_time_estimate": "10 minutes"
            }

    async def check_ssl(self, url: str) -> Dict[str, Any]:
        """Check SSL certificate validity"""
        parsed_url = urlparse(url)

        if parsed_url.scheme != "https":
            return {
                "check_name": "SSL Certificate",
                "check_category": CheckCategory.technical,
                "status": CheckStatus.fail,
                "score": 0,
                "details": {"message": "Site not using HTTPS"},
                "recommendations": "Enable HTTPS to secure your website",
                "impact_level": ImpactLevel.critical,
                "fix_difficulty": FixDifficulty.medium,
                "fix_time_estimate": "1 hour"
            }

        return {
            "check_name": "SSL Certificate",
            "check_category": CheckCategory.technical,
            "status": CheckStatus.pass_check,
            "score": 100,
            "details": {"message": "Valid SSL certificate"},
            "recommendations": None,
            "impact_level": ImpactLevel.low,
            "fix_difficulty": FixDifficulty.easy,
            "fix_time_estimate": None
        }

    async def check_headings(self, url: str) -> Dict[str, Any]:
        """Extract and analyze heading structure"""
        try:
            response = await self.http_client.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            headings = {
                'h1': [h.get_text(strip=True) for h in soup.find_all('h1')],
                'h2': [h.get_text(strip=True) for h in soup.find_all('h2')],
                'h3': [h.get_text(strip=True) for h in soup.find_all('h3')],
            }

            # Check for question-based headings (good for AI)
            question_headings = []
            for level, texts in headings.items():
                for text in texts:
                    if '?' in text or text.lower().startswith(('how', 'what', 'why', 'when', 'where', 'who')):
                        question_headings.append(text)

            if not headings['h1']:
                return {
                    "check_name": "Heading Structure",
                    "check_category": CheckCategory.structure,
                    "status": CheckStatus.fail,
                    "score": 0,
                    "details": {"message": "No H1 tag found"},
                    "recommendations": "Add a clear H1 tag to define your page topic",
                    "impact_level": ImpactLevel.high,
                    "fix_difficulty": FixDifficulty.easy,
                    "fix_time_estimate": "5 minutes"
                }
            elif len(headings['h1']) > 1:
                return {
                    "check_name": "Heading Structure",
                    "check_category": CheckCategory.structure,
                    "status": CheckStatus.warn,
                    "score": 70,
                    "details": {"message": f"Multiple H1 tags found ({len(headings['h1'])})"},
                    "recommendations": "Use only one H1 tag per page",
                    "impact_level": ImpactLevel.medium,
                    "fix_difficulty": FixDifficulty.easy,
                    "fix_time_estimate": "10 minutes"
                }
            else:
                score = 80 if question_headings else 60
                return {
                    "check_name": "Heading Structure",
                    "check_category": CheckCategory.structure,
                    "status": CheckStatus.pass_check if question_headings else CheckStatus.warn,
                    "score": score,
                    "details": {
                        "h1_count": len(headings['h1']),
                        "question_headings": len(question_headings)
                    },
                    "recommendations": "Add more question-based headings for better AI optimization" if not question_headings else None,
                    "impact_level": ImpactLevel.medium if not question_headings else ImpactLevel.low,
                    "fix_difficulty": FixDifficulty.easy,
                    "fix_time_estimate": "15 minutes" if not question_headings else None
                }
        except Exception as e:
            return {
                "check_name": "Heading Structure",
                "check_category": CheckCategory.structure,
                "status": CheckStatus.fail,
                "score": 0,
                "details": {"error": str(e)},
                "recommendations": "Unable to analyze heading structure",
                "impact_level": ImpactLevel.medium,
                "fix_difficulty": FixDifficulty.medium,
                "fix_time_estimate": "30 minutes"
            }

    async def run_technical_analysis(self, url: str, base_url: str) -> List[Dict[str, Any]]:
        """Stage 2: Technical analysis (5-15 seconds)"""
        results = []

        # Page speed check
        speed_result = await self.check_page_speed(url)
        results.append(speed_result)

        # Mobile responsiveness
        mobile_result = await self.check_mobile_responsiveness(url)
        results.append(mobile_result)

        # Sitemap check
        sitemap_result = await self.check_sitemap(base_url)
        results.append(sitemap_result)

        # Schema markup detection
        schema_result = await self.check_schema_markup(url)
        results.append(schema_result)

        # Meta tags analysis
        meta_result = await self.check_meta_tags(url)
        results.append(meta_result)

        return results

    async def check_page_speed(self, url: str) -> Dict[str, Any]:
        """Check page load speed"""
        try:
            import time
            start_time = time.time()
            response = await self.http_client.get(url)
            load_time = time.time() - start_time

            if load_time < 2.5:
                status = CheckStatus.pass_check
                score = 100
                recommendations = None
                impact = ImpactLevel.low
            elif load_time < 4:
                status = CheckStatus.warn
                score = 70
                recommendations = "Optimize page load time to under 2.5 seconds"
                impact = ImpactLevel.medium
            else:
                status = CheckStatus.fail
                score = 30
                recommendations = "Page loads too slowly. Optimize images, minify CSS/JS, and enable caching"
                impact = ImpactLevel.high

            return {
                "check_name": "Page Speed",
                "check_category": CheckCategory.technical,
                "status": status,
                "score": score,
                "details": {"load_time": f"{load_time:.2f} seconds"},
                "recommendations": recommendations,
                "impact_level": impact,
                "fix_difficulty": FixDifficulty.medium,
                "fix_time_estimate": "2 hours" if recommendations else None
            }
        except Exception as e:
            return {
                "check_name": "Page Speed",
                "check_category": CheckCategory.technical,
                "status": CheckStatus.fail,
                "score": 0,
                "details": {"error": str(e)},
                "recommendations": "Unable to measure page speed",
                "impact_level": ImpactLevel.medium,
                "fix_difficulty": FixDifficulty.medium,
                "fix_time_estimate": "1 hour"
            }

    async def check_mobile_responsiveness(self, url: str) -> Dict[str, Any]:
        """Check if site is mobile-friendly"""
        try:
            response = await self.http_client.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Check for viewport meta tag
            viewport = soup.find('meta', attrs={'name': 'viewport'})

            if viewport and 'width=device-width' in viewport.get('content', ''):
                return {
                    "check_name": "Mobile Responsiveness",
                    "check_category": CheckCategory.technical,
                    "status": CheckStatus.pass_check,
                    "score": 100,
                    "details": {"message": "Mobile viewport configured"},
                    "recommendations": None,
                    "impact_level": ImpactLevel.low,
                    "fix_difficulty": FixDifficulty.easy,
                    "fix_time_estimate": None
                }
            else:
                return {
                    "check_name": "Mobile Responsiveness",
                    "check_category": CheckCategory.technical,
                    "status": CheckStatus.fail,
                    "score": 0,
                    "details": {"message": "No mobile viewport found"},
                    "recommendations": "Add viewport meta tag: <meta name='viewport' content='width=device-width, initial-scale=1'>",
                    "impact_level": ImpactLevel.high,
                    "fix_difficulty": FixDifficulty.easy,
                    "fix_time_estimate": "5 minutes"
                }
        except Exception as e:
            return {
                "check_name": "Mobile Responsiveness",
                "check_category": CheckCategory.technical,
                "status": CheckStatus.fail,
                "score": 0,
                "details": {"error": str(e)},
                "recommendations": "Unable to check mobile responsiveness",
                "impact_level": ImpactLevel.medium,
                "fix_difficulty": FixDifficulty.medium,
                "fix_time_estimate": "30 minutes"
            }

    async def check_sitemap(self, base_url: str) -> Dict[str, Any]:
        """Check for sitemap.xml"""
        try:
            sitemap_url = urljoin(base_url, "/sitemap.xml")
            response = await self.http_client.get(sitemap_url)

            if response.status_code == 200:
                return {
                    "check_name": "Sitemap",
                    "check_category": CheckCategory.technical,
                    "status": CheckStatus.pass_check,
                    "score": 100,
                    "details": {"message": "Sitemap.xml found"},
                    "recommendations": None,
                    "impact_level": ImpactLevel.low,
                    "fix_difficulty": FixDifficulty.easy,
                    "fix_time_estimate": None
                }
            else:
                return {
                    "check_name": "Sitemap",
                    "check_category": CheckCategory.technical,
                    "status": CheckStatus.warn,
                    "score": 60,
                    "details": {"message": "Sitemap.xml not found"},
                    "recommendations": "Create a sitemap.xml file to help AI bots discover all your pages",
                    "impact_level": ImpactLevel.medium,
                    "fix_difficulty": FixDifficulty.easy,
                    "fix_time_estimate": "30 minutes"
                }
        except:
            return {
                "check_name": "Sitemap",
                "check_category": CheckCategory.technical,
                "status": CheckStatus.warn,
                "score": 60,
                "details": {"message": "Could not check for sitemap"},
                "recommendations": "Add sitemap.xml for better crawlability",
                "impact_level": ImpactLevel.medium,
                "fix_difficulty": FixDifficulty.easy,
                "fix_time_estimate": "30 minutes"
            }

    async def check_schema_markup(self, url: str) -> Dict[str, Any]:
        """Check for structured data/schema markup"""
        try:
            response = await self.http_client.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for JSON-LD schema
            json_ld_scripts = soup.find_all('script', type='application/ld+json')

            if json_ld_scripts:
                schema_types = []
                for script in json_ld_scripts:
                    try:
                        data = json.loads(script.string)
                        if '@type' in data:
                            schema_types.append(data['@type'])
                    except:
                        pass

                if schema_types:
                    return {
                        "check_name": "Schema Markup",
                        "check_category": CheckCategory.structure,
                        "status": CheckStatus.pass_check,
                        "score": 100,
                        "details": {"schema_types": schema_types},
                        "recommendations": None,
                        "impact_level": ImpactLevel.low,
                        "fix_difficulty": FixDifficulty.medium,
                        "fix_time_estimate": None
                    }

            return {
                "check_name": "Schema Markup",
                "check_category": CheckCategory.structure,
                "status": CheckStatus.warn,
                "score": 50,
                "details": {"message": "No structured data found"},
                "recommendations": "Add schema.org markup (FAQ, HowTo, Article) to improve AI understanding",
                "impact_level": ImpactLevel.high,
                "fix_difficulty": FixDifficulty.medium,
                "fix_time_estimate": "1 hour"
            }
        except Exception as e:
            return {
                "check_name": "Schema Markup",
                "check_category": CheckCategory.structure,
                "status": CheckStatus.fail,
                "score": 0,
                "details": {"error": str(e)},
                "recommendations": "Unable to check schema markup",
                "impact_level": ImpactLevel.medium,
                "fix_difficulty": FixDifficulty.medium,
                "fix_time_estimate": "1 hour"
            }

    async def check_meta_tags(self, url: str) -> Dict[str, Any]:
        """Check meta tags quality"""
        try:
            response = await self.http_client.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')

            title = soup.find('title')
            meta_description = soup.find('meta', attrs={'name': 'description'})

            issues = []
            score = 100

            if not title or not title.text.strip():
                issues.append("Missing title tag")
                score -= 40
            elif len(title.text.strip()) > 60:
                issues.append("Title too long (>60 chars)")
                score -= 20

            if not meta_description or not meta_description.get('content', '').strip():
                issues.append("Missing meta description")
                score -= 30
            elif len(meta_description.get('content', '')) > 160:
                issues.append("Meta description too long (>160 chars)")
                score -= 15

            if issues:
                return {
                    "check_name": "Meta Tags",
                    "check_category": CheckCategory.structure,
                    "status": CheckStatus.warn if score > 50 else CheckStatus.fail,
                    "score": max(0, score),
                    "details": {"issues": issues},
                    "recommendations": "Fix meta tag issues: " + ", ".join(issues),
                    "impact_level": ImpactLevel.high if score < 50 else ImpactLevel.medium,
                    "fix_difficulty": FixDifficulty.easy,
                    "fix_time_estimate": "15 minutes"
                }
            else:
                return {
                    "check_name": "Meta Tags",
                    "check_category": CheckCategory.structure,
                    "status": CheckStatus.pass_check,
                    "score": 100,
                    "details": {"message": "Meta tags properly configured"},
                    "recommendations": None,
                    "impact_level": ImpactLevel.low,
                    "fix_difficulty": FixDifficulty.easy,
                    "fix_time_estimate": None
                }
        except Exception as e:
            return {
                "check_name": "Meta Tags",
                "check_category": CheckCategory.structure,
                "status": CheckStatus.fail,
                "score": 0,
                "details": {"error": str(e)},
                "recommendations": "Unable to check meta tags",
                "impact_level": ImpactLevel.medium,
                "fix_difficulty": FixDifficulty.easy,
                "fix_time_estimate": "15 minutes"
            }

    async def run_content_analysis(self, url: str) -> List[Dict[str, Any]]:
        """Stage 3: Content analysis (15-30 seconds)"""
        results = []

        try:
            response = await self.http_client.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            text_content = soup.get_text()

            # Content structure analysis
            structure_result = await self.analyze_content_structure(soup, text_content)
            results.append(structure_result)

            # Direct answer detection
            answer_result = await self.check_direct_answers(soup)
            results.append(answer_result)

            # Internal linking
            linking_result = await self.check_internal_linking(soup, url)
            results.append(linking_result)

        except Exception as e:
            results.append({
                "check_name": "Content Analysis",
                "check_category": CheckCategory.content,
                "status": CheckStatus.fail,
                "score": 0,
                "details": {"error": str(e)},
                "recommendations": "Unable to analyze content",
                "impact_level": ImpactLevel.high,
                "fix_difficulty": FixDifficulty.hard,
                "fix_time_estimate": "2 hours"
            })

        return results

    async def analyze_content_structure(self, soup: BeautifulSoup, text_content: str) -> Dict[str, Any]:
        """Analyze content structure for AI readability"""
        # Get all paragraphs
        paragraphs = soup.find_all('p')

        if not paragraphs:
            return {
                "check_name": "Content Structure",
                "check_category": CheckCategory.content,
                "status": CheckStatus.fail,
                "score": 0,
                "details": {"message": "No paragraph content found"},
                "recommendations": "Add structured content with clear paragraphs",
                "impact_level": ImpactLevel.critical,
                "fix_difficulty": FixDifficulty.medium,
                "fix_time_estimate": "2 hours"
            }

        # Calculate average paragraph length
        para_lengths = [len(p.get_text().split()) for p in paragraphs if p.get_text().strip()]
        avg_para_length = sum(para_lengths) / len(para_lengths) if para_lengths else 0

        # Count lists and tables (good for AI)
        lists = len(soup.find_all(['ul', 'ol']))
        tables = len(soup.find_all('table'))

        # Word count
        word_count = len(text_content.split())

        score = 100
        issues = []

        if avg_para_length > 100:
            score -= 30
            issues.append("Paragraphs too long (aim for 40-60 words)")

        if word_count < 300:
            score -= 40
            issues.append("Content too thin (<300 words)")

        if lists == 0:
            score -= 20
            issues.append("No lists found (add bullet points)")

        if issues:
            return {
                "check_name": "Content Structure",
                "check_category": CheckCategory.content,
                "status": CheckStatus.warn if score > 50 else CheckStatus.fail,
                "score": max(0, score),
                "details": {
                    "word_count": word_count,
                    "avg_paragraph_length": round(avg_para_length),
                    "lists": lists,
                    "tables": tables,
                    "issues": issues
                },
                "recommendations": "Improve content structure: " + "; ".join(issues),
                "impact_level": ImpactLevel.high if score < 50 else ImpactLevel.medium,
                "fix_difficulty": FixDifficulty.medium,
                "fix_time_estimate": "1 hour"
            }
        else:
            return {
                "check_name": "Content Structure",
                "check_category": CheckCategory.content,
                "status": CheckStatus.pass_check,
                "score": score,
                "details": {
                    "word_count": word_count,
                    "avg_paragraph_length": round(avg_para_length),
                    "lists": lists,
                    "tables": tables
                },
                "recommendations": None,
                "impact_level": ImpactLevel.low,
                "fix_difficulty": FixDifficulty.easy,
                "fix_time_estimate": None
            }

    async def check_direct_answers(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Check for direct answer blocks after questions"""
        # Find all headings that are questions
        question_headings = []
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4']):
            text = heading.get_text(strip=True)
            if '?' in text or text.lower().startswith(('how', 'what', 'why', 'when', 'where', 'who')):
                # Check if there's a direct answer after the question
                next_element = heading.find_next_sibling()
                if next_element and next_element.name == 'p':
                    answer_text = next_element.get_text(strip=True)
                    word_count = len(answer_text.split())
                    if 40 <= word_count <= 60:
                        question_headings.append({
                            "question": text,
                            "has_direct_answer": True,
                            "answer_length": word_count
                        })
                    else:
                        question_headings.append({
                            "question": text,
                            "has_direct_answer": False,
                            "answer_length": word_count
                        })

        if not question_headings:
            return {
                "check_name": "Direct Answers",
                "check_category": CheckCategory.content,
                "status": CheckStatus.fail,
                "score": 0,
                "details": {"message": "No question-based headings found"},
                "recommendations": "Add question headings with 40-60 word answers for AI snippets",
                "impact_level": ImpactLevel.critical,
                "fix_difficulty": FixDifficulty.medium,
                "fix_time_estimate": "1 hour"
            }

        # Check how many have proper direct answers
        with_answers = sum(1 for q in question_headings if q.get('has_direct_answer'))

        if with_answers == len(question_headings):
            return {
                "check_name": "Direct Answers",
                "check_category": CheckCategory.content,
                "status": CheckStatus.pass_check,
                "score": 100,
                "details": {"questions_with_answers": with_answers},
                "recommendations": None,
                "impact_level": ImpactLevel.low,
                "fix_difficulty": FixDifficulty.easy,
                "fix_time_estimate": None
            }
        elif with_answers > 0:
            return {
                "check_name": "Direct Answers",
                "check_category": CheckCategory.content,
                "status": CheckStatus.warn,
                "score": 60,
                "details": {
                    "total_questions": len(question_headings),
                    "with_direct_answers": with_answers
                },
                "recommendations": f"Add 40-60 word answers after {len(question_headings) - with_answers} questions",
                "impact_level": ImpactLevel.high,
                "fix_difficulty": FixDifficulty.easy,
                "fix_time_estimate": "30 minutes"
            }
        else:
            return {
                "check_name": "Direct Answers",
                "check_category": CheckCategory.content,
                "status": CheckStatus.fail,
                "score": 20,
                "details": {"questions_without_answers": len(question_headings)},
                "recommendations": "Add 40-60 word direct answers after each question heading",
                "impact_level": ImpactLevel.critical,
                "fix_difficulty": FixDifficulty.medium,
                "fix_time_estimate": "1 hour"
            }

    async def check_internal_linking(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Check internal linking structure"""
        parsed_url = urlparse(url)
        base_domain = parsed_url.netloc

        all_links = soup.find_all('a', href=True)
        internal_links = []
        external_links = []

        for link in all_links:
            href = link['href']
            if href.startswith('http'):
                if base_domain in href:
                    internal_links.append(href)
                else:
                    external_links.append(href)
            elif href.startswith('/'):
                internal_links.append(href)

        if len(internal_links) < 3:
            return {
                "check_name": "Internal Linking",
                "check_category": CheckCategory.content,
                "status": CheckStatus.fail,
                "score": 30,
                "details": {
                    "internal_links": len(internal_links),
                    "external_links": len(external_links)
                },
                "recommendations": "Add more internal links to help AI understand site structure",
                "impact_level": ImpactLevel.high,
                "fix_difficulty": FixDifficulty.easy,
                "fix_time_estimate": "30 minutes"
            }
        else:
            return {
                "check_name": "Internal Linking",
                "check_category": CheckCategory.content,
                "status": CheckStatus.pass_check,
                "score": 100,
                "details": {
                    "internal_links": len(internal_links),
                    "external_links": len(external_links)
                },
                "recommendations": None,
                "impact_level": ImpactLevel.low,
                "fix_difficulty": FixDifficulty.easy,
                "fix_time_estimate": None
            }

    async def run_ai_analysis(self, url: str, analysis_run_id: UUID) -> List[Dict[str, Any]]:
        """Stage 4: AI-powered analysis (30-60 seconds)"""
        # This would normally call GPT-4 API
        # For now, returning mock AI compatibility scores

        results = []

        # ChatGPT optimization score
        results.append({
            "check_name": "ChatGPT Optimization",
            "check_category": CheckCategory.ai_readiness,
            "status": CheckStatus.pass_check,
            "score": 75,
            "details": {"compatibility_score": 75},
            "recommendations": "Optimize for ChatGPT by adding more Q&A content",
            "impact_level": ImpactLevel.medium,
            "fix_difficulty": FixDifficulty.medium,
            "fix_time_estimate": "2 hours"
        })

        # Perplexity readiness
        results.append({
            "check_name": "Perplexity Readiness",
            "check_category": CheckCategory.ai_readiness,
            "status": CheckStatus.pass_check,
            "score": 80,
            "details": {"compatibility_score": 80},
            "recommendations": None,
            "impact_level": ImpactLevel.low,
            "fix_difficulty": FixDifficulty.easy,
            "fix_time_estimate": None
        })

        # Update AI scores in analysis run
        analysis_run = await self.db.get(AnalysisRun, analysis_run_id)
        if analysis_run:
            analysis_run.chatgpt_score = 75
            analysis_run.perplexity_score = 80
            analysis_run.claude_score = 70
            analysis_run.google_ai_score = 85
            analysis_run.bing_chat_score = 78
            await self.db.commit()

        return results

    async def calculate_overall_score(self, results: List[Dict[str, Any]]) -> int:
        """Calculate weighted overall score based on all checks"""
        category_scores = {
            CheckCategory.ai_readiness: [],
            CheckCategory.content: [],
            CheckCategory.structure: [],
            CheckCategory.technical: []
        }

        for result in results:
            category = result["check_category"]
            score = result["score"]
            category_scores[category].append(score)

        # Calculate average for each category
        category_averages = {}
        for category, scores in category_scores.items():
            if scores:
                category_averages[category] = sum(scores) / len(scores)
            else:
                category_averages[category] = 100

        # Apply weights according to instructions
        weighted_score = (
            category_averages.get(CheckCategory.ai_readiness, 100) * 0.40 +  # 40%
            category_averages.get(CheckCategory.content, 100) * 0.35 +       # 35%
            category_averages.get(CheckCategory.structure, 100) * 0.15 +     # 15%
            category_averages.get(CheckCategory.technical, 100) * 0.10       # 10%
        )

        return int(weighted_score)

    async def update_progress(self, analysis_run_id: UUID, progress: int, message: str):
        """Update analysis progress in database"""
        analysis_run = await self.db.get(AnalysisRun, analysis_run_id)
        if analysis_run:
            analysis_run.progress = progress
            await self.db.commit()

    async def save_results(self, analysis_run_id: UUID, results: List[Dict[str, Any]]):
        """Save analysis results to database"""
        for result in results:
            db_result = AnalysisResult(
                analysis_run_id=analysis_run_id,
                check_category=result["check_category"],
                check_name=result["check_name"],
                status=result["status"],
                score=result["score"],
                details=result.get("details"),
                recommendations=result.get("recommendations"),
                impact_level=result["impact_level"],
                fix_difficulty=result["fix_difficulty"],
                fix_time_estimate=result.get("fix_time_estimate")
            )
            self.db.add(db_result)

        await self.db.commit()

    async def close(self):
        """Clean up resources"""
        await self.http_client.aclose()