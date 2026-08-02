# Action items

Extracted from routed transcripts by the MRF transcription pipeline. This is
the repo's local task inbox until Michael centralizes. Triage and check off.

## 2026-07-10 — Two colleagues - Kubernetes security workshop with BurritoBot scenario (auto).speaker.txt
<!-- source: Two colleagues - Kubernetes security workshop with BurritoBot scenario (auto).speaker.txt -->
- [ ] Add warning that custom code config setup is for experienced users only
- [ ] Show live example of data exfiltration to S3 bucket during challenge
- [ ] Demonstrate Kubernetes network policy activation to block data exfiltration
- [ ] Demonstrate image source restriction (Harbor/GCR) to block malicious images
- [ ] Demonstrate Falco enablement to block LS calls and detect suspicious activity
- [ ] Create in-browser Burrito Bot, VTT, and debug interface with three tabs
- [ ] Prepare challenges five, six, and seven with LLM output restriction problem statement

## 2026-07-10 — Whitney Lee and Michael Forrester - Watch It Burn workshop rounds and guardrail challenges (corrected).speaker.txt
<!-- source: Whitney Lee and Michael Forrester - Watch It Burn workshop rounds and guardrail challenges (corrected).speaker.txt -->
- [ ] Run through all seven challenges together and time the session to determine if reordering is needed
- [ ] Create a planted Easter egg file (with silly path names and "DO NOT OPEN" directory names) inside a container for challenge three
- [ ] Set up Falco rules to detect and alert on suspicious file system activity like LS commands and directory traversal
- [ ] Configure External Secrets Operator (ESO) to manage secrets so they're not visible as Kubernetes secrets in the lab environment

## 2026-07-10 — 2026-06-24 - Whitney Lee and Michael Forrester - Watch It Burn run of show (corrected).speaker.txt
<!-- source: 2026-06-24 - Whitney Lee and Michael Forrester - Watch It Burn run of show (corrected).speaker.txt -->
- [ ] Add Speaker 2 to the mosquito walk
- [ ] Add Speaker 1 to Speaker 2's account
- [ ] Capture/record the attacks from round one to show if they get caught in round two
- [ ] Create a prompt interface separate from the cluster with dropdown to switch between round versions
- [ ] Make prompts clickable to inject into user prompts like a library
- [ ] Provide users a generic prompt version without system prompts at a URL they can access
- [ ] Surface the prompt that caused cluster failure in round three
- [ ] Decide whether to show prompts on front room screen and sanitize if streaming
- [ ] Determine if round one, two, and three challenges stay in same cluster or jump between clusters
- [ ] Clarify what data security vulnerability to demo in round two (data at rest vs. in transit)

## 2026-07-10 — Agentic guardrails demo repo build - agents, observability, attack detection.speaker.txt
<!-- source: Agentic guardrails demo repo build - agents, observability, attack detection.speaker.txt -->
- [ ] Share spec file and technology overview document with Speaker 3
- [ ] Schedule 30-minute session with Speaker 3 for initial project shaping
- [ ] Review the yacht track document to determine finish line and technology choices for demo
- [ ] Create demo showing one basic CNCF attack being stopped
- [ ] Create demo showing one to four advanced attacks (pump injection, etc.) being stopped
- [ ] Pre-install and turn off security tools before demo, then enable during presentation
- [ ] Build agent designed to break out of security constraints for security showcase
- [ ] Build agent that monitors logs and progressively adds guardrail rules based on observability patterns
- [ ] Sit down with spec and agent documents to review side-by-side before Speaker 1 returns to Atlanta
- [ ] Create three demo showcases: standard CNCF guardrails, security enforcement, and observability enforcement

## 2026-07-11 — My recording 25.mp3
<!-- source: My recording 25.mp3 -->
- [ ] Enable live observability views (Datadog interface, S3 bucket monitoring, process viewing)
- [ ] Add hints to challenges about burrito ordering tied to objectives
- [ ] Show working example prompt for data exfiltration attack
- [ ] Activate Kubernetes network policy in round two
- [ ] Enable image source restrictions (Harbor/GACR) in round two
- [ ] Enable Falco runtime detection in round two
- [ ] Provide in-browser BurritoBot, VTT, and data box terminals
- [ ] Add warning label for optional custom code config as "experienced users only"
- [ ] Create challenges five, six, and seven focused on LLM output guardrails
- [ ] Store secret recipe as Kubernetes secret for challenge demonstrations

## 2026-07-11 — My recording 26.mp3
<!-- source: My recording 26.mp3 -->
- [ ] Redo challenge one with a different approach that tests network policy blocking without requiring S3 bucket complexity
- [ ] Change challenge one from S3 exfiltration to a simpler egress test using an uptime monitor health beacon curl command
- [ ] Create a collector URL for the health beacon challenge to make it a legitimate rollout
- [ ] Provide explicit curl commands to attendees for challenges rather than expecting the model to generate them
- [ ] Add a note to challenge four warning that the fork bomb will not work because the model refuses to execute it
- [ ] Update the provisioning page to show only the student view, not admin/instructor views
- [ ] Fix the Datadog button on the provisioning page to link to the correct agent observability trace page
- [ ] Ensure the feedback form is accessible from the provisioning page
- [ ] Create a simple feedback form with Goldilocks-scale questions: pacing (too fast/slow/just right), difficulty level, and friend recommendation

