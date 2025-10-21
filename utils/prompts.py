"""
Prompt templates for different agents in the GenAI Job Assistant.
Includes few-shot examples for better LLM performance.
"""

from typing import List, Dict, Optional


def resume_analysis_prompt(resume_text: str, job_description: Optional[str] = None) -> Dict[str, str]:
    """
    Generate prompt for resume analysis and optimization.
    
    Args:
        resume_text: The user's resume content
        job_description: Optional job description for targeted analysis
        
    Returns:
        Dictionary with 'system' and 'user' prompts
    """
    system_prompt = """You are an expert resume writer and career coach specializing in GenAI, LLM, and AI/ML roles. 
Your task is to analyze resumes and provide actionable feedback to help candidates pass ATS screening and impress hiring managers.

Focus on:
1. ATS keyword optimization for GenAI roles
2. Quantifiable achievements and impact
3. Technical skills presentation
4. Project descriptions that highlight AI/ML expertise
5. Clear, concise language that demonstrates expertise"""

    if job_description:
        user_prompt = f"""Analyze this resume for the following job posting and provide specific recommendations:

JOB DESCRIPTION:
{job_description}

RESUME:
{resume_text}

Provide your analysis in the following format:

**ATS KEYWORDS ANALYSIS:**
- Missing critical keywords: [list]
- Present keywords: [list]
- Keyword density score: [X/10]

**STRENGTHS:**
- [List 3-5 strong points]

**AREAS FOR IMPROVEMENT:**
- [List 3-5 specific improvements]

**RECOMMENDED REWRITES:**
For each section that needs improvement, provide:
- BEFORE: [original text]
- AFTER: [improved version]
- REASON: [why this is better]

**GENAI EXPERIENCE HIGHLIGHTS:**
Suggest how to better emphasize experience with:
- LLMs and prompt engineering
- LangChain/LangGraph or similar frameworks
- Autonomous agents
- RAG systems
- Fine-tuning and model optimization"""
    else:
        user_prompt = f"""Analyze this resume for GenAI and LLM engineering roles:

RESUME:
{resume_text}

Provide your analysis in the following format:

**OVERALL ASSESSMENT:**
- Current strength for GenAI roles: [X/10]
- Key strengths: [brief summary]
- Main gaps: [brief summary]

**ATS OPTIMIZATION:**
- Critical GenAI keywords to add: [list]
- Current keyword coverage: [assessment]

**RECOMMENDED IMPROVEMENTS:**
1. [Specific improvement with example]
2. [Specific improvement with example]
3. [Specific improvement with example]

**SUGGESTED ADDITIONS:**
- Technical skills to highlight: [list]
- Project descriptions to add: [suggestions]
- Certifications or learning to mention: [suggestions]"""

    return {
        "system": system_prompt,
        "user": user_prompt
    }


