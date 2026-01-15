from typing import List
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.team import Team
from app.models.interview import Interview
from app.models.persona import Persona
from app.models.cvp import CVPCanvas
from app.models.roadmap import MVPRoadmap, MVPFeature
from app.models.tasks import ProjectTask # Correct import

class ProjectContextService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_project_context(self, team_id: int) -> str:
        """
        Aggregates all project artifacts into a simplified RAG context string.
        """
        # 1. Fetch Team (Acts as Project)
        team = await self.session.get(Team, team_id)
        if not team:
            return "Project/Team not found."

        context = f"# Project Context: {team.team_name}\n"
        context += f"**Focus**: {team.project_focus}\n\n"

        # 2. Fetch Interviews
        stmt_interviews = select(Interview).where(Interview.team_id == team_id)
        result_interviews = await self.session.execute(stmt_interviews)
        interviews = result_interviews.scalars().all()
        
        context += "## 1. Customer Interviews\n"
        if not interviews:
            context += "(No interviews conducted yet)\n"
        else:
            for idx, interview in enumerate(interviews):
                role = interview.participant_role or "User"
                date = interview.interview_date.strftime('%Y-%m-%d') if interview.interview_date else "Unknown Date"
                # Simplify insights
                insights_summary = "No structured insights."
                if interview.insights_extracted:
                    insights_summary = str(interview.insights_extracted)
                
                context += f"### Interview {idx+1} ({role}, {date})\n"
                context += f"- **Notes/Transcript**: {interview.interview_notes[:500]}...\n" # Truncate checks
                context += f"- **Insights**: {insights_summary}\n\n"

        # 3. Fetch Personas
        stmt_personas = select(Persona).where(Persona.team_id == team_id)
        result_personas = await self.session.execute(stmt_personas)
        personas = result_personas.scalars().all()

        context += "## 2. User Personas\n"
        if not personas:
            context += "(No personas generated yet)\n"
        else:
            for p in personas:
                context += f"### Persona: {p.name}\n"
                context += f"- **Goals**: {p.goals}\n"
                context += f"- **Frustrations**: {p.frustrations}\n\n"

        # 4. Fetch CVP
        stmt_cvp = select(CVPCanvas).where(CVPCanvas.teamid == team_id)
        result_cvp = await self.session.execute(stmt_cvp)
        cvp = result_cvp.scalars().first()

        context += "## 3. Core Value Proposition (CVP)\n"
        if not cvp:
            context += "(No CVP analysis generated yet)\n"
        else:
            context += f"**Value Prop**: {cvp.valueproposition}\n"
            context += f"**Jobs**: {cvp.jobstobedone}\n"
            context += f"**Pains**: {cvp.pains}\n"
            context += f"**Gains**: {cvp.gains}\n\n"


        # 5. Fetch Roadmap
        stmt_roadmap = select(MVPRoadmap).where(MVPRoadmap.team_id == team_id)
        result_roadmap = await self.session.execute(stmt_roadmap)
        roadmap = result_roadmap.scalars().first()

        context += "## 4. Strategic Roadmap\n"
        if not roadmap:
            context += "(No roadmap generated yet)\n"
        else:
            context += f"**Vision**: {roadmap.vision_statement}\n"
            # Could list features if eager loaded, but for now simple check
            context += "(Roadmap exists, assume access to standard plan)\n\n"

        # 6. Fetch Tasks
        stmt_tasks = select(ProjectTask).where(ProjectTask.team_id == team_id)
        result_tasks = await self.session.execute(stmt_tasks)
        tasks = result_tasks.scalars().all()

        context += "## 5. Active Tasks\n"
        if not tasks:
            context += "(No tasks generated yet)\n"
        else:
            for t in tasks:
                status_icon = "[x]" if t.status == "DONE" else "[ ]"
                context += f"- {status_icon} **{t.title}** ({t.status}): {t.description}\n"

        return context

