Build a complete, polished, production-style hackathon prototype called CivicResolve AI for the problem statement:

PS02 — AI-Powered Citizen Complaint Understanding & Resolution Assistant

TAGLINE

“From Citizen Complaint to Government Action — Automatically.”

The application must feel like a serious government-tech AI platform, not a generic CRUD complaint website.

The core concept is an AI-powered multi-agent complaint resolution system that converts an unstructured citizen complaint into a structured, routed, prioritized and trackable government ticket.

---

1. CORE USER FLOW

Implement this complete workflow:

Citizen Complaint
→ AI Understanding
→ Category Classification
→ Entity & Location Detection
→ Urgency/Priority Detection
→ Missing Information Detection
→ Clarification Questions
→ Department Routing
→ Ticket Creation
→ Resolution Recommendation
→ SLA Monitoring
→ Escalation
→ Citizen Response
→ Resolution

The system must support all types of civic complaints, not only water-related complaints.

---

2. AI MULTI-AGENT SYSTEM

Create a visually impressive AI Command Center showing these agents as separate processing stages:

1. Complaint Understanding Agent
   
   - Understand natural-language complaint
   - Extract complaint intent
   - Identify important facts
   - Detect language

2. Entity & Location Agent
   
   - Extract locality
   - Ward
   - Landmark
   - Address
   - Duration
   - People/area affected

3. Priority & Urgency Agent
   
   - LOW
   - MEDIUM
   - HIGH
   - CRITICAL
   - Explain why the priority was selected

4. Missing Information Agent
   
   - Detect missing fields
   - Generate clarification questions
   - Example:
     “Please provide your area, locality, ward or nearest landmark.”

5. Department Routing Agent
   Automatically determine the responsible department.

6. Ticket Agent
   
   - Generate unique ticket ID
   - Create structured ticket
   - Record timestamp
   - Set SLA deadline

7. Resolution Recommendation Agent
   Generate recommended actions for the responsible department.

8. Citizen Response Agent
   Generate a professional citizen-facing response.

9. SLA Monitoring Agent
   
   - Monitor SLA
   - Show countdown
   - SAFE
   - APPROACHING SLA
   - BREACHED

10. Escalation Agent
    Automatically demonstrate escalation when SLA is breached.

Create a Coordinator/Orchestrator that visually connects these agents.

Each agent card should show:

- WAITING
- PROCESSING
- COMPLETED
- ACTION REQUIRED

with subtle animations.

---

3. IMPORTANT DEMO SCENARIO

The primary demo complaint is:

«“There has been no water supply in our area for three days and nobody is responding.”»

AI should produce:

Category: Water Supply
Duration: 3 days
Priority: HIGH
Department: Water Supply Department
Location: Missing
Missing Information: Location

Ask:

«“Please provide your area, locality, ward or nearest landmark.”»

Citizen enters:

«Shivaji Nagar»

Then create a ticket automatically.

Example ticket format:

CR-XXXX

Do NOT hardcode the same ticket ID. Generate it dynamically.

Show:

- Complaint
- Category
- Location
- Priority
- Department
- Status
- SLA
- Resolution recommendation
- Citizen response
- Timeline
- AI reasoning summary

---

4. MULTILINGUAL SUPPORT

Support:

- English
- Hindi
- Marathi

Example Marathi complaint:

«“आमच्या भागात तीन दिवसांपासून पाणी येत नाही.”»

The system should understand:

Water Supply → 3 days → Location missing → High Priority

Also include a language selector.

The UI should be capable of displaying generated responses in the selected language.

---

5. CIVIC CATEGORIES

The AI must classify complaints into broad civic categories:

- Water Supply
- Garbage Collection
- Roads & Potholes
- Streetlights
- Drainage & Sewage
- Electricity
- Public Transport
- Sanitation
- Public Health
- Parks & Environment
- Traffic & Parking
- Construction & Encroachment
- Stray Animals
- Noise Pollution
- Public Safety
- Other Civic Service

Do NOT restrict classification to keywords.

The interface should make it clear that the system performs intent-based complaint understanding.

For unknown complaints, classify as:

Other Civic Service

and generate clarification questions instead of failing.

---

6. CITIZEN PORTAL

Create a beautiful mobile-first citizen interface.

Landing page

Brand:

CivicResolve AI

Tagline:

From Citizen Complaint to Government Action — Automatically.

Buttons:

- Submit Complaint
- Track Complaint
- View Demo

Also show a visual workflow:

Complaint → AI → Department → Action → Resolution

---

Submit Complaint

Fields:

- Complaint description
- Language
- Location
- Landmark
- Optional image upload
- Optional contact information