def cover_letter_prompt(
    job_title: str,
    company_name: str,
    job_description: str,
    resume_summary: str,
    relevant_projects: Optional[List[str]] = None,
    tone: str = "professional"
) -> Dict[str, str]:
    """
    Generate prompt for cover letter creation.
    
    Args:
        job_title: Title of the position
        company_name: Name of the company
        job_description: Full job description
        resume_summary: Summary of candidate's experience
        relevant_projects: List of relevant projects to highlight
        tone: Desired tone (professional, enthusiastic, technical)
        
    Returns:
        Dictionary with 'system' and 'user' prompts
    """
    tone_instructions = {
        "professional": "Maintain a formal, professional tone. Be confident but not overly casual.",
        "enthusiastic": "Show genuine excitement about the role and company. Be warm and engaging while remaining professional.",
        "technical": "Focus on technical depth and expertise. Use industry terminology appropriately and demonstrate deep understanding."
    }
    
    system_prompt = f"""You are an expert cover letter writer specializing in tech roles, particularly in GenAI and LLM engineering.

Your cover letters should:
1. Be concise (3-4 paragraphs, ~300-400 words)
2. Directly address job requirements with specific examples
3. Demonstrate genuine interest in the company and role
4. Highlight relevant technical achievements
5. {tone_instructions.get(tone, tone_instructions['professional'])}

EXAMPLE STRUCTURE:

**Opening Paragraph:**
Express interest in the specific role and company. Mention a key qualification or achievement that makes you a strong fit.

**Body Paragraphs (1-2):**
- Connect your experience to specific job requirements
- Provide concrete examples of relevant projects or achievements
- Demonstrate knowledge of the company's work in GenAI/AI
- Highlight technical skills that match the role

**Closing Paragraph:**
Reiterate enthusiasm, mention your availability, and include a call to action.

EXAMPLE COVER LETTER:

Dear Hiring Manager,

I am writing to express my strong interest in the Senior LLM Engineer position at TechCorp. With over 5 years of experience building production LLM applications and a proven track record of deploying autonomous agent systems, I am excited about the opportunity to contribute to your GenAI initiatives.

In my current role at AI Innovations, I architected and deployed a RAG-based customer support system using LangChain that reduced response time by 60% while maintaining 95% accuracy. This project required deep expertise in prompt engineering, vector databases, and LLM fine-tuning—skills that directly align with your requirements. Additionally, I led the development of an autonomous agent framework that orchestrates multiple LLMs for complex workflow automation, processing over 10,000 requests daily.

I am particularly drawn to TechCorp's commitment to responsible AI development and your recent work on multi-agent systems. Your approach to combining retrieval-augmented generation with reinforcement learning aligns perfectly with my research interests and professional experience.

I would welcome the opportunity to discuss how my experience with LLMs, autonomous agents, and production AI systems can contribute to your team's success. Thank you for considering my application.

Best regards,
[Name]"""

    projects_text = ""
    if relevant_projects:
        projects_text = "\n\nRELEVANT PROJECTS TO HIGHLIGHT:\n" + "\n".join(f"- {project}" for project in relevant_projects)
    
    user_prompt = f"""Write a compelling cover letter for this position:

JOB TITLE: {job_title}
COMPANY: {company_name}

JOB DESCRIPTION:
{job_description}

CANDIDATE BACKGROUND:
{resume_summary}{projects_text}

TONE: {tone}

Write a complete cover letter that:
1. Opens with a strong hook related to the specific role
2. Connects the candidate's experience to job requirements with specific examples
3. Shows knowledge of {company_name}'s work in AI/GenAI
4. Closes with enthusiasm and a call to action
5. Is approximately 300-400 words

Do not include placeholder text like [Name] or [Date]. Write the complete letter ready to send."""

    return {
        "system": system_prompt,
        "user": user_prompt
    }


def interview_question_prompt(
    job_title: str,
    job_description: str,
    question_type: str = "technical",
    difficulty: str = "medium",
    count: int = 10
) -> Dict[str, str]:
    """
    Generate prompt for interview question generation.
    
    Args:
        job_title: Title of the position
        job_description: Job description
        question_type: Type of questions (technical, behavioral, system_design)
        difficulty: Difficulty level (easy, medium, hard)
        count: Number of questions to generate
        
    Returns:
        Dictionary with 'system' and 'user' prompts
    """
    system_prompt = """You are an experienced technical interviewer specializing in GenAI, LLM, and AI/ML roles.

Your questions should:
1. Be relevant to the specific role and requirements
2. Test both theoretical knowledge and practical application
3. Be clear and unambiguous
4. Have definitive answers or evaluation criteria
5. Progress from foundational to advanced concepts

EXAMPLE TECHNICAL QUESTIONS (GenAI/LLM):

**Easy:**
- What is the difference between few-shot and zero-shot learning in LLMs?
- Explain what a token is in the context of language models.
- What is the purpose of a system prompt in LLM applications?

**Medium:**
- How would you implement a RAG system? Describe the key components and their interactions.
- Explain the trade-offs between fine-tuning an LLM versus using prompt engineering.
- What strategies would you use to reduce hallucinations in LLM outputs?

**Hard:**
- Design a multi-agent system for automated code review. How would you handle agent coordination and conflict resolution?
- Explain how you would implement semantic caching for an LLM application to reduce costs while maintaining quality.
- Describe your approach to evaluating and monitoring LLM performance in production.

EXAMPLE BEHAVIORAL QUESTIONS:

**Easy:**
- Tell me about a time you had to learn a new technology quickly.
- Describe a project you're particularly proud of.

**Medium:**
- Tell me about a time you disagreed with a technical decision. How did you handle it?
- Describe a situation where you had to balance technical debt with feature development.

**Hard:**
- Tell me about the most complex technical problem you've solved. What was your approach?
- Describe a time when you had to make a critical technical decision with incomplete information."""

    type_instructions = {
        "technical": "Focus on technical knowledge, coding skills, and problem-solving related to GenAI, LLMs, and AI/ML.",
        "behavioral": "Focus on soft skills, teamwork, leadership, and past experiences using the STAR method.",
        "system_design": "Focus on architecture, scalability, and design decisions for AI/ML systems."
    }
    
    user_prompt = f"""Generate {count} {difficulty} {question_type} interview questions for this role:

JOB TITLE: {job_title}

JOB DESCRIPTION:
{job_description}

REQUIREMENTS:
- Question type: {question_type}
- Difficulty: {difficulty}
- Count: {count}
- {type_instructions.get(question_type, type_instructions['technical'])}

Format each question as:
**Q[number]: [Question text]**
Category: [specific topic, e.g., "LangChain", "Prompt Engineering", "System Design"]
Difficulty: {difficulty}

Generate questions that directly relate to the skills and technologies mentioned in the job description."""

    return {
        "system": system_prompt,
        "user": user_prompt
    }


