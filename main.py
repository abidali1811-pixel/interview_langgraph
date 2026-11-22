import os
from typing import Optional, TypedDict

import streamlit as st
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph


class CandidateState(TypedDict):
    application: str
    experience_level: Optional[str]
    skill_match: Optional[str]
    response: Optional[str]


def get_openai_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets["OPENAI_API_KEY"]
        except (KeyError, FileNotFoundError):
            api_key = ""
    return api_key


@st.cache_resource
def build_candidate_screening_app(api_key: str):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, api_key=api_key)

    def categorize_experience(state: CandidateState) -> CandidateState:
        prompt = ChatPromptTemplate.from_template(
            "Categorize the candidate from this application as exactly one of "
            "'Entry-level', 'Mid-level', or 'Senior-level'. "
            "Return only the category.\n\nApplication: {application}"
        )
        category = (prompt | llm).invoke(
            {"application": state["application"]}
        ).content.strip()
        return {"experience_level": category}

    def assess_skillset(state: CandidateState) -> CandidateState:
        prompt = ChatPromptTemplate.from_template(
            "For a Python Developer position, assess this application. "
            "Return exactly 'Match' if the candidate has Python skills, "
            "otherwise return exactly 'No Match'. "
            "Return only one of those two values.\n\n"
            "Application: {application}"
        )
        assessment = (prompt | llm).invoke(
            {"application": state["application"]}
        ).content.strip()
        return {"skill_match": assessment}

    def schedule_hr_interview(state: CandidateState) -> CandidateState:
        return {"response": "Candidate has been shortlisted for an HR interview."}

    def escalate_to_recruiter(state: CandidateState) -> CandidateState:
        return {
            "response": "Candidate has senior-level experience but does not match the job skills."
        }

    def reject_application(state: CandidateState) -> CandidateState:
        return {"response": "Candidate does not meet the job description and has been rejected."}

    def route_application(state: CandidateState) -> str:
        skill_match = state.get("skill_match", "").lower()
        experience_level = state.get("experience_level", "").lower()

        if "match" in skill_match and "no match" not in skill_match:
            return "schedule_hr_interview"
        if "senior" in experience_level:
            return "escalate_to_recruiter"
        return "reject_application"

    workflow = StateGraph(CandidateState)
    workflow.add_node("categorize_experience", categorize_experience)
    workflow.add_node("assess_skillset", assess_skillset)
    workflow.add_node("schedule_hr_interview", schedule_hr_interview)
    workflow.add_node("escalate_to_recruiter", escalate_to_recruiter)
    workflow.add_node("reject_application", reject_application)

    workflow.add_edge(START, "categorize_experience")
    workflow.add_edge("categorize_experience", "assess_skillset")
    workflow.add_conditional_edges(
        "assess_skillset",
        route_application,
        {
            "schedule_hr_interview": "schedule_hr_interview",
            "escalate_to_recruiter": "escalate_to_recruiter",
            "reject_application": "reject_application",
        },
    )
    workflow.add_edge("schedule_hr_interview", END)
    workflow.add_edge("escalate_to_recruiter", END)
    workflow.add_edge("reject_application", END)

    return workflow.compile()


st.set_page_config(page_title="HR Resume Screening", page_icon="HR", layout="wide")
st.title("HR Resume Screening Chatbot")
st.write(
    "Paste a candidate application to categorize experience, assess Python skills, "
    "and determine the screening outcome."
)

api_key = get_openai_api_key()
if not api_key:
    st.warning(
        "Set OPENAI_API_KEY in the environment or in Streamlit secrets "
        "before running a screening."
    )

application = st.text_area(
    "Candidate application",
    height=220,
    placeholder="I have 5 years of Python development experience...",
)

if st.button("Screen Candidate", type="primary", use_container_width=True):
    if not application.strip():
        st.error("Enter a candidate application.")
    elif not api_key:
        st.error("OPENAI_API_KEY is missing.")
    else:
        with st.spinner("Running the candidate screening workflow..."):
            try:
                app = build_candidate_screening_app(api_key)
                result = app.invoke({"application": application.strip()})
            except Exception as exc:
                st.error(f"Screening failed: {exc}")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Experience Level")
                    st.info(result["experience_level"])
                with col2:
                    st.subheader("Skill Match")
                    st.info(result["skill_match"])

                st.subheader("Decision")
                if "shortlisted" in result["response"].lower():
                    st.success(result["response"])
                elif "rejected" in result["response"].lower():
                    st.error(result["response"])
                else:
                    st.warning(result["response"])