Make the complaint box large and natural-language focused.

Button:

Analyze Complaint

Show an animated AI processing state.

---

7. AI ANALYSIS SCREEN

After analysis, show a professional result card:

AI Understanding

Category
Water Supply

Location
Shivaji Nagar

Duration
3 days

Priority
HIGH

Urgency
High

Responsible Department
Water Supply Department

Confidence
94%

Then show:

Missing Information

«Location information was required and has now been provided.»

Then show the AI agent execution timeline.

---

8. TICKET CREATION

After required information is available:

Create a ticket automatically.

Display a large ticket card:

CR-1042

Use a dynamically generated ID in the real application.

Show:

- Status: SUBMITTED
- Category
- Priority
- Department
- Location
- Created time
- SLA deadline

Add:

Track Complaint

button.

---

9. COMPLAINT TRACKING

Create a tracking page.

Citizen enters:

Ticket ID

Show a timeline:

Complaint Submitted
       ↓
AI Analyzed
       ↓
Department Routed
       ↓
Officer Assigned
       ↓
In Progress
       ↓
Resolution Recommended
       ↓
Resolved

Each step should have timestamp/status.

Show SLA status prominently.

---

10. OFFICER DASHBOARD

Create a separate professional Department Officer Dashboard.

Top KPI cards:

- Total Assigned
- Pending
- In Progress
- Resolved
- SLA Approaching
- SLA Breached

Complaint table columns:

- Ticket ID
- Category
- Location
- Priority
- Department
- Created
- SLA
- Status
- Assigned Officer

Add filters:

- Category
- Priority
- Department
- Status
- Location
- SLA state

Actions:

- View Complaint
- Accept
- Assign
- Change Status
- Add Resolution Note
- Mark Resolved
- Escalate
- View AI Analysis
- View Audit History

---

11. ADMIN DASHBOARD

Create a separate Admin Analytics dashboard.

KPI cards:

- Total Complaints
- Pending
- In Progress
- Resolved
- Escalated
- SLA Breaches
- Average Resolution Time
- SLA Compliance

Charts:

- Complaints by Category
- Complaints by Department
- Complaints by Priority
- Complaints by Status
- Complaints by Location
- Resolution Trend
- SLA Breaches

Clearly label demo analytics as:

Synthetic / Demo Data

Do not present synthetic statistics as real government data.

---

12. AI COMMAND CENTER

This is one of the most important judge-facing screens.

Create a dark/modern professional command center showing:

CITIZEN COMPLAINT
        ↓
UNDERSTANDING AGENT
        ↓
ENTITY & LOCATION AGENT
        ↓
PRIORITY AGENT
        ↓
MISSING INFO AGENT
        ↓
ROUTING AGENT
        ↓
TICKET AGENT
        ↓
RESOLUTION AGENT
        ↓
SLA AGENT
        ↓
ESCALATION AGENT

Each agent should have:

- Icon
- Name
- Status
- Processing animation
- Output
- Processing time

Example:

Priority Agent

Status: COMPLETED

Output:

«HIGH — essential public service unavailable for 3 days.»

This screen must visually communicate that this is an AI agent workflow, not a simple form submission.

---

13. SLA SYSTEM

Use configurable prototype SLAs.

Example:

CRITICAL → shortest SLA
HIGH → short SLA
MEDIUM → moderate SLA
LOW → longer SLA

Show:

SLA Countdown

and states:

- SAFE
- APPROACHING
- BREACHED

Include a prominent:

Simulate SLA Breach

button for hackathon demonstration.

When triggered:

1. SLA becomes BREACHED
2. Ticket status changes to ESCALATED
3. Escalation event appears
4. Supervisor notification appears
5. Audit event is created
6. Citizen notification is generated

Clearly label these as prototype/configurable SLA rules, not official government SLA policies.

---

14. DUPLICATE COMPLAINT DETECTION

When a citizen submits a complaint similar to an existing complaint, show:

Possible Related Complaint

«Water supply failure reported in Shivaji Nagar»

Similarity:

89%

Options:

- Link to Existing Complaint
- Create New Complaint

Implement this across categories rather than only water.

---

15. AUDIT TRAIL

Every important ticket action should appear in an audit timeline.

Example:

10:21 — Complaint submitted
10:21 — AI analysis completed
10:22 — Location detected
10:22 — Priority assigned: HIGH
10:22 — Routed to Water Supply Department
10:23 — Ticket created
10:23 — Officer assigned
10:45 — SLA approaching
11:00 — SLA breached
11:00 — Automatically escalated

---

16. DEMO MODE

Add a Hackathon Demo Mode.

Provide predefined scenarios:

Scenario 1

Water supply interruption