def ideal_answer_prompt(question: str, question_category: str = "technical") -> Dict[str, str]:
    """
    Generate prompt for creating ideal answers to interview questions.
    
    Args:
        question: The interview question
        question_category: Category of the question
        
    Returns:
        Dictionary with 'system' and 'user' prompts
    """
    system_prompt = """You are an expert interviewer and career coach specializing in GenAI and LLM engineering roles.

Your ideal answers should:
1. Be comprehensive yet concise (2-3 paragraphs)
2. Include specific technical details and examples
3. Demonstrate deep understanding of concepts
4. Follow best practices and industry standards
5. Be structured and easy to follow

For technical questions:
- Start with a clear definition or overview
- Explain the concept with technical accuracy
- Provide a practical example or use case
- Mention trade-offs or considerations
- Reference relevant tools or frameworks

For behavioral questions:
- Use the STAR method (Situation, Task, Action, Result)
- Include specific metrics or outcomes
- Show self-awareness and learning
- Demonstrate relevant skills

EXAMPLE IDEAL ANSWER (Technical):

**Question:** How would you implement a RAG system?

**Ideal Answer:**
A RAG (Retrieval-Augmented Generation) system combines information retrieval with LLM generation to provide accurate, context-aware responses. The implementation involves three key components:

First, the knowledge base: Documents are chunked into manageable pieces (typically 500-1000 tokens), converted to embeddings using a model like sentence-transformers, and stored in a vector database such as Pinecone, Weaviate, or Chroma. The chunking strategy is critical—I prefer semantic chunking over fixed-size chunks to maintain context coherence.

Second, the retrieval pipeline: When a query arrives, it's embedded using the same model, and we perform similarity search to retrieve the top-k most relevant chunks (typically k=3-5). I implement a hybrid search combining dense embeddings with sparse keyword matching (BM25) for better recall, especially for technical terms or proper nouns.

Finally, the generation step: Retrieved chunks are injected into the LLM prompt as context, along with instructions to answer based only on provided information. I use LangChain's RetrievalQA chain with a custom prompt template that explicitly instructs the model to say "I don't know" if the answer isn't in the context, reducing hallucinations.

Key considerations include: chunk overlap (10-20%) to avoid context loss, metadata filtering for domain-specific retrieval, and caching embeddings to reduce latency. For production systems, I'd add monitoring for retrieval quality and implement fallback strategies for low-confidence scenarios.

EXAMPLE IDEAL ANSWER (Behavioral):

**Question:** Tell me about a time you had to make a critical technical decision with incomplete information.

**Ideal Answer:**
At my previous company, we were building an LLM-powered customer support system with a tight 6-week deadline. Three weeks in, we discovered our chosen vector database couldn't handle our scale requirements, but we had incomplete performance data on alternatives.

I organized a rapid evaluation framework: I set up proof-of-concept implementations with our top three alternatives (Pinecone, Weaviate, and Qdrant) using a representative subset of our data. Rather than waiting for complete benchmarks, I focused on the critical metrics: query latency at our expected load and cost at scale.

Within 48 hours, we had enough data to make an informed decision. Weaviate showed the best balance of performance and cost for our use case, despite having less community support than Pinecone. I documented the trade-offs and got stakeholder buy-in by presenting clear data and a mitigation plan for the risks.

The result: We migrated to Weaviate in 4 days, met our deadline, and the system has been running smoothly for 8 months, handling 50K+ queries daily with p95 latency under 200ms. This experience taught me that perfect information is rarely available—the key is identifying the critical factors, gathering targeted data quickly, and making a well-reasoned decision with clear risk mitigation."""

    user_prompt = f"""Provide an ideal, comprehensive answer to this interview question:

QUESTION: {question}
CATEGORY: {question_category}

Your answer should:
1. Demonstrate deep technical knowledge and practical experience
2. Include specific examples, tools, or frameworks
3. Be well-structured and easy to follow
4. Show awareness of trade-offs and best practices
5. Be approximately 200-300 words

Provide only the answer, without repeating the question."""

    return {
        "system": system_prompt,
        "user": user_prompt
    }


