from typing import Optional, Dict, Any
import json
from datetime import datetime

from app.core.config import settings


class PromptTemplate:
    """Template for generating analysis prompts."""
    
    @staticmethod
    def get_analysis_prompt(title: str, description: str, background: Optional[str] = None) -> str:
        """Generate the analysis prompt based on the problem details."""
        
        background_section = f"\nBackground: {background}\n" if background else ""
        
        return f"""# Problem Analysis & Innovation Request Template

## PROBLEM STATEMENT
{background_section}
Description: {description}

---

## ANALYSIS REQUEST

Analyze this problem comprehensively and provide:

### 1. EXISTING SOLUTIONS REVIEW
- List current/common approaches used to solve this problem
- For each solution, provide:
  - Algorithm/Technique: [Name and brief description]
  - Time Complexity: O(?)
  - Space Complexity: O(?)
  - Pros: [List 3-4 advantages]
  - Cons: [List 3-4 disadvantages]
  - Use Cases: When this solution is best
  - Real-world Implementation: Industry examples

### 2. COMPARATIVE ANALYSIS TABLE
Create a comparison table across these dimensions:
- Efficiency (Time/Space)
- Scalability
- Implementation Complexity
- Real-world Feasibility
- Resource Requirements

### 3. INNOVATIVE SOLUTIONS
Propose 2-3 novel or hybrid approaches that:
- Improve upon existing solutions
- Address current limitations
- Consider trade-offs (speed vs. memory vs. development time)

For each innovation:
- Approach Name: 
- Core Idea: [Explain the key innovation]
- How it differs: [vs. existing solutions]
- Advantages:
- Disadvantages:
- Feasibility Score: (1-10 with justification)
- Implementation Effort: (Easy/Medium/Hard)

### 4. RECOMMENDED SOLUTION
Based on feasibility, performance, and practical implementation:
- Best Overall Solution: [With reasoning]
- Best for Time Constraints: [When you need speed]
- Best for Production: [For real-world deployment]
- Best for Learning: [For educational purposes]

### 5. SOFTWARE IMPLEMENTATION PLAN
For the recommended solution:
- Architecture Overview: [System design]
- Technology Stack: [Languages/Frameworks suggested]
- Implementation Steps: [Step-by-step breakdown]
- Code Structure: [Pseudocode or skeleton]
- Testing Strategy: [How to validate]
- Performance Optimization Tips: [Key optimizations]

### 6. HARDWARE CONSIDERATIONS (if applicable)
- Hardware Requirements: [CPU, Memory, GPU, Storage]
- Scalability: [How it scales with hardware upgrades]
- Optimization Opportunities: [Using specific hardware features]
- Cost-Performance Analysis: [Hardware investment vs. performance gain]
- Existing Hardware Solutions: [If specialized hardware exists for this]

### 7. PRACTICAL FEASIBILITY ASSESSMENT
Rate the recommended solution on:
- Developers Required: [Number & skill level]
- Development Timeline: [Estimated weeks/months]
- Maintenance Complexity: [Low/Medium/High]
- Scalability Ceiling: [Can it handle 10x/100x growth?]
- Dependencies & Risks: [External libraries, potential issues]

### 8. IMPLEMENTATION ROADMAP

Phase 1: [Weeks 1-2] - Foundation & Setup
Phase 2: [Weeks 3-4] - Core Development
Phase 3: [Weeks 5-6] - Testing & Optimization
Phase 4: [Weeks 7-8] - Deployment & Monitoring

---

## OUTPUT FORMAT PREFERENCE
- Use tables for comparisons
- Use pseudocode/code examples
- Provide diagrams/flowcharts where helpful
- Include actual code snippets for core logic
- Cite real-world examples

Please provide a comprehensive analysis following this template structure. Focus on practical, implementable solutions with clear trade-offs and realistic assessments."""


class ResponseParser:
    """Parse AI responses into structured format."""
    
    @staticmethod
    def parse_analysis_response(response_text: str) -> Dict[str, Any]:
        """
        Parse the AI response into a structured format.
        This is a simplified parser - in production, you might want more sophisticated parsing.
        """
        
        structured_result = {
            "raw_response": response_text,
            "parsed_sections": {},
            "metadata": {
                "parsed_at": datetime.utcnow().isoformat(),
                "parser_version": "1.0"
            }
        }
        
        # Simple section parsing
        sections = [
            "EXISTING SOLUTIONS REVIEW",
            "COMPARATIVE ANALYSIS TABLE", 
            "INNOVATIVE SOLUTIONS",
            "RECOMMENDED SOLUTION",
            "SOFTWARE IMPLEMENTATION PLAN",
            "HARDWARE CONSIDERATIONS",
            "PRACTICAL FEASIBILITY ASSESSMENT",
            "IMPLEMENTATION ROADMAP"
        ]
        
        current_section = None
        section_content = []
        
        lines = response_text.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Check if this line is a section header
            section_found = None
            for section in sections:
                if section.lower() in line.lower() and ('###' in line or '##' in line):
                    section_found = section
                    break
            
            if section_found:
                # Save previous section if exists
                if current_section and section_content:
                    structured_result["parsed_sections"][current_section] = '\n'.join(section_content)
                
                # Start new section
                current_section = section_found
                section_content = []
            elif current_section:
                section_content.append(line)
        
        # Save the last section
        if current_section and section_content:
            structured_result["parsed_sections"][current_section] = '\n'.join(section_content)
        
        return structured_result