Scenario 2

Road pothole

Scenario 3

Garbage not collected

Scenario 4

Broken streetlight

Scenario 5

Drainage overflow

Scenario 6

Electricity outage

Scenario 7

Public safety complaint

Each scenario should automatically populate a realistic complaint.

The judge should be able to select a scenario and run the complete AI pipeline.

---

17. DESIGN REQUIREMENTS

Design should look like a real civic-tech product.

Use:

- React
- Tailwind CSS
- shadcn/ui
- Lucide icons
- Recharts
- Framer Motion where appropriate

Visual style:

- Clean
- Modern
- Professional
- Government-tech
- Trustworthy
- Accessible
- Responsive
- Mobile-first citizen experience

Avoid:

- Cartoon graphics
- Generic AI robot illustrations
- Excessive gradients
- Neon colors
- Overloaded screens
- Fake futuristic effects

Use strong typography, clean cards, tables, timelines, status badges and subtle animations.

---

18. TECHNICAL ARCHITECTURE

Build the frontend so it can communicate with a backend API.

Recommended backend:

FastAPI + Python

Database:

SQLite for local demo, structured so PostgreSQL can be used for deployment.

Create modular services for:

- Complaint analysis
- Classification
- Entity extraction
- Priority
- Department routing
- Missing information
- Ticket creation
- SLA
- Escalation
- Duplicate detection
- Audit logging

Use structured JSON responses.

The application must still work without an external AI API by using a deterministic/local fallback classifier.

If an LLM integration is included, make it optional through environment variables.

Never expose API keys in frontend code.

---

19. IMPORTANT AI IMPLEMENTATION RULE

Do not create a fake “AI” button that only changes the UI.

The prototype should have an actual processing pipeline.

For every complaint, create structured output such as:

{
  "category": "Water Supply",
  "location": "Shivaji Nagar",
  "duration": "3 days",
  "priority": "HIGH",
  "urgency": "HIGH",
  "department": "Water Supply Department",
  "missing_information": [],
  "clarification_questions": [],
  "resolution_recommendation": [],
  "language": "English",
  "confidence": 0.94
}

Use deterministic logic as a fallback and allow an LLM adapter for richer natural-language understanding.

---

20. HONEST HACKATHON PRESENTATION

Do not claim:

- Official government SLA values
- Real government database access
- Real government dispatch
- Real-world complaint statistics
- Production deployment
- Scientifically validated AI accuracy

Use labels such as:

Prototype

Configurable Rules

Synthetic Demo Data

AI-assisted Recommendation

This is a hackathon prototype demonstrating how the workflow could operate.

---

21. FINAL ACCEPTANCE TEST

Before considering the prototype complete, verify these scenarios:

Test A — Water

Input:

«There has been no water supply in our area for three days and nobody is responding.»

Expected:

Water Supply → HIGH → missing location → clarification → Shivaji Nagar → Water Supply Department → ticket → SLA.

Test B — Road

«There is a huge pothole near our college and several bikes have nearly fallen.»

Expected:

Roads & Potholes → HIGH/MEDIUM → Roads Department → resolution recommendation.

Test C — Garbage

«Garbage has not been collected from our street for five days and it is starting to smell.»

Expected:

Garbage Collection → HIGH → Sanitation/Waste Department.

Test D — Streetlight

«The streetlight outside our building has been broken for two weeks.»

Expected:

Streetlights → MEDIUM → Electrical/Streetlight Department.

Test E — Marathi

«आमच्या भागात तीन दिवसांपासून पाणी येत नाही.»

Expected:

Water Supply → 3 days → HIGH → missing location.

Test F — Unknown

Enter an unusual civic complaint.

Expected:

Other Civic Service → clarification questions.

Test G — SLA

Create a ticket → simulate breach.

Expected:

SLA BREACHED → automatic escalation → supervisor → audit trail → citizen response.

Test H — Duplicate

Submit a complaint similar to an existing ticket.

Expected:

Possible Related Complaint → similarity score → Link/Create New.

---

22. FINAL GOAL

The finished prototype should allow a judge to understand the complete concept within 2–3 minutes.

The key message must be visually obvious:

Citizen writes a complaint in natural language.

↓

AI understands what happened.

↓

AI identifies where it happened.

↓

AI determines urgency.

↓

AI identifies missing information.

↓

AI routes it to the correct department.

↓

AI creates and tracks the ticket.

↓

AI recommends resolution actions.

↓

AI monitors SLA.

↓

AI escalates automatically if necessary.

↓

Citizen receives a clear response.

Build the application as a fully interactive prototype, with realistic demo data and working frontend interactions. Do not leave major buttons as non-functional placeholders.