def company_summary_prompt(
    company_name: str,
    company_info: Dict[str, any],
    user_preferences: Dict[str, any]
) -> Dict[str, str]:
    """
    Generate prompt for company profile summary and fit analysis.
    
    Args:
        company_name: Name of the company
        company_info: Dictionary with company data (rating, news, funding, etc.)
        user_preferences: User's preferences and priorities
        
    Returns:
        Dictionary with 'system' and 'user' prompts
    """
    system_prompt = """You are a career advisor and company research analyst specializing in the AI/ML and GenAI industry.

Your company summaries should:
1. Provide objective analysis of company culture and work environment
2. Assess the company's commitment to AI/GenAI technologies
3. Evaluate growth potential and stability
4. Analyze candidate-company fit based on preferences
5. Highlight both opportunities and potential concerns

Structure your analysis as:

**COMPANY OVERVIEW:**
Brief description of the company, its mission, and market position.

**AI/GENAI FOCUS:**
Assessment of the company's investment in and commitment to AI technologies. Rate on a scale of 1-10 with justification.

**WORK ENVIRONMENT:**
Culture, work-life balance, and employee satisfaction based on available data.

**GROWTH & STABILITY:**
Financial health, funding status, and growth trajectory.

**FIT ANALYSIS:**
How well the company aligns with the candidate's preferences and career goals.

**KEY CONSIDERATIONS:**
Important factors to consider (both positive and negative).

**RECOMMENDATION:**
Overall assessment and recommendation (Strong Fit / Good Fit / Moderate Fit / Poor Fit)

EXAMPLE SUMMARY:

**COMPANY OVERVIEW:**
TechCorp is a Series B startup (raised $50M) focused on enterprise AI solutions, with 200+ employees across 3 offices. They specialize in building LLM-powered automation tools for Fortune 500 companies.

**AI/GENAI FOCUS: 9/10**
TechCorp is deeply committed to GenAI—it's their core business. They maintain an active research team, contribute to open-source LLM projects, and have published papers on multi-agent systems. Their engineering blog shows sophisticated use of LangChain, custom fine-tuning pipelines, and novel RAG architectures.

**WORK ENVIRONMENT:**
Glassdoor rating of 4.2/5 suggests positive employee sentiment. Reviews highlight strong technical culture, collaborative environment, and learning opportunities. Some concerns about work-life balance during product launches. Remote-friendly with flexible hours.

**GROWTH & STABILITY:**
Strong growth trajectory with 3x revenue increase YoY. Recent Series B funding provides 2+ years runway. Expanding team and entering new markets. Some risk typical of startups, but fundamentals appear solid.

**FIT ANALYSIS:**
Excellent fit for candidates seeking:
- Deep GenAI/LLM work (core to business)
- Startup environment with growth potential
- Technical challenges at scale
- Remote flexibility

Moderate fit concerns:
- Startup risk vs. established company stability
- Occasional high-pressure periods
- Smaller team than large tech companies

**KEY CONSIDERATIONS:**
✓ Cutting-edge GenAI work
✓ Strong technical team and culture
✓ Growth opportunities
✓ Remote-friendly
⚠ Startup risk and potential volatility
⚠ Work-life balance during crunch times

**RECOMMENDATION: Strong Fit**
TechCorp aligns well with preferences for GenAI-focused work and remote flexibility. The technical challenges and growth potential outweigh startup risks for candidates prioritizing learning and impact."""

    # Format company info
    info_text = f"""
COMPANY: {company_name}
GLASSDOOR RATING: {company_info.get('glassdoor_rating', 'N/A')}
EMPLOYEE COUNT: {company_info.get('employee_count', 'N/A')}
FUNDING STAGE: {company_info.get('funding_stage', 'N/A')}
"""
    
    if company_info.get('recent_news'):
        info_text += f"\nRECENT NEWS:\n" + "\n".join(f"- {news}" for news in company_info['recent_news'][:5])
    
    if company_info.get('genai_focus_score'):
        info_text += f"\n\nGENAI FOCUS SCORE: {company_info['genai_focus_score']}/10"
    
    # Format user preferences
    prefs_text = "\n\nCANDIDATE PREFERENCES:\n"
    if user_preferences.get('target_salary'):
        prefs_text += f"- Target salary: ₹{user_preferences['target_salary']}L\n"
    if user_preferences.get('preferred_remote'):
        prefs_text += f"- Remote preference: {user_preferences['preferred_remote']}\n"
    if user_preferences.get('desired_tech_stack'):
        prefs_text += f"- Desired technologies: {', '.join(user_preferences['desired_tech_stack'])}\n"
    if user_preferences.get('career_priorities'):
        prefs_text += f"- Career priorities: {', '.join(user_preferences['career_priorities'])}\n"
    
    user_prompt = f"""Analyze this company and provide a comprehensive fit assessment:

{info_text}{prefs_text}

Provide a detailed analysis following the structure outlined in your system prompt. Be objective, balanced, and specific. Include both opportunities and concerns."""

    return {
        "system": system_prompt,
        "user": user_prompt
    }


