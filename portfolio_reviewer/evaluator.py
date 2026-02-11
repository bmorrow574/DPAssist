"""
AI Evaluator using Gemini with strict rules from agent.py
"""
import sys
from pathlib import Path

# Add parent directory to Python path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

import google.generativeai as genai
from typing import Dict, List, Optional
from config import config
from schemas.rubric import RubricVersion
from schemas.output import (
    CriterionResult,
    CriterionStatus,
    ConfidenceLevel,
    EvidenceRef,
    EvidenceQuote,
    RunSummary,
)
from schemas.artifact import Artifact, ArtifactSet, ArtifactType
import json
import time


# Configure Gemini
genai.configure(api_key=config.GEMINI_API_KEY)


class PortfolioEvaluator:
    """Evaluate portfolios using Gemini with strict grading rules"""
    
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-1.5-pro')
    
    def evaluate(
        self,
        portfolio_content: Dict,
        rubric: RubricVersion,
        include_scores: bool = False
    ) -> Dict:
        """
        Evaluate portfolio against rubric
        
        Args:
            portfolio_content: Scraped content from portfolio
            rubric: Rubric to evaluate against
            include_scores: Whether to include scores (False before deadline, True after)
            
        Returns:
            Dict with 'results' and 'summary'
        """
        # Build artifact set from scraped content
        artifact_set = self._build_artifact_set(portfolio_content)
        
        # Build strict system prompt
        system_prompt = self._build_system_prompt(rubric, include_scores)
        
        # Build user prompt with portfolio content
        user_prompt = self._build_user_prompt(artifact_set, rubric)
        
        # Call Gemini API
        try:
            response = self.model.generate_content([
                system_prompt,
                user_prompt
            ])
            
            # Parse response
            evaluation = self._parse_evaluation(response.text, rubric, artifact_set)
            
            return evaluation
            
        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            return self._build_error_evaluation(rubric)
    
    def _build_artifact_set(self, portfolio_content: Dict) -> ArtifactSet:
        """Convert scraped content to ArtifactSet"""
        artifacts = []
        
        # Main text content
        if portfolio_content.get('text'):
            artifact = Artifact(
                artifact_id='portfolio_text',
                type=ArtifactType.TEXT,
                source_name=portfolio_content.get('url', 'Portfolio'),
                text=portfolio_content['text']
            )
            artifacts.append(artifact)
        
        # Images as captions
        if portfolio_content.get('images'):
            image_captions = [
                f"Image: {img.get('alt', 'No description')} (src: {img.get('src', '')})"
                for img in portfolio_content['images']
            ]
            
            if image_captions:
                artifact = Artifact(
                    artifact_id='portfolio_images',
                    type=ArtifactType.IMAGE,
                    source_name='Portfolio Images',
                    text='',
                    captions=image_captions
                )
                artifacts.append(artifact)
        
        artifact_set = ArtifactSet(
            artifact_set_id=f"portfolio_{int(time.time())}",
            artifacts=artifacts
        )
        
        return artifact_set
    
    def _build_system_prompt(self, rubric: RubricVersion, include_scores: bool) -> str:
        """Build strict system prompt based on agent.py rules"""
        
        scoring_instruction = ""
        if include_scores:
            scoring_instruction = """
YOU MUST ASSIGN SCORES based on rubric criteria and levels.
"""
        else:
            scoring_instruction = """
DO NOT ASSIGN SCORES. Provide feedback only.
"""
        
        prompt = f"""You are an objective portfolio evaluator. Your role is to assess student work against specific rubric criteria with absolute precision and evidence-based reasoning.

CORE RULES (STRICT - NO EXCEPTIONS):

1. EVIDENCE REQUIREMENTS:
   - MEETS or PARTIALLY_MEETS status REQUIRES direct evidence quotes
   - NOT_YET status must have ZERO evidence quotes
   - Evidence must be exact quotes from portfolio, 10-50 words
   - Each evidence quote must reference location (section/paragraph)

2. CONFIDENCE RULES:
   - MEETS + LOW confidence is FORBIDDEN
   - Use HIGH only when evidence is explicit and complete
   - Use MEDIUM when evidence is present but brief
   - Use LOW only for PARTIALLY_MEETS or NOT_YET

3. OBJECTIVITY:
   - NO encouraging language ("great job", "keep it up")
   - NO subjective opinions
   - NO assumptions beyond what's visible
   - State only what can be verified from evidence

4. COMPLETENESS:
   - Evaluate ALL rubric criteria (no skipping)
   - Each criterion gets exactly one status
   - Each criterion must have feedback

{scoring_instruction}

5. FEEDBACK FORMAT:
   - Be specific and reference rubric requirements
   - Cite what's present and what's missing
   - Use professional, objective tone
   - No congratulatory or motivational language

6. WHAT_TO_ADD:
   - List specific items missing for higher status
   - Be concrete and actionable
   - Reference rubric levels

RUBRIC BEING EVALUATED:
{rubric.title}

CRITERIA:
{self._format_rubric_for_prompt(rubric)}

OUTPUT FORMAT:
Return JSON with this exact structure:
{{
  "results": [
    {{
      "criterion_id": "...",
      "status": "meets|partially_meets|not_yet",
      "score": null or number,
      "max_points": null or number,
      "confidence": "high|medium|low",
      "evidence": [
        {{
          "text": "exact quote from portfolio",
          "location": "section name or paragraph number"
        }}
      ],
      "feedback": "specific objective feedback",
      "what_to_add": ["specific item 1", "specific item 2"]
    }}
  ],
  "summary": {{
    "strengths": ["objective strength 1", "objective strength 2"],
    "biggest_gaps": ["gap 1", "gap 2"],
    "missing_artifacts": ["missing item 1"],
    "teacher_comment_draft": "Professional summary for teacher"
  }}
}}

CRITICAL: Your response must be valid JSON only. No markdown, no preamble, no explanation.
"""
        return prompt
    
    def _format_rubric_for_prompt(self, rubric: RubricVersion) -> str:
        """Format rubric criteria for inclusion in prompt"""
        output = []
        
        for category in rubric.categories:
            output.append(f"\n{category.name}:")
            
            for criterion in category.criteria:
                output.append(f"\n  • {criterion.id}")
                output.append(f"    Title: {criterion.title}")
                output.append(f"    Descriptor: {criterion.descriptor}")
                output.append(f"    Max Points: {criterion.max_points}")
                
                if criterion.levels:
                    output.append("    Levels:")
                    for level in criterion.levels:
                        output.append(f"      - {level.label} ({level.points} pts): {level.descriptor}")
        
        return '\n'.join(output)
    
    def _build_user_prompt(self, artifact_set: ArtifactSet, rubric: RubricVersion) -> str:
        """Build user prompt with portfolio content"""
        
        prompt_parts = ["STUDENT PORTFOLIO CONTENT:\n"]
        
        for artifact in artifact_set.artifacts:
            prompt_parts.append(f"\n--- {artifact.source_name} ---")
            
            if artifact.text:
                prompt_parts.append(artifact.text)
            
            if artifact.captions:
                prompt_parts.append("\nIMAGES:")
                for caption in artifact.captions:
                    prompt_parts.append(f"  • {caption}")
        
        prompt_parts.append("\n\nEVALUATE THIS PORTFOLIO against the rubric criteria. Return JSON only.")
        
        return '\n'.join(prompt_parts)
    
    def _parse_evaluation(
        self,
        response_text: str,
        rubric: RubricVersion,
        artifact_set: ArtifactSet
    ) -> Dict:
        """Parse Gemini response into structured evaluation"""
        
        try:
            # Clean response (remove markdown if present)
            cleaned = response_text.strip()
            if cleaned.startswith('```'):
                # Remove markdown code fences
                lines = cleaned.split('\n')
                cleaned = '\n'.join(lines[1:-1]) if len(lines) > 2 else cleaned
                cleaned = cleaned.replace('```json', '').replace('```', '')
            
            # Parse JSON
            data = json.loads(cleaned)
            
            # Convert to proper schema objects
            results = []
            for result_data in data.get('results', []):
                evidence_quotes = []
                
                for ev in result_data.get('evidence', []):
                    quote = EvidenceQuote(
                        text=ev['text'],
                        ref=EvidenceRef(
                            artifact_id='portfolio_text',
                            source_name='Portfolio',
                            location=ev.get('location', 'Unknown')
                        )
                    )
                    evidence_quotes.append(quote)
                
                result = CriterionResult(
                    criterion_id=result_data['criterion_id'],
                    status=CriterionStatus(result_data['status']),
                    score=result_data.get('score'),
                    max_points=result_data.get('max_points'),
                    confidence=ConfidenceLevel(result_data['confidence']),
                    evidence=evidence_quotes,
                    feedback=result_data.get('feedback', ''),
                    what_to_add=result_data.get('what_to_add', [])
                )
                results.append(result)
            
            summary_data = data.get('summary', {})
            summary = RunSummary(
                strengths=summary_data.get('strengths', []),
                biggest_gaps=summary_data.get('biggest_gaps', []),
                missing_artifacts=summary_data.get('missing_artifacts', []),
                teacher_comment_draft=summary_data.get('teacher_comment_draft', '')
            )
            
            return {
                'results': results,
                'summary': summary
            }
            
        except Exception as e:
            print(f"Error parsing evaluation: {e}")
            print(f"Response was: {response_text[:500]}")
            return self._build_error_evaluation(rubric)
    
    def _build_error_evaluation(self, rubric: RubricVersion) -> Dict:
        """Build error evaluation when AI fails"""
        results = []
        
        for criterion in rubric.all_criteria():
            result = CriterionResult(
                criterion_id=criterion.id,
                status=CriterionStatus.NOT_YET,
                confidence=ConfidenceLevel.LOW,
                evidence=[],
                feedback="Error: Could not evaluate this criterion. Please review manually.",
                what_to_add=["Manual review required"]
            )
            results.append(result)
        
        summary = RunSummary(
            strengths=[],
            biggest_gaps=["Automated evaluation failed - manual review required"],
            missing_artifacts=[],
            teacher_comment_draft="Note: Automated evaluation encountered an error. Please review this submission manually."
        )
        
        return {
            'results': results,
            'summary': summary
        }