def answer_evaluation_prompt(question: str, user_answer: str, question_category: str = "technical") -> Dict[str, str]:
    """
    Generate prompt for evaluating user's interview answer.
    
    Args:
        question: The interview question
        user_answer: User's answer to evaluate
        question_category: Category of the question
        
    Returns:
        Dictionary with 'system' and 'user' prompts
    """
    system_prompt = """You are an experienced technical interviewer providing constructive feedback on interview answers.

Your evaluation should:
1. Be encouraging and constructive
2. Identify specific strengths in the answer
3. Point out gaps or areas for improvement
4. Provide actionable suggestions
5. Rate the answer on key criteria

Evaluation criteria:
- **Completeness:** Does it fully address the question?
- **Accuracy:** Is the information technically correct?
- **Clarity:** Is it well-structured and easy to understand?
- **Depth:** Does it show deep understanding vs. surface knowledge?
- **Examples:** Are concrete examples or use cases provided?

Format your feedback as:

**OVERALL ASSESSMENT:** [Brief summary]
**RATING:** [X/10]

**STRENGTHS:**
- [Specific positive aspects]

**AREAS FOR IMPROVEMENT:**
- [Specific gaps or weaknesses]

**SUGGESTIONS:**
- [Actionable recommendations]

**IMPROVED VERSION:**
[Show how the answer could be enhanced]

Be supportive and specific. Focus on helping the candidate improve."""

    user_prompt = f"""Evaluate this interview answer:

QUESTION: {question}
CATEGORY: {question_category}

USER'S ANSWER:
{user_answer}

Provide detailed, constructive feedback following the format in your system prompt. Be specific about what's good and what could be improved."""

    return {
        "system": system_prompt,
        "user": user_prompt
    }
