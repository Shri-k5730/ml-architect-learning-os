from __future__ import annotations

"""Deterministic Agentic AI curriculum for MLOS V4.

These lessons are deliberately authored in code and take precedence over older
Supabase agentic designs. The subject is agentic AI. The learning system itself
does not need agentic orchestration to teach or grade these normal lessons.
"""

from copy import deepcopy
from typing import Any, Dict, Optional

VERSION = "mlos_v4_deterministic_agentic_2026_08_17"

AGENTIC_AI_DESIGNS: Dict[str, Dict[str, Any]] = {'aia_001': {'design_version': 'mlos_v4_deterministic_agentic_2026_08_17',
             'assessment_mode': 'v4_deterministic_mcq_plus_published_rubric',
             'topic_id': 'aia_001',
             'title': 'Agentic AI outer layer: what agents actually do',
             'learning_objective': 'Explain an agent as an LLM-centered control loop that uses state and tools to pursue a bounded goal, '
                                   'rather than as a chatbot with a longer prompt.',
             'prerequisite_bridge': 'Start from the agentic system behavior. Peel down only when a deeper mechanism explains a design '
                                    'decision or failure.',
             'concept_steps': [{'heading': '1. Agent versus chatbot',
                                'body': 'A chatbot mainly produces a response. An agent is given a goal, can inspect state, choose from '
                                        'allowed actions or tools, observe results, and decide what to do next until it succeeds, stops, '
                                        'or escalates.'},
                               {'heading': '2. Runtime around the model',
                                'body': 'The LLM proposes decisions, but the application runtime owns tool registration, credentials, '
                                        'state, retries, limits, logging and approvals. The model does not directly possess enterprise '
                                        'permissions.'},
                               {'heading': '3. Bounded autonomy',
                                'body': 'Useful autonomy is constrained. The architect defines which actions are allowed, what evidence is '
                                        'required, when a human must approve, and when the workflow must stop.'},
                               {'heading': '4. Failure mode',
                                'body': 'A fluent model can still choose a wrong tool, act on stale context, repeat actions, or continue '
                                        'after uncertainty. Agent quality therefore depends on the full trajectory, not only the final '
                                        'text.'},
                               {'heading': '5. Architect translation',
                                'body': 'Treat the agent as a controlled software system: goal, state, tools, policy, evidence, '
                                        'observability, approval and recovery.'}],
             'concept_map': [],
             'worked_example': {'scenario': 'An IT service agent investigates a failed deployment, reads logs, checks the deployment '
                                            'record, proposes a rollback, and waits for an authorised engineer before executing the '
                                            'rollback.',
                                'takeaway': 'The model proposes actions, but the runtime constrains tools, permissions and approval.'},
             'worked_examples': [{'title': 'Architect readout',
                                  'body': 'An IT service agent investigates a failed deployment, reads logs, checks the deployment record, '
                                          'proposes a rollback, and waits for an authorised engineer before executing the rollback. The '
                                          "design point is: Define the agent's goal boundary, allowed tools, state, approval policy, stop "
                                          'conditions, trace logging and recovery path.'}],
             'code_bridge': {},
             'misconception': 'Calling any LLM application an agent merely because it has a system prompt or produces multiple messages.',
             'architect_extension': "Define the agent's goal boundary, allowed tools, state, approval policy, stop conditions, trace "
                                    'logging and recovery path.',
             'diagnostic_drill': {'question': 'A support bot can answer questions but cannot call tools or update state. Is it necessarily '
                                              'an agent?',
                                  'reveal': 'No. Agentic behavior requires a bounded action loop around the model, not just fluent '
                                            'generation.'},
             'knowledge_checks': [{'kind': 'Critical',
                                   'question': 'A claims agent can read policy data, inspect a claim record, request evidence and propose '
                                               'an action. Which property makes it agentic rather than merely conversational?',
                                   'options': ['It can choose bounded actions from an allowed tool set and react to the observed results.',
                                               'It can produce a detailed explanation of the policy and keep the conversation natural.',
                                               'It can use a large context window so all claim documents fit in one model request.',
                                               'It can generate a plan in text even when the application never executes any action.'],
                                   'answer_index': 0,
                                   'explanation': 'Agentic behavior comes from a controlled action-observation loop, not from verbosity or '
                                                  'context size.',
                                   'is_critical': True,
                                   'id': 'mcq_01'},
                                  {'kind': 'Critical',
                                   'question': 'Which component should hold the actual credential used to call an enterprise API?',
                                   'options': ["The application or tool runtime that enforces the agent's permissions.",
                                               'The model context so the LLM can decide when to reveal the credential.',
                                               'The conversation memory so the credential remains available across sessions.',
                                               'The user prompt so the credential is visible whenever a tool is requested.'],
                                   'answer_index': 0,
                                   'explanation': 'Credentials belong in the controlled runtime, not in model-visible text.',
                                   'is_critical': True,
                                   'id': 'mcq_02'},
                                  {'kind': 'Critical',
                                   'question': 'A production agent keeps trying different tools after the evidence becomes uncertain. What '
                                               'is the most direct architecture control?',
                                   'options': ['Define uncertainty and step limits that force the workflow to stop or escalate.',
                                               'Increase the model temperature so the agent can search a wider action space.',
                                               'Add more tools so the agent has additional ways to continue the investigation.',
                                               'Keep the same loop but ask the model to be more careful in the system prompt.'],
                                   'answer_index': 0,
                                   'explanation': 'Bounded stop and escalation conditions control runaway trajectories.',
                                   'is_critical': True,
                                   'id': 'mcq_03'},
                                  {'kind': 'Scenario',
                                   'question': 'A procurement agent proposes a supplier change that could affect a live contract. What is '
                                               'the best division of responsibility?',
                                   'options': ['The agent prepares evidence and a recommendation; an authorised owner approves the '
                                               'irreversible action.',
                                               'The agent executes automatically because it has already compared the supplier data.',
                                               'The agent asks the user whether it feels confident, then executes if confidence is high.',
                                               'The agent writes the recommendation to memory and lets the next session decide what '
                                               'happened.'],
                                   'answer_index': 0,
                                   'explanation': 'High-impact actions should have explicit human or policy approval.',
                                   'is_critical': False,
                                   'id': 'mcq_04'},
                                  {'kind': 'Scenario',
                                   'question': 'Which observation is strongest evidence that an agent completed a task correctly?',
                                   'options': ['The target system changed to the expected state and the change can be verified from '
                                               'authoritative data.',
                                               'The final answer sounds confident and contains all of the requested business terminology.',
                                               'The model produced a chain of intermediate thoughts that appears logically consistent.',
                                               'The agent used several tools, which demonstrates that it performed a sufficiently complex '
                                               'workflow.'],
                                   'answer_index': 0,
                                   'explanation': 'Task success should be verified against system state, not style or tool count.',
                                   'is_critical': False,
                                   'id': 'mcq_05'},
                                  {'kind': 'Architecture',
                                   'question': 'Why is trajectory logging useful for an agent?',
                                   'options': ['It reconstructs the state, tool calls, results and decisions that led to an outcome.',
                                               'It guarantees that the model will make the same decision on every future request.',
                                               'It removes the need to define permissions because all actions can be inspected later.',
                                               'It converts probabilistic model outputs into deterministic business outcomes '
                                               'automatically.'],
                                   'answer_index': 0,
                                   'explanation': 'Logs make behavior observable but do not replace controls.',
                                   'is_critical': False,
                                   'id': 'mcq_06'},
                                  {'kind': 'Scenario',
                                   'question': 'A customer-service agent has access to both `lookup_order` and `issue_refund`. Which '
                                               'configuration is safest for ordinary status queries?',
                                   'options': ['Allow order lookup automatically and require an approval gate before the refund tool can '
                                               'execute.',
                                               'Expose both tools equally because the model can infer which one is appropriate from the '
                                               'request.',
                                               'Hide both tools and ask the model to simulate their results from its general knowledge.',
                                               'Allow the refund tool first so the agent can resolve cases quickly and audit the decision '
                                               'later.'],
                                   'answer_index': 0,
                                   'explanation': 'Tool access should reflect action risk.',
                                   'is_critical': False,
                                   'id': 'mcq_07'},
                                  {'kind': 'Trap',
                                   'question': 'Which statement about an LLM-based agent is most accurate?',
                                   'options': ['The model proposes decisions inside a larger runtime that owns state, tools, permissions '
                                               'and recovery.',
                                               "The model itself owns every tool credential because tool use is part of the model's "
                                               'reasoning process.',
                                               'The model is an autonomous employee once a goal is present, so external workflow logic is '
                                               'optional.',
                                               'The model becomes deterministic when a planner is added, so operational controls can be '
                                               'simplified.'],
                                   'answer_index': 0,
                                   'explanation': 'The runtime, not the model alone, is the system.',
                                   'is_critical': False,
                                   'id': 'mcq_08'},
                                  {'kind': 'Scenario',
                                   'question': 'An agent gives the correct final answer after first making an unauthorised tool call that '
                                               'was later reversed. How should the run be judged?',
                                   'options': ['The trajectory still failed a safety requirement even though the final text was correct.',
                                               'The run should pass because only the final answer determines whether the user was helped.',
                                               'The run should pass if the unauthorised action was inexpensive and produced no visible '
                                               'error.',
                                               'The run should be scored only on latency because the final business state was eventually '
                                               'restored.'],
                                   'answer_index': 0,
                                   'explanation': 'Agent evaluation must include trajectory safety.',
                                   'is_critical': False,
                                   'id': 'mcq_09'},
                                  {'kind': 'Architecture',
                                   'question': "What should be specified before calling an enterprise workflow 'autonomous'?",
                                   'options': ['Allowed actions, required evidence, approval boundaries, stop conditions and recovery '
                                               'behavior.',
                                               'Model size, prompt length, response style, context-window size and vendor name.',
                                               'Number of tools, number of agents, number of prompts and average token consumption.',
                                               'Only the business goal, because the agent should discover the operating boundaries '
                                               'dynamically.'],
                                   'answer_index': 0,
                                   'explanation': 'Autonomy is a policy boundary, not a marketing label.',
                                   'is_critical': False,
                                   'id': 'mcq_10'}],
             'evidence_tasks': [{'question_id': 'q1',
                                 'type': 'architect_decision',
                                 'label': 'Short architect response',
                                 'purpose': 'Demonstrate the mechanism in one concrete scenario, then name one specific risk and one '
                                            'implementable control.',
                                 'question': 'In 80-140 words, explain Agentic AI outer layer: what agents actually do using one business '
                                             'or engineering example. Include the mechanism, one risk and one control.',
                                 'expected_focus': ['mechanism', 'example', 'risk', 'control'],
                                 'response_shape': 'Mechanism → concrete example → specific risk → implementable control.',
                                 'target_min_words': 80,
                                 'target_max_words': 140,
                                 'sample_answer': 'A customer-support agent differs from a chatbot because it does more than generate a '
                                                  'reply. The runtime gives it a bounded goal, state and approved tools, then lets it '
                                                  'choose an action, observe the result and decide what to do next. For example, an '
                                                  'order-support agent may verify a customer, retrieve an order and return its status. A '
                                                  'specific risk is an unauthorised refund or repeated tool calls. I would restrict the '
                                                  'agent to allow-listed tools and least-privilege permissions, require approval for '
                                                  'high-impact actions, and enforce stop or escalation conditions when evidence is '
                                                  'missing.'}],
             'written_rubric': {'required': [{'id': 'mechanism',
                                              'label': 'Agent mechanism',
                                              'description': 'Explains a goal-driven loop or bounded action system.',
                                              'phrases_any': ['goal', 'tool', 'observe', 'state', 'action', 'loop', 'runtime'],
                                              'token_groups_all': [['goal', 'action'], ['tool', 'result']]},
                                             {'id': 'example',
                                              'label': 'Concrete example',
                                              'description': 'Uses a business or engineering agent example.',
                                              'phrases_any': ['for example',
                                                              'scenario',
                                                              'agent',
                                                              'claim',
                                                              'order',
                                                              'support',
                                                              'procurement',
                                                              'service',
                                                              'deployment'],
                                              'token_groups_all': []},
                                             {'id': 'risk',
                                              'label': 'Specific risk',
                                              'description': 'Names a failure or unsafe action.',
                                              'phrases_any': ['unauthor',
                                                              'wrong tool',
                                                              'stale',
                                                              'repeat',
                                                              'runaway',
                                                              'unsafe',
                                                              'delete',
                                                              'refund',
                                                              'disclos',
                                                              'hallucinat',
                                                              'failure'],
                                              'token_groups_all': []},
                                             {'id': 'control',
                                              'label': 'Operating control',
                                              'description': 'Names an implementable control.',
                                              'phrases_any': ['allow-list',
                                                              'allowlist',
                                                              'read-only',
                                                              'approval',
                                                              'permission',
                                                              'stop',
                                                              'limit',
                                                              'escalat',
                                                              'guardrail',
                                                              'human',
                                                              'audit'],
                                              'token_groups_all': []}],
                                'bonus': [{'id': 'runtime_boundary',
                                           'label': 'Runtime boundary',
                                           'description': 'Distinguishes model reasoning from runtime/tool enforcement.',
                                           'phrases_any': ['runtime', 'credential', 'application', 'tool registry', 'permissions'],
                                           'token_groups_all': []},
                                          {'id': 'recovery',
                                           'label': 'Recovery',
                                           'description': 'Names rollback, retry policy or recovery.',
                                           'phrases_any': ['rollback', 'recover', 'retry', 'kill switch'],
                                           'token_groups_all': []}]},
             'sample_answer': 'A customer-support agent differs from a chatbot because it does more than generate a reply. The runtime '
                              'gives it a bounded goal, state and approved tools, then lets it choose an action, observe the result and '
                              'decide what to do next. For example, an order-support agent may verify a customer, retrieve an order and '
                              'return its status. A specific risk is an unauthorised refund or repeated tool calls. I would restrict the '
                              'agent to allow-listed tools and least-privilege permissions, require approval for high-impact actions, and '
                              'enforce stop or escalation conditions when evidence is missing.',
             'mastery_repair_prompts': ['Can I state the mechanism without hiding behind generic AI vocabulary?',
                                        'Can I name a concrete failure that could happen in this exact scenario?',
                                        'Can I name an implementable control and what it blocks, limits or escalates?',
                                        'Can I state the stop, fallback or escalation behavior when evidence is insufficient?'],
             'is_gate': False,
             'assessment_principle': 'Normal lesson scoring is deterministic. MCQs use stable answer IDs and a published pass rule. The '
                                     'written response is scored only against the published mechanism, example, risk and control rubric. '
                                     'No hidden architecture vocabulary, essay-length preference or generic governance template may change '
                                     'the result.',
             'answer_quality_bar': {'three_star': 'Mechanism + concrete example + one specific risk + one implementable control.',
                                    'four_star': 'Adds evidence, tool boundary, stop condition or escalation behavior that is relevant to '
                                                 'the scenario.',
                                    'five_star': 'Adds multiple relevant operating details without adding unrelated architecture '
                                                 'vocabulary.'}},
 'aia_002': {'design_version': 'mlos_v4_deterministic_agentic_2026_08_17',
             'assessment_mode': 'v4_deterministic_mcq_plus_published_rubric',
             'topic_id': 'aia_002',
             'title': 'Agent loop: goal, plan, tool, observe',
             'learning_objective': 'Explain the agent loop as goal → plan → tool/action → observation → state update → next decision, with '
                                   'explicit completion and escalation conditions.',
             'prerequisite_bridge': 'Start from the agentic system behavior. Peel down only when a deeper mechanism explains a design '
                                    'decision or failure.',
             'concept_steps': [{'heading': '1. Goal',
                                'body': "The loop begins with a bounded goal and success condition. 'Help the customer' is vague; 'return "
                                        "the authorised order status for the supplied order ID' is testable."},
                               {'heading': '2. Plan and action',
                                'body': 'The agent chooses the next step and an allowed tool. The runtime validates the tool and arguments '
                                        'before execution.'},
                               {'heading': '3. Observe and update',
                                'body': 'The tool result becomes an observation. The agent updates task state and decides whether the '
                                        'evidence is sufficient, another step is needed, or the workflow should stop.'},
                               {'heading': '4. Stop and escalate',
                                'body': 'The loop needs maximum-step limits, completion criteria, error handling and escalation rules. '
                                        'Otherwise it can repeat calls, create duplicate actions or continue on weak evidence.'},
                               {'heading': '5. Architect translation',
                                'body': 'Design the loop as an observable state machine around a probabilistic model, not as an unbounded '
                                        'prompt conversation.'}],
             'concept_map': [],
             'worked_example': {'scenario': 'A procurement agent checks an order: validate the user and order ID, call `get_order`, '
                                            'observe the returned status, verify authorisation, then answer or escalate if the record is '
                                            'ambiguous.',
                                'takeaway': 'Every observation changes the next decision, and explicit stop conditions prevent unnecessary '
                                            'or unsafe actions.'},
             'worked_examples': [{'title': 'Architect readout',
                                  'body': 'A procurement agent checks an order: validate the user and order ID, call `get_order`, observe '
                                          'the returned status, verify authorisation, then answer or escalate if the record is ambiguous. '
                                          'The design point is: Persist task state, validate tool calls, define completion evidence, cap '
                                          'iterations, make side-effecting actions idempotent, and provide an escalation path.'}],
             'code_bridge': {},
             'misconception': "Treating 'goal, plan, tool, observe' as a one-way checklist instead of a loop where observations alter the "
                              'next decision.',
             'architect_extension': 'Persist task state, validate tool calls, define completion evidence, cap iterations, make '
                                    'side-effecting actions idempotent, and provide an escalation path.',
             'diagnostic_drill': {'question': 'The search API returns no matching order. What should the loop do?',
                                  'reveal': 'Update state with the failed observation and choose a bounded next action such as '
                                            'clarification, alternate lookup or escalation, rather than inventing an answer.'},
             'knowledge_checks': [{'kind': 'Critical',
                                   'question': "An order-status agent calls `get_order` and receives 'order ID not found'. What should "
                                               'happen next?',
                                   'options': ['Record the observation and choose a bounded next step such as clarification or an approved '
                                               'alternate lookup.',
                                               'Repeat the same call until the API eventually returns a record for the requested order.',
                                               'Assume the order is delayed and answer from the most common historical status pattern.',
                                               'Move directly to a write tool so the missing order can be recreated in the source system.'],
                                   'answer_index': 0,
                                   'explanation': 'Observations must drive the next bounded decision.',
                                   'is_critical': True,
                                   'id': 'mcq_01'},
                                  {'kind': 'Critical',
                                   'question': 'Which goal is best specified for an agent loop?',
                                   'options': ['Return the current status of an authorised order or stop if identity, order ID or evidence '
                                               'cannot be verified.',
                                               'Help procurement users efficiently while being accurate, helpful and professional in every '
                                               'situation.',
                                               "Use the available tools to solve as much of the user's problem as the model considers "
                                               'appropriate.',
                                               'Answer all order questions and keep trying until the user indicates that the conversation '
                                               'is satisfactory.'],
                                   'answer_index': 0,
                                   'explanation': 'A bounded goal includes success and stop conditions.',
                                   'is_critical': True,
                                   'id': 'mcq_02'},
                                  {'kind': 'Critical',
                                   'question': 'Why should a side-effecting tool such as `create_order` use an idempotency key?',
                                   'options': ['So a retry does not create a duplicate order when the previous result is uncertain.',
                                               'So the model can call the tool more frequently without having to validate its parameters.',
                                               'So the agent can bypass human approval after it has successfully created one similar '
                                               'order.',
                                               'So the tool result remains in the model context even after the application session '
                                               'expires.'],
                                   'answer_index': 0,
                                   'explanation': 'Idempotency controls duplicate side effects during retries.',
                                   'is_critical': True,
                                   'id': 'mcq_03'},
                                  {'kind': 'Scenario',
                                   'question': 'A tool call times out after the external system may already have processed it. What is the '
                                               'safest next step?',
                                   'options': ['Check authoritative state or use an idempotent retry before issuing another side-effecting '
                                               'request.',
                                               'Immediately retry the same write request because a timeout means the first call definitely '
                                               'failed.',
                                               'Ask the LLM whether the action probably succeeded and continue based on its confidence.',
                                               'Ignore the timeout and mark the task successful if the planned sequence has no remaining '
                                               'steps.'],
                                   'answer_index': 0,
                                   'explanation': 'Uncertain side effects require state verification.',
                                   'is_critical': False,
                                   'id': 'mcq_04'},
                                  {'kind': 'Architecture',
                                   'question': 'What should an observation contain for reliable next-step reasoning?',
                                   'options': ['The relevant tool result, error or state evidence needed to decide what action is valid '
                                               'next.',
                                               "The model's private reasoning text because that is the most complete representation of "
                                               'system state.',
                                               'A summary of the original prompt only, since tool results can be reconstructed from the '
                                               'plan.',
                                               'The final user-facing response so the next step can optimize communication rather than '
                                               'system state.'],
                                   'answer_index': 0,
                                   'explanation': 'Observations are evidence from tools/environment.',
                                   'is_critical': False,
                                   'id': 'mcq_05'},
                                  {'kind': 'Trap',
                                   'question': 'Which design most directly prevents an infinite agent loop?',
                                   'options': ['A maximum-step budget combined with explicit completion, failure and escalation '
                                               'conditions.',
                                               'A larger context window combined with a prompt reminding the model not to repeat itself.',
                                               'A higher token budget combined with additional tools that give the model more '
                                               'alternatives.',
                                               'A second LLM that rewrites the plan after every action but has no separate termination '
                                               'policy.'],
                                   'answer_index': 0,
                                   'explanation': 'Termination must be enforced by the workflow.',
                                   'is_critical': False,
                                   'id': 'mcq_06'},
                                  {'kind': 'Scenario',
                                   'question': 'An agent has enough evidence to answer the order status, but its original plan contains '
                                               'two unused diagnostic steps. What should it do?',
                                   'options': ['Stop because the success condition is satisfied; a plan is guidance, not a requirement to '
                                               'execute unnecessary steps.',
                                               'Execute all planned steps because changing the plan would make the trajectory '
                                               'inconsistent.',
                                               'Create a new plan with additional verification steps so the answer has more supporting '
                                               'evidence.',
                                               'Continue until the maximum-step budget is exhausted so the system gets full value from the '
                                               'tool allowance.'],
                                   'answer_index': 0,
                                   'explanation': 'Completion evidence should stop the loop.',
                                   'is_critical': False,
                                   'id': 'mcq_07'},
                                  {'kind': 'Architecture',
                                   'question': 'Which state is most important to persist between loop iterations?',
                                   'options': ['Goal, completed steps, authoritative observations, pending actions and approval status.',
                                               'Only the latest model message because previous tool outcomes can be regenerated if '
                                               'required.',
                                               'Only the initial user prompt because the plan should remain fixed throughout the entire '
                                               'run.',
                                               "All hidden reasoning tokens because state consistency depends on reproducing the model's "
                                               'thoughts.'],
                                   'answer_index': 0,
                                   'explanation': 'Task state should be explicit and observable.',
                                   'is_critical': False,
                                   'id': 'mcq_08'},
                                  {'kind': 'Scenario',
                                   'question': 'A human rejects a proposed refund during the loop. What should the agent do?',
                                   'options': ['Record the rejection, stop the refund path and follow the defined alternate or escalation '
                                               'behavior.',
                                               'Resubmit the approval with a stronger explanation until the human accepts the '
                                               'recommendation.',
                                               'Switch to a different write tool that achieves the same outcome without needing the '
                                               'rejected approval.',
                                               'Remove the rejection from working memory so the model can reconsider the request '
                                               'independently.'],
                                   'answer_index': 0,
                                   'explanation': 'Approval outcomes are binding workflow state.',
                                   'is_critical': False,
                                   'id': 'mcq_09'},
                                  {'kind': 'Architecture',
                                   'question': 'Which metric best reveals a loop that is technically completing but behaving '
                                               'inefficiently?',
                                   'options': ['Steps and tool calls per successful task, segmented by retry and failure reason.',
                                               'Average response length, because longer answers imply unnecessary loop iterations.',
                                               'Number of tools registered in the system, because larger tool sets create more execution '
                                               'cost.',
                                               'Prompt size, because token count alone determines how many actions the agent will '
                                               'perform.'],
                                   'answer_index': 0,
                                   'explanation': 'Trajectory metrics expose loop inefficiency.',
                                   'is_critical': False,
                                   'id': 'mcq_10'}],
             'evidence_tasks': [{'question_id': 'q1',
                                 'type': 'architect_decision',
                                 'label': 'Short architect response',
                                 'purpose': 'Demonstrate the mechanism in one concrete scenario, then name one specific risk and one '
                                            'implementable control.',
                                 'question': 'In 80-140 words, explain Agent loop: goal, plan, tool, observe using one business or '
                                             'engineering example. Include the mechanism, one risk and one control.',
                                 'expected_focus': ['mechanism', 'example', 'risk', 'control'],
                                 'response_shape': 'Mechanism → concrete example → specific risk → implementable control.',
                                 'target_min_words': 80,
                                 'target_max_words': 140,
                                 'sample_answer': 'An agent loop repeatedly turns a goal into controlled actions: define the goal, choose '
                                                  'the next step, call an approved tool, observe the result, update state, and decide '
                                                  'whether to continue, stop or escalate. For example, an order-status agent verifies the '
                                                  'requester, calls a read-only order API, checks the returned record and then responds. A '
                                                  'risk is looping on the same tool or acting on uncertain evidence. I would use a '
                                                  'maximum-step limit, validate each tool result, and require the loop to stop or escalate '
                                                  'when the success condition is met or evidence remains insufficient.'}],
             'written_rubric': {'required': [{'id': 'mechanism',
                                              'label': 'Loop mechanism',
                                              'description': 'Explains goal, action/tool, observation and next decision.',
                                              'phrases_any': ['goal',
                                                              'plan',
                                                              'tool',
                                                              'observe',
                                                              'observation',
                                                              'next action',
                                                              'state',
                                                              'decide'],
                                              'token_groups_all': [['tool', 'result'], ['observe', 'decide']]},
                                             {'id': 'example',
                                              'label': 'Concrete example',
                                              'description': 'Provides a business or engineering loop example.',
                                              'phrases_any': ['for example',
                                                              'scenario',
                                                              'order',
                                                              'procurement',
                                                              'support',
                                                              'claim',
                                                              'deployment',
                                                              'agent'],
                                              'token_groups_all': []},
                                             {'id': 'risk',
                                              'label': 'Specific risk',
                                              'description': 'Names a loop failure.',
                                              'phrases_any': ['repeat',
                                                              'infinite',
                                                              'duplicate',
                                                              'wrong',
                                                              'unauthor',
                                                              'timeout',
                                                              'stale',
                                                              'hallucinat',
                                                              'uncertain'],
                                              'token_groups_all': []},
                                             {'id': 'control',
                                              'label': 'Operating control',
                                              'description': 'Names a concrete loop control.',
                                              'phrases_any': ['stop',
                                                              'max',
                                                              'limit',
                                                              'idempot',
                                                              'approval',
                                                              'read-only',
                                                              'escalat',
                                                              'validate',
                                                              'guardrail'],
                                              'token_groups_all': []}],
                                'bonus': [{'id': 'state_update',
                                           'label': 'State update',
                                           'description': 'Explains that observations update state or next action.',
                                           'phrases_any': ['update state', 'state update', 'observation', 'next decision'],
                                           'token_groups_all': []},
                                          {'id': 'failure_path',
                                           'label': 'Failure path',
                                           'description': 'Names retry, fallback or escalation behavior.',
                                           'phrases_any': ['retry', 'fallback', 'escalat', 'human'],
                                           'token_groups_all': []}]},
             'sample_answer': 'An agent loop repeatedly turns a goal into controlled actions: define the goal, choose the next step, call '
                              'an approved tool, observe the result, update state, and decide whether to continue, stop or escalate. For '
                              'example, an order-status agent verifies the requester, calls a read-only order API, checks the returned '
                              'record and then responds. A risk is looping on the same tool or acting on uncertain evidence. I would use a '
                              'maximum-step limit, validate each tool result, and require the loop to stop or escalate when the success '
                              'condition is met or evidence remains insufficient.',
             'mastery_repair_prompts': ['Can I state the mechanism without hiding behind generic AI vocabulary?',
                                        'Can I name a concrete failure that could happen in this exact scenario?',
                                        'Can I name an implementable control and what it blocks, limits or escalates?',
                                        'Can I state the stop, fallback or escalation behavior when evidence is insufficient?'],
             'is_gate': False,
             'assessment_principle': 'Normal lesson scoring is deterministic. MCQs use stable answer IDs and a published pass rule. The '
                                     'written response is scored only against the published mechanism, example, risk and control rubric. '
                                     'No hidden architecture vocabulary, essay-length preference or generic governance template may change '
                                     'the result.',
             'answer_quality_bar': {'three_star': 'Mechanism + concrete example + one specific risk + one implementable control.',
                                    'four_star': 'Adds evidence, tool boundary, stop condition or escalation behavior that is relevant to '
                                                 'the scenario.',
                                    'five_star': 'Adds multiple relevant operating details without adding unrelated architecture '
                                                 'vocabulary.'}},
 'aia_003': {'design_version': 'mlos_v4_deterministic_agentic_2026_08_17',
             'assessment_mode': 'v4_deterministic_mcq_plus_published_rubric',
             'topic_id': 'aia_003',
             'title': 'Tools, memory, guardrails and human checkpoints',
             'learning_objective': 'Distinguish tools, memory, guardrails and human checkpoints, then combine them so an agent can act '
                                   'without receiving unrestricted authority.',
             'prerequisite_bridge': 'Start from the agentic system behavior. Peel down only when a deeper mechanism explains a design '
                                    'decision or failure.',
             'concept_steps': [{'heading': '1. Tools',
                                'body': 'Tools are capabilities registered by the application runtime, such as `get_order`, `create_order` '
                                        'or `issue_refund`. The runtime holds credentials and validates arguments; the system prompt can '
                                        'describe policy but does not grant the credential.'},
                               {'heading': '2. Memory and state',
                                'body': 'Memory retains relevant context across steps or sessions, such as user identity, order state, '
                                        'previous observations or preferences. A system prompt is instruction, not memory.'},
                               {'heading': '3. Guardrails',
                                'body': 'Guardrails constrain what may be attempted: allow-listed tools, least-privilege permissions, '
                                        'parameter validation, amount limits, data boundaries and policy checks.'},
                               {'heading': '4. Human checkpoints',
                                'body': 'High-impact, ambiguous or irreversible actions pause before execution. The reviewer sees the '
                                        'request, evidence and proposed action, then approves, rejects or escalates.'},
                               {'heading': '5. Architect translation',
                                'body': 'Risk-tier the tools. Automate low-risk reads; gate sensitive writes; log decisions; make '
                                        'rejection and timeout behavior explicit.'}],
             'concept_map': [],
             'worked_example': {'scenario': 'A procurement agent may read an order automatically, but changing bank details or issuing a '
                                            'large refund requires an authorised approver. The agent carries order state and approval '
                                            'status between steps.',
                                'takeaway': 'Tools create capability, memory carries context, guardrails restrict capability, and '
                                            'checkpoints govern high-impact execution.'},
             'worked_examples': [{'title': 'Architect readout',
                                  'body': 'A procurement agent may read an order automatically, but changing bank details or issuing a '
                                          'large refund requires an authorised approver. The agent carries order state and approval status '
                                          'between steps. The design point is: Use tool-level identity, least privilege, typed schemas, '
                                          'risk tiers, approval gates, audit events, memory retention rules and explicit rejection '
                                          'behavior.'}],
             'code_bridge': {},
             'misconception': 'Treating a system prompt as the mechanism that grants tool access or as a substitute for runtime memory and '
                              'permissions.',
             'architect_extension': 'Use tool-level identity, least privilege, typed schemas, risk tiers, approval gates, audit events, '
                                    'memory retention rules and explicit rejection behavior.',
             'diagnostic_drill': {'question': "Can a system prompt saying 'never issue unauthorised refunds' replace an API permission "
                                              'check?',
                                  'reveal': 'No. Prompt policy is useful guidance, but the runtime must enforce permissions and approval '
                                            'independently.'},
             'knowledge_checks': [{'kind': 'Critical',
                                   'question': 'Where should an enterprise tool such as `issue_refund` actually be registered and '
                                               'executed?',
                                   'options': ['In the application runtime, which owns credentials, validates arguments and enforces '
                                               'permissions.',
                                               'In the system prompt, because describing a function gives the model controlled access to '
                                               'the API.',
                                               'In long-term memory, because persistent context is the safest place to keep callable '
                                               'capabilities.',
                                               'In the user message, because explicit user intent is sufficient authorization for a '
                                               'business action.'],
                                   'answer_index': 0,
                                   'explanation': 'Tool execution is a runtime capability, not a prompt or memory property.',
                                   'is_critical': True,
                                   'id': 'mcq_01'},
                                  {'kind': 'Critical',
                                   'question': 'Which item is memory rather than instruction?',
                                   'options': ['The verified order ID, previous lookup result and approval status carried into the next '
                                               'step.',
                                               'A system rule stating that refunds above a threshold require authorised approval.',
                                               'A tool schema describing the fields accepted by the `create_order` API.',
                                               'A permission policy restricting the service account to read-only access on the order '
                                               'database.'],
                                   'answer_index': 0,
                                   'explanation': 'Memory stores task context; the other items are instruction, schema or permission.',
                                   'is_critical': True,
                                   'id': 'mcq_02'},
                                  {'kind': 'Critical',
                                   'question': 'A customer-service agent can issue refunds up to any amount. Which control best reduces '
                                               'the risk without blocking normal automation?',
                                   'options': ['Set a low automatic limit and require an authorised approval gate above that limit.',
                                               'Keep unlimited access but ask the model to explain why each refund is reasonable before '
                                               'executing.',
                                               'Store previous successful refunds in memory so the model can imitate historically accepted '
                                               'decisions.',
                                               'Use a more capable model so it can distinguish fraudulent requests without needing '
                                               'transaction limits.'],
                                   'answer_index': 0,
                                   'explanation': 'Risk-based permissions and approvals constrain impact.',
                                   'is_critical': True,
                                   'id': 'mcq_03'},
                                  {'kind': 'Scenario',
                                   'question': 'A human reviewer rejects a bank-detail change. What state should the workflow preserve?',
                                   'options': ['The rejection, reviewer decision and blocked action so the agent cannot execute it later '
                                               'in the same task.',
                                               'Only the original user request so another model call can reconsider the decision from a '
                                               'clean context.',
                                               'The proposed bank details but not the rejection, because rejection is a temporary human '
                                               'opinion.',
                                               "Only the model's confidence score, because the reviewer decision can be reconstructed from "
                                               'the final response.'],
                                   'answer_index': 0,
                                   'explanation': 'Approval state must be durable and binding.',
                                   'is_critical': False,
                                   'id': 'mcq_04'},
                                  {'kind': 'Architecture',
                                   'question': 'Which tool should ordinarily receive the narrowest permissions?',
                                   'options': ['A tool that writes supplier bank details, because its side effects are high impact and '
                                               'difficult to reverse.',
                                               'A read-only order lookup, because read operations should always be more restricted than '
                                               'writes.',
                                               'A product-catalog search, because search tools create the largest number of possible model '
                                               'outputs.',
                                               'A policy retrieval tool, because grounding the model increases the chance that it will act '
                                               'automatically.'],
                                   'answer_index': 0,
                                   'explanation': 'Permission strength follows action risk.',
                                   'is_critical': False,
                                   'id': 'mcq_05'},
                                  {'kind': 'Scenario',
                                   'question': "An agent retrieves a customer's account record, then another user starts a new session. "
                                               'What memory control matters most?',
                                   'options': ['Scope stored context to the correct user/task and prevent cross-user retrieval of '
                                               'sensitive state.',
                                               'Keep all recent account records in shared memory so the next session can reuse successful '
                                               'tool results.',
                                               'Move the account record into the system prompt because instructions are isolated from user '
                                               'messages.',
                                               'Remove tool permissions after the first lookup because memory makes further authorization '
                                               'unnecessary.'],
                                   'answer_index': 0,
                                   'explanation': 'Memory needs identity and tenancy boundaries.',
                                   'is_critical': False,
                                   'id': 'mcq_06'},
                                  {'kind': 'Trap',
                                   'question': 'Which statement about guardrails is most accurate?',
                                   'options': ['Guardrails should be enforced in code and policy around the model, not trusted solely to '
                                               'prompt compliance.',
                                               'Guardrails are mainly warning text that helps a sufficiently capable model remember '
                                               'business rules.',
                                               'Guardrails are unnecessary when every action is logged because auditability makes unsafe '
                                               'execution acceptable.',
                                               "Guardrails should be applied only after a tool call so they do not constrain the model's "
                                               'reasoning flexibility.'],
                                   'answer_index': 0,
                                   'explanation': 'Enforcement belongs around execution.',
                                   'is_critical': False,
                                   'id': 'mcq_07'},
                                  {'kind': 'Scenario',
                                   'question': "A tool returns a customer's full account record, but the task needs only delivery status. "
                                               'What is the best design response?',
                                   'options': ['Minimise the tool response to the fields required by the task and apply authorization '
                                               'before returning data.',
                                               'Return the full record to the model but instruct it not to mention unnecessary fields in '
                                               'the final answer.',
                                               'Store the full record in memory so future requests do not need another authenticated '
                                               'database lookup.',
                                               'Ask the model to redact sensitive fields after it has already received and reasoned over '
                                               'the full record.'],
                                   'answer_index': 0,
                                   'explanation': 'Data minimisation should happen before model exposure where possible.',
                                   'is_critical': False,
                                   'id': 'mcq_08'},
                                  {'kind': 'Architecture',
                                   'question': 'What information should an approver see at a human checkpoint?',
                                   'options': ['The requested action, relevant evidence, risk context and exact effect that approval will '
                                               'authorise.',
                                               'The full hidden model reasoning so the approver can validate every internal token before '
                                               'deciding.',
                                               'Only a yes/no recommendation so the approval remains quick and does not expose '
                                               'implementation detail.',
                                               'The entire conversation history and all available customer data, even when most of it is '
                                               'unrelated.'],
                                   'answer_index': 0,
                                   'explanation': 'Approvals need decision-relevant evidence.',
                                   'is_critical': False,
                                   'id': 'mcq_09'},
                                  {'kind': 'Scenario',
                                   'question': 'A high-risk action waits for approval but no reviewer responds before the workflow '
                                               'timeout. What should happen?',
                                   'options': ['Follow a defined timeout path such as stop, safe fallback or escalation; do not '
                                               'auto-approve.',
                                               'Execute the action because the absence of rejection implies the reviewer had no objection.',
                                               'Ask the model to estimate whether the reviewer would probably have approved and continue '
                                               'accordingly.',
                                               'Remove the approval requirement for the current session so the user is not blocked by '
                                               'operational delay.'],
                                   'answer_index': 0,
                                   'explanation': 'Missing approval must never become implicit approval.',
                                   'is_critical': False,
                                   'id': 'mcq_10'}],
             'evidence_tasks': [{'question_id': 'q1',
                                 'type': 'architect_decision',
                                 'label': 'Short architect response',
                                 'purpose': 'Demonstrate the mechanism in one concrete scenario, then name one specific risk and one '
                                            'implementable control.',
                                 'question': 'In 80-140 words, explain Tools, memory, guardrails and human checkpoints using one business '
                                             'or engineering example. Include the mechanism, one risk and one control.',
                                 'expected_focus': ['mechanism', 'example', 'risk', 'control'],
                                 'response_shape': 'Mechanism → concrete example → specific risk → implementable control.',
                                 'target_min_words': 80,
                                 'target_max_words': 140,
                                 'sample_answer': 'In a procurement agent, tools let the runtime read or change business systems, while '
                                                  'memory carries relevant state such as the verified user, order ID, prior tool results '
                                                  'and approval status. Guardrails restrict what the agent may do, and human checkpoints '
                                                  'control high-impact actions. A specific risk is an over-privileged tool issuing an '
                                                  'unauthorised refund or exposing account data. I would use least-privilege permissions '
                                                  'and risk-based approval gates. Read-only lookups may run automatically, but sensitive '
                                                  'writes remain blocked until an authorised reviewer approves the proposed action and '
                                                  'supporting evidence.'}],
             'written_rubric': {'required': [{'id': 'mechanism',
                                              'label': 'Mechanism',
                                              'description': 'Explains how tools/memory/guardrails/checkpoints work together.',
                                              'phrases_any': ['tool',
                                                              'memory',
                                                              'guardrail',
                                                              'approval',
                                                              'checkpoint',
                                                              'runtime',
                                                              'permission'],
                                              'token_groups_all': [['tool', 'approval'], ['memory', 'tool']]},
                                             {'id': 'example',
                                              'label': 'Concrete example',
                                              'description': 'Uses a business or engineering example.',
                                              'phrases_any': ['procurement',
                                                              'order',
                                                              'refund',
                                                              'account',
                                                              'bank',
                                                              'support',
                                                              'for example',
                                                              'scenario'],
                                              'token_groups_all': []},
                                             {'id': 'risk',
                                              'label': 'Specific risk',
                                              'description': 'Names an unsafe tool or memory outcome.',
                                              'phrases_any': ['unauthor',
                                                              'refund',
                                                              'delete',
                                                              'disclos',
                                                              'data leak',
                                                              'wrong',
                                                              'full access',
                                                              'over-privilege',
                                                              'overprivilege'],
                                              'token_groups_all': []},
                                             {'id': 'control',
                                              'label': 'Operating control',
                                              'description': 'Names least privilege or approval behavior.',
                                              'phrases_any': ['read-only',
                                                              'least privilege',
                                                              'approval',
                                                              'human',
                                                              'allow-list',
                                                              'permission',
                                                              'limit',
                                                              'blocked',
                                                              'vet'],
                                              'token_groups_all': []}],
                                'bonus': [{'id': 'prompt_distinction',
                                           'label': 'Prompt distinction',
                                           'description': 'Distinguishes system prompt from memory/tool registration.',
                                           'phrases_any': ['system prompt', 'runtime', 'not memory', 'instruction'],
                                           'token_groups_all': []},
                                          {'id': 'audit',
                                           'label': 'Audit',
                                           'description': 'Mentions logging or audit trail.',
                                           'phrases_any': ['audit', 'log'],
                                           'token_groups_all': []}]},
             'sample_answer': 'In a procurement agent, tools let the runtime read or change business systems, while memory carries '
                              'relevant state such as the verified user, order ID, prior tool results and approval status. Guardrails '
                              'restrict what the agent may do, and human checkpoints control high-impact actions. A specific risk is an '
                              'over-privileged tool issuing an unauthorised refund or exposing account data. I would use least-privilege '
                              'permissions and risk-based approval gates. Read-only lookups may run automatically, but sensitive writes '
                              'remain blocked until an authorised reviewer approves the proposed action and supporting evidence.',
             'mastery_repair_prompts': ['Can I state the mechanism without hiding behind generic AI vocabulary?',
                                        'Can I name a concrete failure that could happen in this exact scenario?',
                                        'Can I name an implementable control and what it blocks, limits or escalates?',
                                        'Can I state the stop, fallback or escalation behavior when evidence is insufficient?'],
             'is_gate': False,
             'assessment_principle': 'Normal lesson scoring is deterministic. MCQs use stable answer IDs and a published pass rule. The '
                                     'written response is scored only against the published mechanism, example, risk and control rubric. '
                                     'No hidden architecture vocabulary, essay-length preference or generic governance template may change '
                                     'the result.',
             'answer_quality_bar': {'three_star': 'Mechanism + concrete example + one specific risk + one implementable control.',
                                    'four_star': 'Adds evidence, tool boundary, stop condition or escalation behavior that is relevant to '
                                                 'the scenario.',
                                    'five_star': 'Adds multiple relevant operating details without adding unrelated architecture '
                                                 'vocabulary.'}},
 'aia_004': {'design_version': 'mlos_v4_deterministic_agentic_2026_08_17',
             'assessment_mode': 'v4_deterministic_mcq_plus_published_rubric',
             'topic_id': 'aia_004',
             'title': 'Agent planning and task decomposition',
             'learning_objective': 'Break a vague business goal into bounded, observable tasks with allowed tools, evidence, completion '
                                   'conditions and escalation paths.',
             'prerequisite_bridge': 'Start from the agentic system behavior. Peel down only when a deeper mechanism explains a design '
                                    'decision or failure.',
             'concept_steps': [{'heading': '1. Start with a testable goal',
                                'body': "Turn a broad goal into a success condition. 'Handle procurement' is vague. 'Return the current "
                                        "status of an authorised order and stop if identity or order evidence cannot be verified' is "
                                        'bounded.'},
                               {'heading': '2. Decompose into observable steps',
                                'body': 'Each step should have an input, one bounded action, expected evidence and a clear outcome. '
                                        'Example: validate identity → capture order ID → call `get_order` → verify returned customer/order '
                                        'match → respond.'},
                               {'heading': '3. Constrain tools per step',
                                'body': 'A planning schema should say which tools a step may use. A status-check plan does not need '
                                        '`delete_order`, unrestricted SQL or supplier-bank write access.'},
                               {'heading': '4. Define risk and stop behavior',
                                'body': 'Planning can fail through vague goals, repeated steps, unauthorised actions, missing evidence or '
                                        'no stopping rule. Controls include least privilege, evidence checks, max-step limits and '
                                        'escalation when evidence is insufficient.'},
                               {'heading': '5. Architect translation',
                                'body': 'A useful plan schema is: goal, step, allowed tool, required evidence, success/failure condition, '
                                        'next step and escalation. The runtime validates the plan rather than blindly executing '
                                        'model-generated actions.'}],
             'concept_map': [],
             'worked_example': {'scenario': 'A procurement agent checks order status. It verifies the requester, captures the order '
                                            'number, uses a read-only `get_order` tool, checks that the returned record belongs to the '
                                            'authorised customer, then answers. Missing or conflicting evidence stops the flow and routes '
                                            'to a human.',
                                'takeaway': 'Decomposition turns a vague goal into bounded steps whose evidence and permissions can be '
                                            'tested.'},
             'worked_examples': [{'title': 'Architect readout',
                                  'body': 'A procurement agent checks order status. It verifies the requester, captures the order number, '
                                          'uses a read-only `get_order` tool, checks that the returned record belongs to the authorised '
                                          'customer, then answers. Missing or conflicting evidence stops the flow and routes to a human. '
                                          'The design point is: Require a structured plan with goal, bounded steps, allowed tools, '
                                          'evidence per step, completion/failure conditions, step budget and escalation path.'}],
             'code_bridge': {},
             'misconception': 'Treating a plan as a long natural-language to-do list with no evidence, permission boundary, stop condition '
                              'or recovery behavior.',
             'architect_extension': 'Require a structured plan with goal, bounded steps, allowed tools, evidence per step, '
                                    'completion/failure conditions, step budget and escalation path.',
             'diagnostic_drill': {'question': "A plan says 'search until you find the answer'. What is missing?",
                                  'reveal': 'It needs bounded search steps, evidence criteria, a maximum attempt/step budget and a stop or '
                                            'escalation path when the evidence is insufficient.'},
             'knowledge_checks': [{'kind': 'Critical',
                                   'question': 'A procurement agent must answer an order-status request. Which plan is best decomposed?',
                                   'options': ['Verify requester → capture order ID → read order → verify ownership → return status or '
                                               'escalate on missing evidence.',
                                               "Understand the user's need → investigate the situation thoroughly → use useful tools → "
                                               'provide the best possible answer.',
                                               'Read the order database → continue searching related records → compare all available data '
                                               '→ answer when confidence feels high.',
                                               'Ask the model to create a detailed plan → execute every generated step → summarize the '
                                               'result → store the plan for later use.'],
                                   'answer_index': 0,
                                   'explanation': 'Good decomposition uses bounded observable steps and stop behavior.',
                                   'is_critical': True,
                                   'id': 'mcq_01'},
                                  {'kind': 'Critical',
                                   'question': 'Why should a planning schema record required evidence for each step?',
                                   'options': ['So the runtime can decide whether the step succeeded before allowing dependent actions to '
                                               'continue.',
                                               'So the model can produce a longer explanation of why it chose each step in the final '
                                               'response.',
                                               'So every step can use the same tool even when the evidence requirements differ across the '
                                               'workflow.',
                                               'So the planner can avoid explicit failure conditions because evidence automatically '
                                               'guarantees task completion.'],
                                   'answer_index': 0,
                                   'explanation': 'Evidence makes step completion testable.',
                                   'is_critical': True,
                                   'id': 'mcq_02'},
                                  {'kind': 'Critical',
                                   'question': 'A status-check plan includes a general SQL write tool even though the task only needs '
                                               'reads. What is the main architecture issue?',
                                   'options': ['The plan violates least privilege by exposing a capability that is unnecessary for the '
                                               'task.',
                                               'The plan is inefficient because SQL tools always consume more model tokens than read-only '
                                               'APIs.',
                                               'The plan is incomplete because every database read should be paired with a database write '
                                               'step.',
                                               'The plan is too deterministic because allowing fewer tools prevents the model from '
                                               'adapting to new requests.'],
                                   'answer_index': 0,
                                   'explanation': "Allowed tools should match the task's required authority.",
                                   'is_critical': True,
                                   'id': 'mcq_03'},
                                  {'kind': 'Scenario',
                                   'question': 'The order lookup returns two records with the same customer name but different account '
                                               'IDs. What should the plan do?',
                                   'options': ['Stop the normal path and request additional verified evidence or escalate before '
                                               'disclosing either order.',
                                               'Choose the most recent record because recency is usually enough evidence for an '
                                               'order-status response.',
                                               'Return both records so the user can identify the correct one after seeing the available '
                                               'order information.',
                                               'Continue to the response step because the lookup tool succeeded and therefore the '
                                               'retrieval step is complete.'],
                                   'answer_index': 0,
                                   'explanation': 'Ambiguous evidence should trigger a defined failure path.',
                                   'is_critical': False,
                                   'id': 'mcq_04'},
                                  {'kind': 'Architecture',
                                   'question': 'Which field most clearly distinguishes a robust plan step from a natural-language to-do '
                                               'item?',
                                   'options': ['A machine-checkable success/failure condition tied to evidence from the action.',
                                               'A descriptive explanation of why the model believes the step is relevant to the goal.',
                                               'A confidence score generated by the model after it writes the step in the plan.',
                                               'A list of alternative prompts that could be used if the user dislikes the first answer.'],
                                   'answer_index': 0,
                                   'explanation': 'Observable success/failure turns planning into workflow control.',
                                   'is_critical': False,
                                   'id': 'mcq_05'},
                                  {'kind': 'Scenario',
                                   'question': 'A supplier-search agent keeps calling the same search tool with slightly different '
                                               'queries. What planning control is most direct?',
                                   'options': ['Set a bounded search/step budget and define the evidence threshold for stopping or '
                                               'escalating.',
                                               'Increase the context window so the agent can remember more query variants before repeating '
                                               'itself.',
                                               'Add another search provider so the planner has more possible actions when the first '
                                               'provider is inconclusive.',
                                               'Raise model temperature so repeated queries diverge more quickly and eventually produce a '
                                               'different supplier list.'],
                                   'answer_index': 0,
                                   'explanation': 'Bounded attempts plus evidence criteria prevent runaway search.',
                                   'is_critical': False,
                                   'id': 'mcq_06'},
                                  {'kind': 'Trap',
                                   'question': 'Which statement about task decomposition is most accurate?',
                                   'options': ['Decomposition improves control only when steps have boundaries, evidence and failure '
                                               'behavior, not merely smaller wording.',
                                               'Decomposition makes an agent deterministic because each smaller step is easier for an LLM '
                                               'to execute correctly.',
                                               'Decomposition removes the need for tool permissions because each individual step has '
                                               'limited business scope.',
                                               'Decomposition should always create the maximum number of steps because smaller tasks are '
                                               'inherently safer.'],
                                   'answer_index': 0,
                                   'explanation': 'Smaller tasks help only when they are governed and observable.',
                                   'is_critical': False,
                                   'id': 'mcq_07'},
                                  {'kind': 'Scenario',
                                   'question': 'An agent has already verified the requested order status and the success condition is met. '
                                               'The generated plan still contains two optional enrichment steps. What should happen?',
                                   'options': ["Stop and answer, because the plan's completion condition has been satisfied.",
                                               'Execute the remaining steps because every generated plan item must run for audit '
                                               'consistency.',
                                               'Regenerate a longer plan so the optional steps can be replaced with mandatory verification '
                                               'tasks.',
                                               'Continue until the maximum-step budget is consumed because unused budget indicates '
                                               'incomplete planning.'],
                                   'answer_index': 0,
                                   'explanation': 'Completion criteria override unnecessary planned work.',
                                   'is_critical': False,
                                   'id': 'mcq_08'},
                                  {'kind': 'Architecture',
                                   'question': 'Which plan representation is easiest to validate before execution?',
                                   'options': ['A structured schema containing step ID, allowed action, required evidence, success/failure '
                                               'condition and next transition.',
                                               "A paragraph describing the agent's intention, rationale and likely sequence in fluent "
                                               'natural language.',
                                               'A hidden reasoning trace containing every candidate step considered by the model before '
                                               'choosing the final plan.',
                                               'A list of tool names ordered by the model, with the tool arguments generated only after '
                                               'each call begins.'],
                                   'answer_index': 0,
                                   'explanation': 'Structured plans expose enforceable fields.',
                                   'is_critical': False,
                                   'id': 'mcq_09'},
                                  {'kind': 'Scenario',
                                   'question': 'A financial approval step is reached, but the designated approver is unavailable. What '
                                               'should the plan specify?',
                                   'options': ['A timeout and escalation or safe-stop path that preserves the blocked transaction.',
                                               'Automatic approval after a reasonable delay so the rest of the plan can continue.',
                                               'A model-confidence threshold that substitutes for the missing approver when confidence is '
                                               'high.',
                                               'A retry loop that repeatedly sends the same approval request until the workflow deadline '
                                               'expires.'],
                                   'answer_index': 0,
                                   'explanation': 'Plans need explicit exception paths, not implicit authority.',
                                   'is_critical': False,
                                   'id': 'mcq_10'}],
             'evidence_tasks': [{'question_id': 'q1',
                                 'type': 'architect_decision',
                                 'label': 'Short architect response',
                                 'purpose': 'Demonstrate the mechanism in one concrete scenario, then name one specific risk and one '
                                            'implementable control.',
                                 'question': 'In 80-140 words, explain Agent planning and task decomposition using one business or '
                                             'engineering example. Include the mechanism, one risk and one control.',
                                 'expected_focus': ['mechanism', 'example', 'risk', 'control'],
                                 'response_shape': 'Mechanism → concrete example → specific risk → implementable control.',
                                 'target_min_words': 80,
                                 'target_max_words': 140,
                                 'sample_answer': 'In a procurement agent, planning turns a broad goal such as “check order status” into '
                                                  'bounded steps: verify the requester, capture the order ID, call the read-only '
                                                  '`get_order` tool, verify that the returned order belongs to the authorised customer, '
                                                  'then return the status. Each step has required evidence and a success or failure '
                                                  'condition. A specific risk is that a vague plan or over-privileged tool could expose '
                                                  'another customer’s data or perform an unintended write. I would restrict the plan to '
                                                  'allowed read-only tools and set stop conditions. If identity or order evidence is '
                                                  'missing or ambiguous, the agent must stop and escalate to a human rather than continue '
                                                  'guessing.'}],
             'written_rubric': {'required': [{'id': 'mechanism',
                                              'label': 'Planning mechanism',
                                              'description': 'Explains decomposition into bounded steps or a plan schema.',
                                              'phrases_any': ['decompos',
                                                              'plan schema',
                                                              'bounded step',
                                                              'sequence of steps',
                                                              'steps',
                                                              'goal'],
                                              'token_groups_all': [['goal', 'step'], ['plan', 'step']]},
                                             {'id': 'example',
                                              'label': 'Concrete example',
                                              'description': 'Uses a business or engineering scenario.',
                                              'phrases_any': ['procurement',
                                                              'order',
                                                              'customer',
                                                              'supplier',
                                                              'database',
                                                              'for example',
                                                              'scenario',
                                                              'agent'],
                                              'token_groups_all': []},
                                             {'id': 'risk',
                                              'label': 'Specific risk',
                                              'description': 'Names a concrete planning or action risk.',
                                              'phrases_any': ['unauthor',
                                                              'not authoris',
                                                              'delete',
                                                              'wrong',
                                                              'vague',
                                                              'repeat',
                                                              'no stop',
                                                              'ambiguous',
                                                              'full access',
                                                              'unintended',
                                                              'expose another'],
                                              'token_groups_all': []},
                                             {'id': 'control',
                                              'label': 'Operating control',
                                              'description': 'Names a concrete implementable control.',
                                              'phrases_any': ['read-only',
                                                              'human approval',
                                                              'approval',
                                                              'allowed tool',
                                                              'least privilege',
                                                              'stop',
                                                              'escalat',
                                                              'guardrail',
                                                              'max step',
                                                              'evidence',
                                                              'authoris',
                                                              'authorize'],
                                              'token_groups_all': []}],
                                'bonus': [{'id': 'evidence',
                                           'label': 'Evidence per step',
                                           'description': 'Requires observable evidence or validation at a step.',
                                           'phrases_any': ['evidence', 'verify', 'verified', 'validation', 'authentic', 'accurate'],
                                           'token_groups_all': []},
                                          {'id': 'stop_escalation',
                                           'label': 'Stop/escalation',
                                           'description': 'States a stop, escalation or failure path.',
                                           'phrases_any': ['stop', 'escalat', 'cannot execute', 'can not execute', 'blocked', 'timeout'],
                                           'token_groups_all': [['stop', 'human'], ['escalat', 'human']]},
                                          {'id': 'tool_boundary',
                                           'label': 'Tool boundary',
                                           'description': 'Limits tools or permissions to the step.',
                                           'phrases_any': ['read-only', 'write access', 'allowed tools', 'permission', 'least privilege'],
                                           'token_groups_all': []}]},
             'sample_answer': 'In a procurement agent, planning turns a broad goal such as “check order status” into bounded steps: verify '
                              'the requester, capture the order ID, call the read-only `get_order` tool, verify that the returned order '
                              'belongs to the authorised customer, then return the status. Each step has required evidence and a success '
                              'or failure condition. A specific risk is that a vague plan or over-privileged tool could expose another '
                              'customer’s data or perform an unintended write. I would restrict the plan to allowed read-only tools and '
                              'set stop conditions. If identity or order evidence is missing or ambiguous, the agent must stop and '
                              'escalate to a human rather than continue guessing.',
             'mastery_repair_prompts': ['Can I state the mechanism without hiding behind generic AI vocabulary?',
                                        'Can I name a concrete failure that could happen in this exact scenario?',
                                        'Can I name an implementable control and what it blocks, limits or escalates?',
                                        'Can I state the stop, fallback or escalation behavior when evidence is insufficient?'],
             'is_gate': False,
             'assessment_principle': 'Normal lesson scoring is deterministic. MCQs use stable answer IDs and a published pass rule. The '
                                     'written response is scored only against the published mechanism, example, risk and control rubric. '
                                     'No hidden architecture vocabulary, essay-length preference or generic governance template may change '
                                     'the result.',
             'answer_quality_bar': {'three_star': 'Mechanism + concrete example + one specific risk + one implementable control.',
                                    'four_star': 'Adds evidence, tool boundary, stop condition or escalation behavior that is relevant to '
                                                 'the scenario.',
                                    'five_star': 'Adds multiple relevant operating details without adding unrelated architecture '
                                                 'vocabulary.'}},
 'aia_005': {'design_version': 'mlos_v4_deterministic_agentic_2026_08_17',
             'assessment_mode': 'v4_deterministic_mcq_plus_published_rubric',
             'topic_id': 'aia_005',
             'title': 'Tool calling, APIs and action boundaries',
             'learning_objective': 'Design tool calls as typed, permissioned API operations with validated inputs, explicit side-effect '
                                   'boundaries, safe retries and auditable outcomes.',
             'prerequisite_bridge': 'Start from the agentic system behavior. Peel down only when a deeper mechanism explains a design '
                                    'decision or failure.',
             'concept_steps': [{'heading': '1. Tool schema',
                                'body': 'A tool exposes a narrow operation with typed inputs and documented output. Good schemas make '
                                        'invalid or ambiguous requests harder to express.'},
                               {'heading': '2. Runtime validation',
                                'body': 'The model may propose a tool call, but the runtime checks identity, permission, parameter '
                                        'constraints and policy before the external API runs.'},
                               {'heading': '3. Read versus write risk',
                                'body': 'Read tools, reversible updates and irreversible/high-impact actions should have different '
                                        'permissions, limits and approval requirements.'},
                               {'heading': '4. Retry safety',
                                'body': 'Network failures can leave the outcome unknown. Writes need idempotency or authoritative state '
                                        'checks before retry.'},
                               {'heading': '5. Architect translation',
                                'body': 'Use least privilege, allow-listed endpoints, typed validation, timeouts, idempotency, audit IDs '
                                        'and risk-based approval.'}],
             'concept_map': [],
             'worked_example': {'scenario': 'A purchasing agent may call `get_supplier_quote` automatically. `create_purchase_order` '
                                            'validates supplier, amount and cost center, uses an idempotency key, and requires approval '
                                            'above the automatic spend limit.',
                                'takeaway': 'The model selects a capability; the runtime decides whether the proposed API action is valid '
                                            'and authorised.'},
             'worked_examples': [{'title': 'Architect readout',
                                  'body': 'A purchasing agent may call `get_supplier_quote` automatically. `create_purchase_order` '
                                          'validates supplier, amount and cost center, uses an idempotency key, and requires approval '
                                          'above the automatic spend limit. The design point is: Design tools as narrow application '
                                          'capabilities with service identities, schemas, policy checks, risk tiers, idempotency, '
                                          'timeout/retry rules and trace IDs.'}],
             'code_bridge': {},
             'misconception': 'Assuming a tool is safe because its description tells the model when not to use it.',
             'architect_extension': 'Design tools as narrow application capabilities with service identities, schemas, policy checks, risk '
                                    'tiers, idempotency, timeout/retry rules and trace IDs.',
             'diagnostic_drill': {'question': 'A create-PO API times out. Should the agent immediately retry?',
                                  'reveal': 'Not blindly. Verify state or retry with the same idempotency key so an uncertain first call '
                                            'cannot create a duplicate PO.'},
             'knowledge_checks': [{'kind': 'Critical',
                                   'question': 'What is the safest tool definition for changing a purchase-order delivery date?',
                                   'options': ['A narrow `update_delivery_date(po_id, new_date)` operation with typed validation and '
                                               'policy checks.',
                                               'A generic `execute_sql(statement)` tool that lets the model update any field required by '
                                               'the request.',
                                               'A shell tool with database credentials so the model can adapt the update when schema '
                                               'details change.',
                                               'A broad `modify_purchase_order(payload)` tool that accepts arbitrary JSON and trusts the '
                                               'model to include safe fields.'],
                                   'answer_index': 0,
                                   'explanation': 'Narrow typed operations reduce authority and ambiguity.',
                                   'is_critical': True,
                                   'id': 'mcq_01'},
                                  {'kind': 'Critical',
                                   'question': 'A model proposes `issue_refund(amount=50000)` for a user whose limit is 500. Where should '
                                               'the call be rejected?',
                                   'options': ['In runtime policy validation before the refund API is invoked.',
                                               'In the final response after the external refund has completed.',
                                               'In conversation memory so future sessions remember not to repeat it.',
                                               "In the LLM's explanation step after it has decided the tool is appropriate."],
                                   'answer_index': 0,
                                   'explanation': 'Authorization must be enforced before side effects.',
                                   'is_critical': True,
                                   'id': 'mcq_02'},
                                  {'kind': 'Critical',
                                   'question': 'Why is idempotency important for side-effecting API tools?',
                                   'options': ['It lets uncertain retries return the same operation result without creating duplicate side '
                                               'effects.',
                                               "It makes the LLM's choice of tool deterministic across different user prompts and model "
                                               'versions.',
                                               'It prevents the API from returning validation errors when the model supplies an invalid '
                                               'argument.',
                                               'It replaces the need for transaction logging because repeated requests are automatically '
                                               'ignored forever.'],
                                   'answer_index': 0,
                                   'explanation': 'Idempotency controls retries, not all validation/audit.',
                                   'is_critical': True,
                                   'id': 'mcq_03'},
                                  {'kind': 'Scenario',
                                   'question': 'A tool requires a free-text `customer_id_or_name` field, and the model submits a name '
                                               'shared by several customers. What is the better design?',
                                   'options': ['Require a unique customer identifier or add a disambiguation step before a sensitive '
                                               'action.',
                                               'Let the API choose the first name match because deterministic server ordering removes '
                                               'model uncertainty.',
                                               'Ask the model to select the most likely customer using conversational context and execute '
                                               'immediately.',
                                               'Increase tool-description detail so the model learns which duplicate name is usually the '
                                               'intended account.'],
                                   'answer_index': 0,
                                   'explanation': 'Typed identifiers and disambiguation reduce ambiguous side effects.',
                                   'is_critical': False,
                                   'id': 'mcq_04'},
                                  {'kind': 'Architecture',
                                   'question': 'Which identity should a production tool call normally use?',
                                   'options': ["A scoped service or delegated identity whose permissions match the tool's intended "
                                               'operation.',
                                               "The model provider's API key because the LLM initiated the tool call and should own its "
                                               'permissions.',
                                               'A shared administrator credential so every tool can adapt to unexpected workflow '
                                               'requirements.',
                                               "The end user's password stored in memory so the agent can authenticate repeatedly without "
                                               'interruption.'],
                                   'answer_index': 0,
                                   'explanation': 'Tool identities should be scoped and managed.',
                                   'is_critical': False,
                                   'id': 'mcq_05'},
                                  {'kind': 'Scenario',
                                   'question': 'A read API returns 20 sensitive fields but the agent needs only two. What should the tool '
                                               'layer do?',
                                   'options': ['Return only the task-required fields when possible and enforce authorization before data '
                                               'reaches the model.',
                                               'Return all fields and depend on the final-answer prompt to prevent the model from '
                                               'disclosing the extras.',
                                               'Place the full response in long-term memory so future tool calls can be avoided for '
                                               'performance reasons.',
                                               'Ask the model to redact fields after reasoning because model-level redaction is more '
                                               'flexible than API design.'],
                                   'answer_index': 0,
                                   'explanation': 'Minimise sensitive data exposure.',
                                   'is_critical': False,
                                   'id': 'mcq_06'},
                                  {'kind': 'Trap',
                                   'question': 'Which error should normally be retried automatically?',
                                   'options': ['A transient 503 on a read-only request, using bounded backoff and an overall retry limit.',
                                               'A 403 permission failure on a refund request, because permissions may change if the call '
                                               'is repeated.',
                                               'A schema-validation failure caused by an invalid account identifier, because the model may '
                                               'get lucky on retry.',
                                               'A human rejection of a high-value transaction, because approval services can return '
                                               'temporary business decisions.'],
                                   'answer_index': 0,
                                   'explanation': 'Retry transient technical failures, not policy/business failures.',
                                   'is_critical': False,
                                   'id': 'mcq_07'},
                                  {'kind': 'Architecture',
                                   'question': 'What should be logged for a sensitive tool call?',
                                   'options': ['Trace ID, requester/task identity, validated arguments or safe hashes, authorization '
                                               'decision, result and approval reference.',
                                               'Only the final natural-language answer so the tool details remain hidden from operational '
                                               'reviewers.',
                                               'Every secret and credential used by the tool so investigators can exactly reproduce the '
                                               'call later.',
                                               'Only the tool name and latency because arguments and authorization belong exclusively to '
                                               'application code.'],
                                   'answer_index': 0,
                                   'explanation': 'Audits need decision context without exposing secrets.',
                                   'is_critical': False,
                                   'id': 'mcq_08'},
                                  {'kind': 'Scenario',
                                   'question': 'A model chooses a write tool when a read-only tool could satisfy the request. What policy '
                                               'is best?',
                                   'options': ['Reject or reroute to the least-privileged capability that can satisfy the task.',
                                               "Allow the write because a valid result proves that the model understood the user's goal.",
                                               'Permit the write if it is faster, then restore the original state after returning the '
                                               'response.',
                                               "Increase monitoring only; restricting the tool would reduce the model's ability to adapt."],
                                   'answer_index': 0,
                                   'explanation': 'Least privilege applies to tool selection.',
                                   'is_critical': False,
                                   'id': 'mcq_09'},
                                  {'kind': 'Architecture',
                                   'question': 'Which boundary belongs in the tool contract rather than only in prompt text?',
                                   'options': ['Maximum refund amount and the approval requirement above that amount.',
                                               'A preferred conversational tone for explaining why a refund request was rejected.',
                                               'A suggestion to summarize tool outputs concisely before showing them to the user.',
                                               'A reminder that the model should think carefully before selecting any action.'],
                                   'answer_index': 0,
                                   'explanation': 'Business action limits require enforceable policy.',
                                   'is_critical': False,
                                   'id': 'mcq_10'}],
             'evidence_tasks': [{'question_id': 'q1',
                                 'type': 'architect_decision',
                                 'label': 'Short architect response',
                                 'purpose': 'Demonstrate the mechanism in one concrete scenario, then name one specific risk and one '
                                            'implementable control.',
                                 'question': 'In 80-140 words, explain Tool calling, APIs and action boundaries using one business or '
                                             'engineering example. Include the mechanism, one risk and one control.',
                                 'expected_focus': ['mechanism', 'example', 'risk', 'control'],
                                 'response_shape': 'Mechanism → concrete example → specific risk → implementable control.',
                                 'target_min_words': 80,
                                 'target_max_words': 140,
                                 'sample_answer': 'A tool call should be treated as a typed API request, not as free-form model authority. '
                                                  'The LLM proposes a tool and arguments, but the runtime validates the schema, user '
                                                  'permissions and side-effect boundary before execution. For example, a procurement agent '
                                                  'may call `create_order` only with validated supplier, quantity and approval data. A '
                                                  'risk is a duplicate or unauthorised write caused by bad arguments or retries. I would '
                                                  'enforce typed validation, least-privilege credentials, idempotency keys for writes, and '
                                                  'approval for high-impact operations. The runtime logs the request and result so failed '
                                                  'or repeated calls can be traced safely.'}],
             'written_rubric': {'required': [{'id': 'mechanism',
                                              'label': 'Tool/API mechanism',
                                              'description': 'Explains model proposes call and runtime validates/executes it.',
                                              'phrases_any': ['tool call', 'api', 'runtime', 'schema', 'parameter', 'function', 'execute'],
                                              'token_groups_all': []},
                                             {'id': 'example',
                                              'label': 'Concrete example',
                                              'description': 'Uses a tool/API business example.',
                                              'phrases_any': ['order', 'refund', 'supplier', 'api', 'database', 'for example', 'scenario'],
                                              'token_groups_all': []},
                                             {'id': 'risk',
                                              'label': 'Specific risk',
                                              'description': 'Names unsafe call, ambiguity, duplicate or over-permission.',
                                              'phrases_any': ['unauthor',
                                                              'duplicate',
                                                              'wrong',
                                                              'ambiguous',
                                                              'full access',
                                                              'sensitive',
                                                              'over-privilege',
                                                              'overprivilege'],
                                              'token_groups_all': []},
                                             {'id': 'control',
                                              'label': 'Operating control',
                                              'description': 'Names typed validation, least privilege, approval, idempotency or '
                                                             'allow-list.',
                                              'phrases_any': ['validation',
                                                              'read-only',
                                                              'least privilege',
                                                              'approval',
                                                              'idempot',
                                                              'allow-list',
                                                              'permission',
                                                              'limit'],
                                              'token_groups_all': []}],
                                'bonus': [{'id': 'retry',
                                           'label': 'Retry safety',
                                           'description': 'Mentions timeout/retry/state verification.',
                                           'phrases_any': ['retry', 'timeout', 'state check'],
                                           'token_groups_all': []},
                                          {'id': 'audit',
                                           'label': 'Auditability',
                                           'description': 'Mentions trace/audit logging.',
                                           'phrases_any': ['audit', 'trace', 'log'],
                                           'token_groups_all': []}]},
             'sample_answer': 'A tool call should be treated as a typed API request, not as free-form model authority. The LLM proposes a '
                              'tool and arguments, but the runtime validates the schema, user permissions and side-effect boundary before '
                              'execution. For example, a procurement agent may call `create_order` only with validated supplier, quantity '
                              'and approval data. A risk is a duplicate or unauthorised write caused by bad arguments or retries. I would '
                              'enforce typed validation, least-privilege credentials, idempotency keys for writes, and approval for '
                              'high-impact operations. The runtime logs the request and result so failed or repeated calls can be traced '
                              'safely.',
             'mastery_repair_prompts': ['Can I state the mechanism without hiding behind generic AI vocabulary?',
                                        'Can I name a concrete failure that could happen in this exact scenario?',
                                        'Can I name an implementable control and what it blocks, limits or escalates?',
                                        'Can I state the stop, fallback or escalation behavior when evidence is insufficient?'],
             'is_gate': False,
             'assessment_principle': 'Normal lesson scoring is deterministic. MCQs use stable answer IDs and a published pass rule. The '
                                     'written response is scored only against the published mechanism, example, risk and control rubric. '
                                     'No hidden architecture vocabulary, essay-length preference or generic governance template may change '
                                     'the result.',
             'answer_quality_bar': {'three_star': 'Mechanism + concrete example + one specific risk + one implementable control.',
                                    'four_star': 'Adds evidence, tool boundary, stop condition or escalation behavior that is relevant to '
                                                 'the scenario.',
                                    'five_star': 'Adds multiple relevant operating details without adding unrelated architecture '
                                                 'vocabulary.'}},
 'aia_006': {'design_version': 'mlos_v4_deterministic_agentic_2026_08_17',
             'assessment_mode': 'v4_deterministic_mcq_plus_published_rubric',
             'topic_id': 'aia_006',
             'title': 'Agent memory, retrieval and state',
             'learning_objective': 'Separate working state, conversation memory and retrieved long-term knowledge, then govern freshness, '
                                   'identity, provenance and retention.',
             'prerequisite_bridge': 'Start from the agentic system behavior. Peel down only when a deeper mechanism explains a design '
                                    'decision or failure.',
             'concept_steps': [{'heading': '1. Working state',
                                'body': 'Working state tracks the current task: goal, step, tool results, pending approvals and completion '
                                        'status.'},
                               {'heading': '2. Conversation memory',
                                'body': 'Conversation memory keeps relevant prior interaction context. It should be scoped to the correct '
                                        'user/session and should not become an uncontrolled transcript dump.'},
                               {'heading': '3. Retrieved long-term knowledge',
                                'body': 'Persistent facts or preferences should be retrieved from governed stores with provenance and '
                                        'freshness, not assumed true because an earlier model message mentioned them.'},
                               {'heading': '4. Memory failure modes',
                                'body': 'Stale facts, cross-user leakage, poisoned notes and conflicting sources can silently drive wrong '
                                        'actions.'},
                               {'heading': '5. Architect translation',
                                'body': 'Define memory type, owner, retention, access scope, provenance, freshness rules, conflict '
                                        'resolution and deletion behavior.'}],
             'concept_map': [],
             'worked_example': {'scenario': "A travel-booking agent keeps the current itinerary in working state, retrieves the user's "
                                            'saved seat preference from a profile store, and rechecks live flight availability rather than '
                                            "trusting yesterday's search result.",
                                'takeaway': 'Different information has different lifetime and authority; memory is not a substitute for '
                                            'live source-of-truth checks.'},
             'worked_examples': [{'title': 'Architect readout',
                                  'body': "A travel-booking agent keeps the current itinerary in working state, retrieves the user's saved "
                                          'seat preference from a profile store, and rechecks live flight availability rather than '
                                          "trusting yesterday's search result. The design point is: Use typed state, tenant/user scoping, "
                                          'provenance, TTL/freshness rules, source-of-truth refresh, retention limits and conflict '
                                          'handling.'}],
             'code_bridge': {},
             'misconception': "Calling every piece of context 'memory' and treating old model-generated text as authoritative state.",
             'architect_extension': 'Use typed state, tenant/user scoping, provenance, TTL/freshness rules, source-of-truth refresh, '
                                    'retention limits and conflict handling.',
             'diagnostic_drill': {'question': "Yesterday's memory says an order was 'shipped'. Can today's agent answer from that memory "
                                              'alone?',
                                  'reveal': 'No when current status matters. Treat the memory as context and refresh from the '
                                            'authoritative order system.'},
             'knowledge_checks': [{'kind': 'Critical',
                                   'question': 'Which item belongs in working state for a multi-step procurement task?',
                                   'options': ['The current order ID, completed checks, latest tool result and pending approval status.',
                                               'A permanent summary of every procurement conversation from all users in the organization.',
                                               'The API credential used to query the order service so the model can reuse it in later '
                                               'sessions.',
                                               'A generic system instruction telling the agent to be helpful and follow procurement '
                                               'policy.'],
                                   'answer_index': 0,
                                   'explanation': 'Working state tracks current task progress.',
                                   'is_critical': True,
                                   'id': 'mcq_01'},
                                  {'kind': 'Critical',
                                   'question': "A saved memory says a supplier is 'approved', but the supplier master now marks it "
                                               'suspended. What should the agent do?',
                                   'options': ['Refresh the authoritative supplier record and treat the saved memory only as historical '
                                               'context.',
                                               'Trust the saved memory because persistent memory is intended to prevent repeated '
                                               'source-system lookups.',
                                               'Average the two states and ask the model to decide which status is more likely to be '
                                               'current.',
                                               'Keep both states in context and proceed unless the model expresses uncertainty in the '
                                               'final response.'],
                                   'answer_index': 0,
                                   'explanation': 'Current authoritative data overrides stale memory.',
                                   'is_critical': True,
                                   'id': 'mcq_02'},
                                  {'kind': 'Critical',
                                   'question': "What is the strongest control against one customer's memory appearing in another "
                                               "customer's session?",
                                   'options': ['Enforce user/tenant scoping in the memory store and retrieval query before context reaches '
                                               'the model.',
                                               'Add a system-prompt reminder that the model must never mention data belonging to another '
                                               'customer.',
                                               'Use a larger model because stronger instruction following reduces accidental cross-user '
                                               'recall.',
                                               'Store all memories in one collection but ask the retriever to prefer records with similar '
                                               'wording.'],
                                   'answer_index': 0,
                                   'explanation': 'Isolation must be enforced at storage/retrieval.',
                                   'is_critical': True,
                                   'id': 'mcq_03'},
                                  {'kind': 'Scenario',
                                   'question': "A user tells an agent 'always ship to the old address' once, but the account profile later "
                                               'changes. How should persistent memory behave?',
                                   'options': ['Use provenance and freshness rules so the current governed profile can supersede the old '
                                               'conversational preference.',
                                               "Keep the first preference forever because memory should preserve the user's original "
                                               'intent across profile updates.',
                                               'Delete the profile address from the source system so the memory store becomes the single '
                                               'source of truth.',
                                               'Let the LLM choose between the two values based on whichever wording appears more '
                                               'confident in context.'],
                                   'answer_index': 0,
                                   'explanation': 'Persistent memory needs conflict and freshness policy.',
                                   'is_critical': False,
                                   'id': 'mcq_04'},
                                  {'kind': 'Architecture',
                                   'question': 'Which metadata is most useful for a retrieved persistent memory?',
                                   'options': ['Source, owner or subject, timestamp/version, scope and confidence/verification status '
                                               'where applicable.',
                                               'Only token count and embedding dimension, because semantic similarity is the main '
                                               'determinant of trust.',
                                               'Only the model version that created the memory, because newer model versions make older '
                                               'facts invalid.',
                                               'Only the original prompt text, because downstream agents can infer provenance and '
                                               'freshness from language.'],
                                   'answer_index': 0,
                                   'explanation': 'Provenance metadata supports trust decisions.',
                                   'is_critical': False,
                                   'id': 'mcq_05'},
                                  {'kind': 'Scenario',
                                   'question': 'A retrieval search returns two conflicting policy snippets, one current and one expired. '
                                               'What should the agent do?',
                                   'options': ['Use version/effective-date metadata to select the authoritative current source or escalate '
                                               'the conflict.',
                                               'Use both snippets and ask the model to synthesize a compromise policy that covers the two '
                                               'versions.',
                                               'Choose the longer snippet because it likely contains the most complete interpretation of '
                                               'the policy.',
                                               'Choose the snippet with the higher semantic similarity score even if its effective date '
                                               'has expired.'],
                                   'answer_index': 0,
                                   'explanation': 'Authority and freshness outrank similarity alone.',
                                   'is_critical': False,
                                   'id': 'mcq_06'},
                                  {'kind': 'Trap',
                                   'question': 'Which statement about memory is most accurate?',
                                   'options': ['Memory supplies context; critical actions should still verify facts against the '
                                               'appropriate source of truth.',
                                               'Memory makes repeated authorization unnecessary because the agent remembers which users '
                                               'were previously approved.',
                                               'Memory should contain every tool response so no information is lost between sessions or '
                                               'model upgrades.',
                                               "Memory is equivalent to the system prompt because both are text injected into the model's "
                                               'context window.'],
                                   'answer_index': 0,
                                   'explanation': 'Memory is contextual and governed.',
                                   'is_critical': False,
                                   'id': 'mcq_07'},
                                  {'kind': 'Scenario',
                                   'question': 'A customer asks the agent to forget a saved preference. What architecture capability is '
                                               'required?',
                                   'options': ['A deletion/update path that removes the governed memory and prevents it from being '
                                               'retrieved again.',
                                               'A prompt that tells the model not to mention the preference even though the memory remains '
                                               'retrievable.',
                                               'A lower retrieval score for the preference so it is less likely, but still possible, to '
                                               'enter context.',
                                               'A new conversation thread because starting fresh guarantees that persistent memory is no '
                                               'longer accessible.'],
                                   'answer_index': 0,
                                   'explanation': 'Retention/deletion must be enforceable.',
                                   'is_critical': False,
                                   'id': 'mcq_08'},
                                  {'kind': 'Architecture',
                                   'question': 'Why should raw tool outputs not automatically become permanent memory?',
                                   'options': ['They may contain transient, sensitive or incorrect information whose lifetime and '
                                               'authority differ from persistent facts.',
                                               'They consume model tokens, and permanent memory is useful only when it contains short '
                                               'natural-language summaries.',
                                               'They prevent embeddings from being generated consistently because API outputs use '
                                               'structured rather than textual data.',
                                               'They reduce model creativity because future runs see too many factual constraints from '
                                               'earlier successful tool calls.'],
                                   'answer_index': 0,
                                   'explanation': 'Persistence requires deliberate policy.',
                                   'is_critical': False,
                                   'id': 'mcq_09'},
                                  {'kind': 'Scenario',
                                   'question': 'An agent remembers that a user prefers supplier A, but supplier A now violates a mandatory '
                                               'compliance rule. What should happen?',
                                   'options': ['Treat the preference as lower-authority context and enforce the current compliance rule '
                                               'before any recommendation.',
                                               'Follow the remembered preference because explicit user history should override changing '
                                               'procurement governance.',
                                               'Recommend supplier A but add a disclaimer, since the agent should not alter stored '
                                               'preferences automatically.',
                                               "Delete the compliance rule from retrieval context so the model can honor the user's "
                                               'persistent preference consistently.'],
                                   'answer_index': 0,
                                   'explanation': 'Policy authority overrides preference.',
                                   'is_critical': False,
                                   'id': 'mcq_10'}],
             'evidence_tasks': [{'question_id': 'q1',
                                 'type': 'architect_decision',
                                 'label': 'Short architect response',
                                 'purpose': 'Demonstrate the mechanism in one concrete scenario, then name one specific risk and one '
                                            'implementable control.',
                                 'question': 'In 80-140 words, explain Agent memory, retrieval and state using one business or engineering '
                                             'example. Include the mechanism, one risk and one control.',
                                 'expected_focus': ['mechanism', 'example', 'risk', 'control'],
                                 'response_shape': 'Mechanism → concrete example → specific risk → implementable control.',
                                 'target_min_words': 80,
                                 'target_max_words': 140,
                                 'sample_answer': 'Agent state and memory should be separated by purpose. Working state stores the current '
                                                  'task, such as verified user, order ID and latest tool result. Longer-term memory stores '
                                                  'approved reusable context, while retrieval brings authoritative knowledge into the '
                                                  'current task when needed. For example, a procurement agent may remember an approved '
                                                  'supplier preference but must retrieve the current order status from the source system. '
                                                  'A risk is stale or cross-user memory leaking into a decision. I would scope memory by '
                                                  'user and task, record provenance and freshness, apply retention limits, and prefer the '
                                                  'authoritative source when stored memory conflicts with current data.'}],
             'written_rubric': {'required': [{'id': 'mechanism',
                                              'label': 'Memory/state mechanism',
                                              'description': 'Separates current state/memory/retrieval or explains how context is carried.',
                                              'phrases_any': ['memory', 'state', 'retriev', 'context', 'previous', 'session', 'persistent'],
                                              'token_groups_all': []},
                                             {'id': 'example',
                                              'label': 'Concrete example',
                                              'description': 'Uses a business or engineering memory example.',
                                              'phrases_any': ['order',
                                                              'customer',
                                                              'supplier',
                                                              'profile',
                                                              'for example',
                                                              'scenario',
                                                              'agent'],
                                              'token_groups_all': []},
                                             {'id': 'risk',
                                              'label': 'Specific risk',
                                              'description': 'Names stale, cross-user, privacy or poisoned context.',
                                              'phrases_any': ['stale',
                                                              'cross-user',
                                                              'leak',
                                                              'wrong',
                                                              'privacy',
                                                              'poison',
                                                              'conflict',
                                                              'expired'],
                                              'token_groups_all': []},
                                             {'id': 'control',
                                              'label': 'Operating control',
                                              'description': 'Names scoping, provenance, TTL/freshness, source-of-truth or retention.',
                                              'phrases_any': ['scope',
                                                              'provenance',
                                                              'ttl',
                                                              'fresh',
                                                              'source of truth',
                                                              'retention',
                                                              'delete',
                                                              'authoritative',
                                                              'permission'],
                                              'token_groups_all': []}],
                                'bonus': [{'id': 'authority',
                                           'label': 'Authority',
                                           'description': 'Distinguishes memory from source of truth.',
                                           'phrases_any': ['source of truth', 'authoritative', 'refresh'],
                                           'token_groups_all': []},
                                          {'id': 'retention',
                                           'label': 'Retention',
                                           'description': 'Mentions deletion or retention policy.',
                                           'phrases_any': ['retention', 'delete', 'forget'],
                                           'token_groups_all': []}]},
             'sample_answer': 'Agent state and memory should be separated by purpose. Working state stores the current task, such as '
                              'verified user, order ID and latest tool result. Longer-term memory stores approved reusable context, while '
                              'retrieval brings authoritative knowledge into the current task when needed. For example, a procurement '
                              'agent may remember an approved supplier preference but must retrieve the current order status from the '
                              'source system. A risk is stale or cross-user memory leaking into a decision. I would scope memory by user '
                              'and task, record provenance and freshness, apply retention limits, and prefer the authoritative source when '
                              'stored memory conflicts with current data.',
             'mastery_repair_prompts': ['Can I state the mechanism without hiding behind generic AI vocabulary?',
                                        'Can I name a concrete failure that could happen in this exact scenario?',
                                        'Can I name an implementable control and what it blocks, limits or escalates?',
                                        'Can I state the stop, fallback or escalation behavior when evidence is insufficient?'],
             'is_gate': False,
             'assessment_principle': 'Normal lesson scoring is deterministic. MCQs use stable answer IDs and a published pass rule. The '
                                     'written response is scored only against the published mechanism, example, risk and control rubric. '
                                     'No hidden architecture vocabulary, essay-length preference or generic governance template may change '
                                     'the result.',
             'answer_quality_bar': {'three_star': 'Mechanism + concrete example + one specific risk + one implementable control.',
                                    'four_star': 'Adds evidence, tool boundary, stop condition or escalation behavior that is relevant to '
                                                 'the scenario.',
                                    'five_star': 'Adds multiple relevant operating details without adding unrelated architecture '
                                                 'vocabulary.'}},
 'aia_007': {'design_version': 'mlos_v4_deterministic_agentic_2026_08_17',
             'assessment_mode': 'v4_deterministic_mcq_plus_published_rubric',
             'topic_id': 'aia_007',
             'title': 'Human checkpoints, approval and escalation',
             'learning_objective': 'Place human decision gates where agent uncertainty, impact or irreversibility exceeds the authority '
                                   'delegated to automation.',
             'prerequisite_bridge': 'Start from the agentic system behavior. Peel down only when a deeper mechanism explains a design '
                                    'decision or failure.',
             'concept_steps': [{'heading': '1. Risk-based checkpoint',
                                'body': 'Not every tool call needs a human. Define which actions can run automatically and which must '
                                        'pause based on impact, value, confidence/evidence or policy.'},
                               {'heading': '2. Approval packet',
                                'body': 'The reviewer needs the proposed action, relevant evidence, affected object, expected effect and '
                                        'reason for the gate.'},
                               {'heading': '3. Binding decision',
                                'body': 'Approval authorises a specific action. Rejection, modification and timeout are durable workflow '
                                        'states and must not be bypassed by replanning.'},
                               {'heading': '4. Escalation',
                                'body': 'Escalation is for ambiguity, missing evidence, repeated failure or authority gaps. It routes the '
                                        'task to a named role or queue with enough context to continue safely.'},
                               {'heading': '5. Architect translation',
                                'body': 'Specify trigger, approver role, evidence packet, SLA/timeout, action scope, audit event, '
                                        'rejection path and escalation target.'}],
             'concept_map': [],
             'worked_example': {'scenario': 'A claims agent may retrieve policy and calculate an indicative amount automatically, but a '
                                            'payment above ₹50,000 pauses with evidence for a claims manager. Rejection stops payment; '
                                            'missing approval after the SLA escalates to the duty manager.',
                                'takeaway': "A checkpoint is an enforceable workflow transition, not a conversational suggestion to 'ask a "
                                            "human'."},
             'worked_examples': [{'title': 'Architect readout',
                                  'body': 'A claims agent may retrieve policy and calculate an indicative amount automatically, but a '
                                          'payment above ₹50,000 pauses with evidence for a claims manager. Rejection stops payment; '
                                          'missing approval after the SLA escalates to the duty manager. The design point is: Risk-tier '
                                          'actions and model uncertainty, then implement pre-execution approval with scoped authorization, '
                                          'durable decision state, audit logs and escalation SLAs.'}],
             'code_bridge': {},
             'misconception': "Adding 'human in the loop' as a vague statement without trigger, authority, evidence, timeout or rejection "
                              'behavior.',
             'architect_extension': 'Risk-tier actions and model uncertainty, then implement pre-execution approval with scoped '
                                    'authorization, durable decision state, audit logs and escalation SLAs.',
             'diagnostic_drill': {'question': "The agent's approval request times out. Is silence approval?",
                                  'reveal': 'No. Timeout follows an explicit safe-stop or escalation path.'},
             'knowledge_checks': [{'kind': 'Critical',
                                   'question': 'Which action is the strongest candidate for a mandatory human checkpoint?',
                                   'options': ["Changing a customer's bank account before a high-value payment is released.",
                                               'Reading a public product catalog to answer an availability question.',
                                               'Formatting an already-approved order status into a user-facing response.',
                                               'Searching an internal knowledge base for a troubleshooting article.'],
                                   'answer_index': 0,
                                   'explanation': 'Irreversible/high-impact financial data changes warrant approval.',
                                   'is_critical': True,
                                   'id': 'mcq_01'},
                                  {'kind': 'Critical',
                                   'question': 'What should an approval record authorize?',
                                   'options': ['A specific proposed action against a defined object and scope, supported by the reviewed '
                                               'evidence.',
                                               "All future actions of the same tool because the reviewer has already validated the agent's "
                                               'judgment once.',
                                               'The entire remaining agent plan so no further checkpoints are needed if the plan changes '
                                               'during execution.',
                                               'Any action whose model confidence is at least as high as the action that the reviewer '
                                               'originally approved.'],
                                   'answer_index': 0,
                                   'explanation': 'Approval must be scoped.',
                                   'is_critical': True,
                                   'id': 'mcq_02'},
                                  {'kind': 'Critical',
                                   'question': 'A reviewer rejects a supplier-bank change. The planner discovers a different API that can '
                                               'make the same change. What should happen?',
                                   'options': ['The rejected business action remains blocked; replanning must not bypass the approval '
                                               'decision.',
                                               'The new API may execute because the rejection applied only to the original tool '
                                               'invocation.',
                                               "The model should compare its confidence with the reviewer's decision and choose whichever "
                                               'is higher.',
                                               'The agent should wait briefly and then retry through the new API because business state '
                                               'may have changed.'],
                                   'answer_index': 0,
                                   'explanation': 'Approval/rejection binds the intended action, not just one tool.',
                                   'is_critical': True,
                                   'id': 'mcq_03'},
                                  {'kind': 'Scenario',
                                   'question': 'A low-risk read-only request has complete evidence and no policy exception. What is the '
                                               'best use of human checkpoints?',
                                   'options': ['Allow the read automatically if policy permits; reserve human attention for defined '
                                               'higher-risk or ambiguous cases.',
                                               'Require a human for every tool call because any LLM action is probabilistic and therefore '
                                               'equally risky.',
                                               'Skip all checkpoints in the session once one read-only action has succeeded without an '
                                               'incident.',
                                               'Ask a human only after the final answer if the user complains that the returned '
                                               'information was incorrect.'],
                                   'answer_index': 0,
                                   'explanation': 'Human attention should be risk-based.',
                                   'is_critical': False,
                                   'id': 'mcq_04'},
                                  {'kind': 'Architecture',
                                   'question': 'Which approval packet is most useful to a reviewer?',
                                   'options': ['Action, affected record, relevant evidence, policy/risk trigger and exact consequence of '
                                               'approval.',
                                               'Only the model recommendation and confidence score so the reviewer is not biased by raw '
                                               'evidence.',
                                               'The entire model context and every retrieved document, regardless of relevance to the '
                                               'requested action.',
                                               'Only the original user request because reviewing tool outputs would make the checkpoint '
                                               'too slow.'],
                                   'answer_index': 0,
                                   'explanation': 'Reviewers need decision-relevant evidence.',
                                   'is_critical': False,
                                   'id': 'mcq_05'},
                                  {'kind': 'Scenario',
                                   'question': 'An agent cannot verify whether the requester is authorised to see a contract. What is the '
                                               'proper escalation trigger?',
                                   'options': ['Missing authorization evidence before disclosure, routed to the defined identity or '
                                               'contract owner.',
                                               'Low model confidence after disclosure, routed to a reviewer if the user challenges the '
                                               'answer.',
                                               'High latency in the retrieval API, routed directly to the finance approver responsible for '
                                               'payments.',
                                               'Any request with more than one document, routed to a human because multi-document tasks '
                                               'are always high risk.'],
                                   'answer_index': 0,
                                   'explanation': 'Escalation should map to the actual authority/evidence gap.',
                                   'is_critical': False,
                                   'id': 'mcq_06'},
                                  {'kind': 'Trap',
                                   'question': "Which statement best describes 'human in the loop'?",
                                   'options': ['It is an explicit workflow policy with triggers, authority, evidence and post-decision '
                                               'behavior.',
                                               "It is satisfied whenever the agent's final message recommends that a user verify important "
                                               'information.',
                                               'It means every model output is manually reviewed, regardless of action risk or available '
                                               'automation controls.',
                                               'It is mainly a prompt technique that asks the model to imagine what a human reviewer would '
                                               'decide.'],
                                   'answer_index': 0,
                                   'explanation': 'HITL is a workflow control.',
                                   'is_critical': False,
                                   'id': 'mcq_07'},
                                  {'kind': 'Scenario',
                                   'question': 'A payment approval expires after 30 minutes because underlying exchange-rate data changes. '
                                               'What should the system do?',
                                   'options': ['Require revalidation and, if policy says so, a new approval tied to the refreshed '
                                               'transaction evidence.',
                                               'Reuse the old approval because the reviewer approved the business intent, not the exact '
                                               'transaction state.',
                                               'Execute immediately before the exchange rate changes again because delay increases '
                                               'operational risk.',
                                               'Ask the model whether the changed rate is material enough to invalidate the previous '
                                               'approval.'],
                                   'answer_index': 0,
                                   'explanation': 'Approvals can be evidence/version scoped.',
                                   'is_critical': False,
                                   'id': 'mcq_08'},
                                  {'kind': 'Architecture',
                                   'question': 'What should happen when an approval SLA expires without a response?',
                                   'options': ['Move to the defined timeout state, such as safe stop or escalation to a named backup role.',
                                               'Auto-approve because the absence of rejection should not block a time-sensitive automated '
                                               'workflow.',
                                               'Reset the approval timer indefinitely so the task remains active until the original '
                                               'reviewer eventually responds.',
                                               'Remove the checkpoint and continue with enhanced logging because auditability compensates '
                                               'for the missing decision.'],
                                   'answer_index': 0,
                                   'explanation': 'Timeout behavior must be explicit.',
                                   'is_critical': False,
                                   'id': 'mcq_09'},
                                  {'kind': 'Scenario',
                                   'question': 'Which metric best shows whether human checkpoints are well placed?',
                                   'options': ['Approval volume, approval/rejection rate, escalation reasons, latency and incidents by '
                                               'action-risk tier.',
                                               'Total prompt tokens, because higher token use indicates the model needed more human '
                                               'judgment.',
                                               'Number of tools registered, because more tools necessarily require proportionally more '
                                               'approvals.',
                                               'Average final-answer length, because concise answers correlate with fewer human '
                                               'interventions.'],
                                   'answer_index': 0,
                                   'explanation': 'Checkpoint performance should be observed by risk and outcome.',
                                   'is_critical': False,
                                   'id': 'mcq_10'}],
             'evidence_tasks': [{'question_id': 'q1',
                                 'type': 'architect_decision',
                                 'label': 'Short architect response',
                                 'purpose': 'Demonstrate the mechanism in one concrete scenario, then name one specific risk and one '
                                            'implementable control.',
                                 'question': 'In 80-140 words, explain Human checkpoints, approval and escalation using one business or '
                                             'engineering example. Include the mechanism, one risk and one control.',
                                 'expected_focus': ['mechanism', 'example', 'risk', 'control'],
                                 'response_shape': 'Mechanism → concrete example → specific risk → implementable control.',
                                 'target_min_words': 80,
                                 'target_max_words': 140,
                                 'sample_answer': 'A human checkpoint is a pre-execution decision gate used when an agent reaches an '
                                                  'action whose impact or uncertainty exceeds its delegated authority. For example, a '
                                                  'procurement agent may prepare a supplier-bank change, but the runtime pauses before '
                                                  'execution and sends the proposed change, evidence and requester identity to an '
                                                  'authorised reviewer. A risk is an incorrect or unauthorised financial change becoming '
                                                  'irreversible. I would define the approval trigger, reviewer role, required evidence and '
                                                  'timeout path in policy. Until approval is recorded, the action remains blocked. '
                                                  'Rejection or missing approval causes a safe stop or escalation rather than automatic '
                                                  'execution.'}],
             'written_rubric': {'required': [{'id': 'mechanism',
                                              'label': 'Checkpoint mechanism',
                                              'description': 'Explains pre-execution approval/escalation for risk/uncertainty.',
                                              'phrases_any': ['checkpoint',
                                                              'approval',
                                                              'human',
                                                              'escalat',
                                                              'review',
                                                              'before execute',
                                                              'pause'],
                                              'token_groups_all': []},
                                             {'id': 'example',
                                              'label': 'Concrete example',
                                              'description': 'Uses a business or engineering approval example.',
                                              'phrases_any': ['payment',
                                                              'refund',
                                                              'bank',
                                                              'supplier',
                                                              'claim',
                                                              'order',
                                                              'for example',
                                                              'scenario'],
                                              'token_groups_all': []},
                                             {'id': 'risk',
                                              'label': 'Specific risk',
                                              'description': 'Names high-impact/unauthorised/irreversible action or missing evidence.',
                                              'phrases_any': ['unauthor',
                                                              'high-value',
                                                              'irreversible',
                                                              'wrong',
                                                              'missing evidence',
                                                              'financial',
                                                              'disclos',
                                                              'bank'],
                                              'token_groups_all': []},
                                             {'id': 'control',
                                              'label': 'Operating control',
                                              'description': 'Names trigger, reviewer, evidence or binding approval behavior.',
                                              'phrases_any': ['trigger',
                                                              'approver',
                                                              'reviewer',
                                                              'approval',
                                                              'evidence',
                                                              'blocked',
                                                              'timeout',
                                                              'escalat',
                                                              'role'],
                                              'token_groups_all': []}],
                                'bonus': [{'id': 'timeout',
                                           'label': 'Timeout',
                                           'description': 'Defines timeout/SLA behavior.',
                                           'phrases_any': ['timeout', 'sla', 'expire'],
                                           'token_groups_all': []},
                                          {'id': 'scope',
                                           'label': 'Approval scope',
                                           'description': 'Scopes approval to action/evidence.',
                                           'phrases_any': ['specific action', 'scope', 'record', 'transaction'],
                                           'token_groups_all': []}]},
             'sample_answer': 'A human checkpoint is a pre-execution decision gate used when an agent reaches an action whose impact or '
                              'uncertainty exceeds its delegated authority. For example, a procurement agent may prepare a supplier-bank '
                              'change, but the runtime pauses before execution and sends the proposed change, evidence and requester '
                              'identity to an authorised reviewer. A risk is an incorrect or unauthorised financial change becoming '
                              'irreversible. I would define the approval trigger, reviewer role, required evidence and timeout path in '
                              'policy. Until approval is recorded, the action remains blocked. Rejection or missing approval causes a safe '
                              'stop or escalation rather than automatic execution.',
             'mastery_repair_prompts': ['Can I state the mechanism without hiding behind generic AI vocabulary?',
                                        'Can I name a concrete failure that could happen in this exact scenario?',
                                        'Can I name an implementable control and what it blocks, limits or escalates?',
                                        'Can I state the stop, fallback or escalation behavior when evidence is insufficient?'],
             'is_gate': False,
             'assessment_principle': 'Normal lesson scoring is deterministic. MCQs use stable answer IDs and a published pass rule. The '
                                     'written response is scored only against the published mechanism, example, risk and control rubric. '
                                     'No hidden architecture vocabulary, essay-length preference or generic governance template may change '
                                     'the result.',
             'answer_quality_bar': {'three_star': 'Mechanism + concrete example + one specific risk + one implementable control.',
                                    'four_star': 'Adds evidence, tool boundary, stop condition or escalation behavior that is relevant to '
                                                 'the scenario.',
                                    'five_star': 'Adds multiple relevant operating details without adding unrelated architecture '
                                                 'vocabulary.'}},
 'aia_008': {'design_version': 'mlos_v4_deterministic_agentic_2026_08_17',
             'assessment_mode': 'v4_deterministic_mcq_plus_published_rubric',
             'topic_id': 'aia_008',
             'title': 'Agent evaluation: task success, groundedness and safety',
             'learning_objective': 'Evaluate an agent on the full task trajectory: whether it achieved the requested outcome, used '
                                   'evidence correctly, invoked tools safely, respected policy and met operational cost/latency '
                                   'constraints.',
             'prerequisite_bridge': 'Start from the agentic system behavior. Peel down only when a deeper mechanism explains a design '
                                    'decision or failure.',
             'concept_steps': [{'heading': '1. Task success',
                                'body': 'Define an observable success condition in the target system or workflow, not merely a fluent '
                                        'final answer.'},
                               {'heading': '2. Groundedness',
                                'body': 'Claims and decisions should be supported by authoritative retrieved or tool evidence. Evaluation '
                                        'should catch fabricated or unsupported facts.'},
                               {'heading': '3. Tool and safety behavior',
                                'body': 'Inspect tool selection, parameters, permissions, side effects, approvals and stop behavior across '
                                        'the trajectory.'},
                               {'heading': '4. Scenario eval sets',
                                'body': 'Use representative normal, edge, adversarial and failure scenarios. Include tool errors, missing '
                                        'data, ambiguous identity and approval rejection.'},
                               {'heading': '5. Production monitoring',
                                'body': 'Track task success, human overrides, policy violations, latency, token/tool cost and failure '
                                        'patterns after release.'}],
             'concept_map': [],
             'worked_example': {'scenario': 'For an order agent, an eval checks whether the correct authorised status was returned, the '
                                            'status came from the order API, no unrelated customer data was accessed, and the agent '
                                            'stopped safely when the order ID was ambiguous.',
                                'takeaway': 'A correct final sentence is not enough if the trajectory was unsafe or unsupported.'},
             'worked_examples': [{'title': 'Architect readout',
                                  'body': 'For an order agent, an eval checks whether the correct authorised status was returned, the '
                                          'status came from the order API, no unrelated customer data was accessed, and the agent stopped '
                                          'safely when the order ID was ambiguous. The design point is: Build versioned scenario suites, '
                                          'trace assertions, source-grounding checks, action-policy tests, human-review samples and '
                                          'production outcome monitoring.'}],
             'code_bridge': {},
             'misconception': 'Evaluating an agent only on response fluency or one happy-path demo.',
             'architect_extension': 'Build versioned scenario suites, trace assertions, source-grounding checks, action-policy tests, '
                                    'human-review samples and production outcome monitoring.',
             'diagnostic_drill': {'question': 'The final answer is correct but the agent first queried an unauthorised account. Pass or '
                                              'fail?',
                                  'reveal': 'Fail the safety criterion. Agent evaluation must inspect the trajectory, not only the final '
                                            'text.'},
             'knowledge_checks': [{'kind': 'Critical',
                                   'question': 'Which metric most directly measures task success for an order-cancellation agent?',
                                   'options': ['Percentage of eligible cancellation requests that end in the correct verified order state.',
                                               'Average similarity between the final response and a reference cancellation explanation.',
                                               'Average number of tool calls, because more tool use indicates more complete task '
                                               'execution.',
                                               "Percentage of responses containing the words 'cancelled' and 'confirmed' in the final "
                                               'message.'],
                                   'answer_index': 0,
                                   'explanation': 'Success should be tied to target-system outcome.',
                                   'is_critical': True,
                                   'id': 'mcq_01'},
                                  {'kind': 'Critical',
                                   'question': 'An agent states a delivery date that is not present in retrieved policy or tool data. '
                                               'Which evaluation dimension failed?',
                                   'options': ['Groundedness, because the claim is unsupported by the available authoritative evidence.',
                                               'Latency, because unsupported claims usually occur when the model answers too quickly.',
                                               'Tool coverage, because every final claim must come from a different registered tool.',
                                               'Task decomposition, because any incorrect fact proves the original plan had too few '
                                               'steps.'],
                                   'answer_index': 0,
                                   'explanation': 'Groundedness measures evidence support.',
                                   'is_critical': True,
                                   'id': 'mcq_02'},
                                  {'kind': 'Critical',
                                   'question': 'The final response is correct, but the agent attempted an unauthorised refund before being '
                                               'blocked. How should the run score?',
                                   'options': ['Task success may pass, but the safety/tool-policy criterion must fail for the trajectory.',
                                               'The entire run should pass because the policy layer successfully blocked the unsafe call.',
                                               'The run should pass if the refund attempt did not create an actual financial side effect.',
                                               'The run should be judged only on the final response because blocked actions are not part '
                                               'of user-visible behavior.'],
                                   'answer_index': 0,
                                   'explanation': 'Evaluation should score separate dimensions.',
                                   'is_critical': True,
                                   'id': 'mcq_03'},
                                  {'kind': 'Scenario',
                                   'question': 'Which eval-set case best tests recovery rather than only happy-path accuracy?',
                                   'options': ['The order API times out after a read; the agent must retry within policy or escalate '
                                               'without inventing status.',
                                               'The order API returns the expected record and the agent provides the correct status in one '
                                               'step.',
                                               'The user asks a common status question using the exact wording seen in development '
                                               'examples.',
                                               'The agent receives a short prompt and returns a concise response within the target '
                                               'latency.'],
                                   'answer_index': 0,
                                   'explanation': 'Failure injection tests recovery.',
                                   'is_critical': False,
                                   'id': 'mcq_04'},
                                  {'kind': 'Architecture',
                                   'question': 'Why version an agent evaluation suite?',
                                   'options': ['So changes in model, prompts, tools or policies can be compared against the same '
                                               'controlled scenarios over time.',
                                               'So the model learns the expected answers from prior evaluation runs and becomes more '
                                               'deterministic.',
                                               'So only the latest model version needs production monitoring because older scenario '
                                               'results remain valid indefinitely.',
                                               'So every deployment can use a different scenario set without keeping backward-comparable '
                                               'evidence.'],
                                   'answer_index': 0,
                                   'explanation': 'Versioned evals enable comparable release evidence.',
                                   'is_critical': False,
                                   'id': 'mcq_05'},
                                  {'kind': 'Scenario',
                                   'question': "A grounded answer uses the right policy but applies it to the wrong customer's account. "
                                               'Which evaluation should catch this?',
                                   'options': ['Identity/authorization and task-correctness checks, because correct source citation does '
                                               'not prove correct subject scope.',
                                               'Groundedness alone, because any cited authoritative source guarantees the action is '
                                               'associated with the right user.',
                                               'Latency, because account mismatches are usually caused by slow retrieval and stale model '
                                               'context.',
                                               'Cost, because querying the wrong account increases tool calls and therefore makes the '
                                               'mistake economically visible.'],
                                   'answer_index': 0,
                                   'explanation': 'Grounding is necessary but not sufficient.',
                                   'is_critical': False,
                                   'id': 'mcq_06'},
                                  {'kind': 'Trap',
                                   'question': 'Which statement about LLM-as-judge evaluation is safest?',
                                   'options': ['It can help with nuanced semantic review, but critical policy and tool assertions should '
                                               'also use deterministic checks.',
                                               'It should replace deterministic checks because a capable judge can understand every policy '
                                               'exception from context.',
                                               'It should be used only for latency and cost because semantic quality is better measured '
                                               'with exact string matching.',
                                               'It guarantees unbiased grading if the judge model differs from the model used by the '
                                               'production agent.'],
                                   'answer_index': 0,
                                   'explanation': 'Use deterministic checks for enforceable criteria.',
                                   'is_critical': False,
                                   'id': 'mcq_07'},
                                  {'kind': 'Scenario',
                                   'question': "An agent's task success is stable, but average tool calls per success doubles after a "
                                               'prompt change. What should be investigated?',
                                   'options': ['Trajectory efficiency, retry loops and unnecessary planning steps before accepting the '
                                               'change.',
                                               'Only the final response style, because task success proves the workflow itself is still '
                                               'healthy.',
                                               'Only model accuracy, because tool-call count is irrelevant when the outcome remains '
                                               'correct.',
                                               'Only infrastructure cost, because additional tool calls cannot affect reliability or '
                                               'side-effect risk.'],
                                   'answer_index': 0,
                                   'explanation': 'Efficiency changes can reveal loop problems.',
                                   'is_critical': False,
                                   'id': 'mcq_08'},
                                  {'kind': 'Architecture',
                                   'question': 'What production signal complements offline agent evals?',
                                   'options': ['Real task outcomes, human overrides, policy blocks, failure reasons, latency and cost by '
                                               'scenario or action type.',
                                               'Only model-provider uptime, because offline evals already cover all behavior after the '
                                               'service is available.',
                                               'Only token count, because production quality is difficult to observe without labelled '
                                               'benchmark answers.',
                                               'Only user thumbs-up rate, because direct user preference is the most complete measure of '
                                               'safety and correctness.'],
                                   'answer_index': 0,
                                   'explanation': 'Production monitoring needs multiple outcome/behavior signals.',
                                   'is_critical': False,
                                   'id': 'mcq_09'},
                                  {'kind': 'Scenario',
                                   'question': 'A test suite contains 100 routine cases and no cases for ambiguous identity, tool timeout '
                                               'or approval rejection. What is the main weakness?',
                                   'options': ['The scenario distribution misses important failure modes, so the release evidence is '
                                               'over-optimistic.',
                                               'The suite is too large because routine cases should be replaced entirely by adversarial '
                                               'scenarios.',
                                               'The suite is invalid because agent evaluation should use only real production '
                                               'conversations, never synthetic cases.',
                                               'The suite is sufficient if the routine-case pass rate is 100%, because edge cases can be '
                                               'monitored after release.'],
                                   'answer_index': 0,
                                   'explanation': 'Representative failure cases are essential.',
                                   'is_critical': False,
                                   'id': 'mcq_10'}],
             'evidence_tasks': [{'question_id': 'q1',
                                 'type': 'architect_decision',
                                 'label': 'Short architect response',
                                 'purpose': 'Demonstrate the mechanism in one concrete scenario, then name one specific risk and one '
                                            'implementable control.',
                                 'question': 'In 80-140 words, explain Agent evaluation: task success, groundedness and safety using one '
                                             'business or engineering example. Include the mechanism, one risk and one control.',
                                 'expected_focus': ['mechanism', 'example', 'risk', 'control'],
                                 'response_shape': 'Mechanism → concrete example → specific risk → implementable control.',
                                 'target_min_words': 80,
                                 'target_max_words': 140,
                                 'sample_answer': 'Agent evaluation should test the full task trajectory, not only whether the final text '
                                                  'sounds correct. For an order-support agent, I would check whether it reached the '
                                                  'requested outcome, used authoritative evidence, invoked permitted tools, respected '
                                                  'approvals, recovered from failures, and stayed within latency and cost limits. A '
                                                  'specific risk is a fluent answer that reports an order status the tools never verified '
                                                  'or that hides an unsafe tool call. I would use versioned scenario tests with '
                                                  'deterministic policy assertions and trace inspection, including ambiguous and failure '
                                                  'cases. Production monitoring should track task success, groundedness, policy '
                                                  'violations, tool errors, cost and latency.'}],
             'written_rubric': {'required': [{'id': 'mechanism',
                                              'label': 'Evaluation mechanism',
                                              'description': 'Explains task/trajectory evaluation, groundedness or tool/safety checks.',
                                              'phrases_any': ['task success',
                                                              'grounded',
                                                              'evaluation',
                                                              'eval',
                                                              'trajectory',
                                                              'tool',
                                                              'safety'],
                                              'token_groups_all': []},
                                             {'id': 'example',
                                              'label': 'Concrete example',
                                              'description': 'Uses a business or engineering agent-eval example.',
                                              'phrases_any': ['order', 'customer', 'refund', 'support', 'for example', 'scenario', 'agent'],
                                              'token_groups_all': []},
                                             {'id': 'risk',
                                              'label': 'Specific risk',
                                              'description': 'Names unsupported, unsafe or missed failure behavior.',
                                              'phrases_any': ['hallucinat',
                                                              'unsupported',
                                                              'unauthor',
                                                              'unsafe',
                                                              'wrong',
                                                              'happy path',
                                                              'failure',
                                                              'ambiguous'],
                                              'token_groups_all': []},
                                             {'id': 'control',
                                              'label': 'Operating control',
                                              'description': 'Names scenario tests, trace checks, policy assertions or monitoring.',
                                              'phrases_any': ['scenario',
                                                              'trace',
                                                              'deterministic',
                                                              'monitor',
                                                              'policy',
                                                              'test',
                                                              'assert',
                                                              'grounding'],
                                              'token_groups_all': []}],
                                'bonus': [{'id': 'multi_metric',
                                           'label': 'Multiple dimensions',
                                           'description': 'Separates task success from groundedness/safety/cost.',
                                           'phrases_any': ['task success', 'grounded', 'safety', 'cost', 'latency'],
                                           'token_groups_all': []},
                                          {'id': 'production',
                                           'label': 'Production monitoring',
                                           'description': 'Mentions live outcome/override monitoring.',
                                           'phrases_any': ['production', 'override', 'monitor'],
                                           'token_groups_all': []}]},
             'sample_answer': 'Agent evaluation should test the full task trajectory, not only whether the final text sounds correct. For '
                              'an order-support agent, I would check whether it reached the requested outcome, used authoritative '
                              'evidence, invoked permitted tools, respected approvals, recovered from failures, and stayed within latency '
                              'and cost limits. A specific risk is a fluent answer that reports an order status the tools never verified '
                              'or that hides an unsafe tool call. I would use versioned scenario tests with deterministic policy '
                              'assertions and trace inspection, including ambiguous and failure cases. Production monitoring should track '
                              'task success, groundedness, policy violations, tool errors, cost and latency.',
             'mastery_repair_prompts': ['Can I state the mechanism without hiding behind generic AI vocabulary?',
                                        'Can I name a concrete failure that could happen in this exact scenario?',
                                        'Can I name an implementable control and what it blocks, limits or escalates?',
                                        'Can I state the stop, fallback or escalation behavior when evidence is insufficient?'],
             'is_gate': False,
             'assessment_principle': 'Normal lesson scoring is deterministic. MCQs use stable answer IDs and a published pass rule. The '
                                     'written response is scored only against the published mechanism, example, risk and control rubric. '
                                     'No hidden architecture vocabulary, essay-length preference or generic governance template may change '
                                     'the result.',
             'answer_quality_bar': {'three_star': 'Mechanism + concrete example + one specific risk + one implementable control.',
                                    'four_star': 'Adds evidence, tool boundary, stop condition or escalation behavior that is relevant to '
                                                 'the scenario.',
                                    'five_star': 'Adds multiple relevant operating details without adding unrelated architecture '
                                                 'vocabulary.'}},
 'aia_009': {'design_version': 'mlos_v4_deterministic_agentic_2026_08_17',
             'assessment_mode': 'v4_deterministic_mcq_plus_published_rubric',
             'topic_id': 'aia_009',
             'title': 'Multi-agent orchestration and handoffs',
             'learning_objective': 'Use multiple agents only when role separation creates real value, and define handoff contracts, shared '
                                   'state, ownership and failure handling so coordination does not multiply risk.',
             'prerequisite_bridge': 'Start from the agentic system behavior. Peel down only when a deeper mechanism explains a design '
                                    'decision or failure.',
             'concept_steps': [{'heading': '1. Why multiple agents',
                                'body': 'Separate agents can help when tasks require distinct tools, policies, context or specialist '
                                        'reasoning. They are not automatically better than one orchestrated agent.'},
                               {'heading': '2. Handoff contract',
                                'body': 'A handoff defines input state, required evidence, allowed action, expected output and who owns '
                                        'the task after transfer.'},
                               {'heading': '3. Shared state',
                                'body': 'Agents need controlled shared task state or explicit messages. Hidden assumptions and duplicated '
                                        'memory create inconsistent decisions.'},
                               {'heading': '4. Coordination failures',
                                'body': 'Failures include ping-pong routing, lost context, conflicting actions, duplicated side effects '
                                        'and unclear accountability.'},
                               {'heading': '5. Architect translation',
                                'body': 'Define roles, routing criteria, handoff schema, correlation/trace ID, shared state, conflict '
                                        'policy, timeout, owner and end-to-end evaluation.'}],
             'concept_map': [],
             'worked_example': {'scenario': 'A service triage agent classifies a vehicle issue, a diagnostics agent reads fault data, and '
                                            'a warranty agent checks coverage. The orchestrator passes a typed case record between them '
                                            'and owns the final response.',
                                'takeaway': 'Specialists help only when handoffs preserve evidence, state and accountability.'},
             'worked_examples': [{'title': 'Architect readout',
                                  'body': 'A service triage agent classifies a vehicle issue, a diagnostics agent reads fault data, and a '
                                          'warranty agent checks coverage. The orchestrator passes a typed case record between them and '
                                          'owns the final response. The design point is: Prefer the simplest topology that works; use '
                                          'explicit routing, typed handoff contracts, shared state, idempotency, conflict resolution and '
                                          'end-to-end ownership.'}],
             'code_bridge': {},
             'misconception': 'Adding agents because the workflow has multiple steps, without proving that separate roles improve '
                              'capability or control.',
             'architect_extension': 'Prefer the simplest topology that works; use explicit routing, typed handoff contracts, shared state, '
                                    'idempotency, conflict resolution and end-to-end ownership.',
             'diagnostic_drill': {'question': 'Two agents keep handing the same case back to each other. What control is missing?',
                                  'reveal': 'A routing/handoff rule with ownership and a bounded retry/escalation path.'},
             'knowledge_checks': [{'kind': 'Critical',
                                   'question': 'When is a separate specialist agent most justified?',
                                   'options': ['When it needs a distinct tool/policy/context boundary that benefits from explicit role '
                                               'isolation and handoff.',
                                               'Whenever a workflow has more than three steps, because each group of steps should have its '
                                               'own agent.',
                                               'Whenever different prompts improve response variety, even if all agents use the same tools '
                                               'and authority.',
                                               'Whenever latency is important, because multiple agents always execute in parallel and '
                                               'therefore finish faster.'],
                                   'answer_index': 0,
                                   'explanation': 'Multi-agent complexity needs a real boundary/value.',
                                   'is_critical': True,
                                   'id': 'mcq_01'},
                                  {'kind': 'Critical',
                                   'question': 'What should a handoff from a triage agent to a diagnostics agent contain?',
                                   'options': ['A typed task state with case identity, verified evidence, requested action and '
                                               'ownership/return expectations.',
                                               'Only a natural-language summary, because the receiving model can infer missing state from '
                                               'the conversation history.',
                                               "The sending agent's hidden reasoning so the receiver can reconstruct every alternative "
                                               'that was considered.',
                                               'All customer and system data available to the sending agent, because handoffs should '
                                               'preserve maximum context.'],
                                   'answer_index': 0,
                                   'explanation': 'Handoffs should be explicit and minimal.',
                                   'is_critical': True,
                                   'id': 'mcq_02'},
                                  {'kind': 'Critical',
                                   'question': 'Two agents alternately route a case to each other with no progress. Which control directly '
                                               'addresses this?',
                                   'options': ['Bound handoff count and define routing ownership plus an escalation state for unresolved '
                                               'cases.',
                                               "Increase both models' temperature so each agent is less likely to repeat the previous "
                                               'routing decision.',
                                               'Add a third supervisor agent that can also return the case to either specialist without a '
                                               'step limit.',
                                               'Persist longer conversation memory so both agents can see more of the repeated routing '
                                               'history.'],
                                   'answer_index': 0,
                                   'explanation': 'Coordination needs bounded routing and owner.',
                                   'is_critical': True,
                                   'id': 'mcq_03'},
                                  {'kind': 'Scenario',
                                   'question': 'A diagnostics agent and warranty agent both write different statuses to the same case '
                                               'record. What architecture issue is present?',
                                   'options': ['Conflicting write ownership; the workflow needs authoritative state transitions or a '
                                               'conflict-resolution policy.',
                                               'Insufficient prompt detail; both agents should simply be told to agree before they update '
                                               'the record.',
                                               'Too little context window; a larger model context would automatically serialize the two '
                                               'writes correctly.',
                                               "Excessive logging; the shared trace can cause agents to overfit to each other's previous "
                                               'actions.'],
                                   'answer_index': 0,
                                   'explanation': 'Shared-state write ownership must be explicit.',
                                   'is_critical': False,
                                   'id': 'mcq_04'},
                                  {'kind': 'Architecture',
                                   'question': 'What does an orchestrator own in a multi-agent workflow?',
                                   'options': ['Routing, shared task state, handoff policy, termination and end-to-end outcome tracking.',
                                               "Every specialist's internal prompt wording, but not the workflow state after a handoff "
                                               'occurs.',
                                               'Only the first routing decision; after delegation the specialists should coordinate '
                                               'without central policy.',
                                               'Only cost accounting, because specialist agents should independently manage permissions '
                                               'and completion.'],
                                   'answer_index': 0,
                                   'explanation': 'Orchestration owns coordination.',
                                   'is_critical': False,
                                   'id': 'mcq_05'},
                                  {'kind': 'Scenario',
                                   'question': 'A specialist agent fails after creating a side effect, and the orchestrator retries the '
                                               'whole subtask. What control matters?',
                                   'options': ["Idempotent operations or state checks so the retry cannot duplicate the specialist's side "
                                               'effect.',
                                               'Longer handoff messages so the specialist remembers that it probably completed the side '
                                               'effect previously.',
                                               'A different LLM for the retry so the new agent is unlikely to choose exactly the same '
                                               'action sequence.',
                                               'Removal of shared state so each retry begins independently and avoids contamination from '
                                               'the failed run.'],
                                   'answer_index': 0,
                                   'explanation': 'Cross-agent retries need side-effect safety.',
                                   'is_critical': False,
                                   'id': 'mcq_06'},
                                  {'kind': 'Trap',
                                   'question': 'Which statement about multi-agent systems is most accurate?',
                                   'options': ['Additional agents create coordination cost and failure modes, so they need a measurable '
                                               'reason to exist.',
                                               'Additional agents are inherently safer because no single model has to reason about the '
                                               'entire workflow.',
                                               'Additional agents reduce latency because specialist tasks can always run independently in '
                                               'parallel.',
                                               'Additional agents make ownership clearer automatically because each model instance '
                                               'represents a distinct role.'],
                                   'answer_index': 0,
                                   'explanation': 'More agents are not automatically better.',
                                   'is_critical': False,
                                   'id': 'mcq_07'},
                                  {'kind': 'Architecture',
                                   'question': 'Which identifier should follow a case across agent handoffs?',
                                   'options': ['A stable correlation/trace ID linking the end-to-end task, state changes and tool actions.',
                                               'A new independent session ID at every handoff so each specialist has a clean context '
                                               'boundary.',
                                               'The provider request ID only, because every model invocation is the authoritative '
                                               'representation of the workflow.',
                                               'The final user-message ID, because intermediate tool and handoff activity does not need '
                                               'cross-agent correlation.'],
                                   'answer_index': 0,
                                   'explanation': 'End-to-end traces require stable correlation.',
                                   'is_critical': False,
                                   'id': 'mcq_08'},
                                  {'kind': 'Scenario',
                                   'question': 'A triage agent passes raw customer notes to a specialist that needs only a fault code and '
                                               'vehicle ID. What is the better handoff?',
                                   'options': ['Pass the minimum typed fields and evidence required by the specialist, respecting '
                                               'data-access boundaries.',
                                               'Pass the full notes because specialists should always receive the maximum context '
                                               'available to the orchestrator.',
                                               "Store the notes in the specialist's long-term memory so later cases with similar wording "
                                               'can reuse them.',
                                               'Ask the specialist to redact irrelevant data after receiving it because model-based '
                                               'minimization is more flexible.'],
                                   'answer_index': 0,
                                   'explanation': 'Minimize handoff data.',
                                   'is_critical': False,
                                   'id': 'mcq_09'},
                                  {'kind': 'Architecture',
                                   'question': 'How should a multi-agent system be evaluated?',
                                   'options': ['Measure end-to-end task success plus handoff correctness, state consistency, tool safety, '
                                               'latency and cost.',
                                               "Score each agent's final text separately and average the results, regardless of the "
                                               'end-to-end outcome.',
                                               'Evaluate only the orchestrator because specialist errors are implementation details hidden '
                                               'behind delegation.',
                                               'Evaluate only successful handoffs because failures are already captured by production '
                                               'exception logs.'],
                                   'answer_index': 0,
                                   'explanation': 'Coordination quality is part of system quality.',
                                   'is_critical': False,
                                   'id': 'mcq_10'}],
             'evidence_tasks': [{'question_id': 'q1',
                                 'type': 'architect_decision',
                                 'label': 'Short architect response',
                                 'purpose': 'Demonstrate the mechanism in one concrete scenario, then name one specific risk and one '
                                            'implementable control.',
                                 'question': 'In 80-140 words, explain Multi-agent orchestration and handoffs using one business or '
                                             'engineering example. Include the mechanism, one risk and one control.',
                                 'expected_focus': ['mechanism', 'example', 'risk', 'control'],
                                 'response_shape': 'Mechanism → concrete example → specific risk → implementable control.',
                                 'target_min_words': 80,
                                 'target_max_words': 140,
                                 'sample_answer': 'A multi-agent design is useful only when specialist roles create a clear separation of '
                                                  'work. For example, a support workflow might use a triage agent to classify the request '
                                                  'and a diagnostic agent to investigate a technical issue, with an orchestrator '
                                                  'controlling the handoff. A risk is lost context, duplicate actions or two agents '
                                                  'believing they own the same task. I would define a handoff contract containing task ID, '
                                                  'required context, completed evidence, next owner and permitted actions. Shared state is '
                                                  'versioned and traceable, and retries are idempotent. Routing limits and escalation '
                                                  'prevent ping-pong between agents when ownership or evidence is unclear.'}],
             'written_rubric': {'required': [{'id': 'mechanism',
                                              'label': 'Multi-agent mechanism',
                                              'description': 'Explains specialist roles plus orchestration/handoffs.',
                                              'phrases_any': ['multi-agent', 'agent', 'handoff', 'orchestr', 'specialist', 'route', 'role'],
                                              'token_groups_all': []},
                                             {'id': 'example',
                                              'label': 'Concrete example',
                                              'description': 'Uses a business or engineering multi-agent scenario.',
                                              'phrases_any': ['triage',
                                                              'diagnostic',
                                                              'warranty',
                                                              'procurement',
                                                              'support',
                                                              'for example',
                                                              'scenario'],
                                              'token_groups_all': []},
                                             {'id': 'risk',
                                              'label': 'Specific risk',
                                              'description': 'Names coordination, duplication, lost context or ownership risk.',
                                              'phrases_any': ['conflict',
                                                              'duplicate',
                                                              'lost',
                                                              'ping-pong',
                                                              'unclear ownership',
                                                              'wrong route',
                                                              'failure',
                                                              'inconsistent'],
                                              'token_groups_all': []},
                                             {'id': 'control',
                                              'label': 'Operating control',
                                              'description': 'Names handoff contract, shared state, owner, trace, limit or conflict '
                                                             'policy.',
                                              'phrases_any': ['handoff contract',
                                                              'shared state',
                                                              'owner',
                                                              'trace',
                                                              'correlation',
                                                              'limit',
                                                              'escalat',
                                                              'idempot',
                                                              'routing'],
                                              'token_groups_all': []}],
                                'bonus': [{'id': 'simplicity',
                                           'label': 'Simplicity tradeoff',
                                           'description': 'States multiple agents need justification.',
                                           'phrases_any': ['simplest', 'complexity', 'justify', 'only when'],
                                           'token_groups_all': []},
                                          {'id': 'end_to_end',
                                           'label': 'End-to-end',
                                           'description': 'Mentions end-to-end outcome evaluation.',
                                           'phrases_any': ['end-to-end', 'task success', 'handoff correctness'],
                                           'token_groups_all': []}]},
             'sample_answer': 'A multi-agent design is useful only when specialist roles create a clear separation of work. For example, a '
                              'support workflow might use a triage agent to classify the request and a diagnostic agent to investigate a '
                              'technical issue, with an orchestrator controlling the handoff. A risk is lost context, duplicate actions or '
                              'two agents believing they own the same task. I would define a handoff contract containing task ID, required '
                              'context, completed evidence, next owner and permitted actions. Shared state is versioned and traceable, and '
                              'retries are idempotent. Routing limits and escalation prevent ping-pong between agents when ownership or '
                              'evidence is unclear.',
             'mastery_repair_prompts': ['Can I state the mechanism without hiding behind generic AI vocabulary?',
                                        'Can I name a concrete failure that could happen in this exact scenario?',
                                        'Can I name an implementable control and what it blocks, limits or escalates?',
                                        'Can I state the stop, fallback or escalation behavior when evidence is insufficient?'],
             'is_gate': False,
             'assessment_principle': 'Normal lesson scoring is deterministic. MCQs use stable answer IDs and a published pass rule. The '
                                     'written response is scored only against the published mechanism, example, risk and control rubric. '
                                     'No hidden architecture vocabulary, essay-length preference or generic governance template may change '
                                     'the result.',
             'answer_quality_bar': {'three_star': 'Mechanism + concrete example + one specific risk + one implementable control.',
                                    'four_star': 'Adds evidence, tool boundary, stop condition or escalation behavior that is relevant to '
                                                 'the scenario.',
                                    'five_star': 'Adds multiple relevant operating details without adding unrelated architecture '
                                                 'vocabulary.'}},
 'aia_010': {'design_version': 'mlos_v4_deterministic_agentic_2026_08_17',
             'assessment_mode': 'v4_deterministic_mcq_plus_published_rubric',
             'topic_id': 'aia_010',
             'title': 'Production agent monitoring, cost and rollback',
             'learning_objective': 'Operate agents with trajectory monitoring, budgets, versioned releases, kill/rollback controls and '
                                   'outcome-based alerts so failures are detectable and recoverable.',
             'prerequisite_bridge': 'Start from the agentic system behavior. Peel down only when a deeper mechanism explains a design '
                                    'decision or failure.',
             'concept_steps': [{'heading': '1. Monitor behavior, not only uptime',
                                'body': 'Track task success, tool errors, policy blocks, retries, step count, human overrides, latency and '
                                        'cost. A healthy API can still host a badly behaving agent.'},
                               {'heading': '2. Budget the trajectory',
                                'body': 'Use token, tool-call, step and monetary budgets. Cost spikes can signal loops, excessive '
                                        'retrieval or a changed model/tool path.'},
                               {'heading': '3. Version everything that changes behavior',
                                'body': 'Record model, prompt/policy, tool schema and workflow version so incidents and regressions can be '
                                        'tied to a release.'},
                               {'heading': '4. Recovery and rollback',
                                'body': 'Define kill switches, disable risky tools, route to human fallback and roll back to a known-good '
                                        'version. Side effects may need compensating actions rather than simple software rollback.'},
                               {'heading': '5. Architect translation',
                                'body': 'Release with SLOs, alerts, trace sampling, budget limits, canary rollout, rollback criteria and '
                                        'named incident ownership.'}],
             'concept_map': [],
             'worked_example': {'scenario': "After a prompt release, a support agent's task-success rate stays flat but tool calls per "
                                            'case triple and refund-tool blocks increase. The rollout is paused and the previous workflow '
                                            'version is restored while traces are reviewed.',
                                'takeaway': 'Cost and safety regressions can appear before users report wrong final answers, so monitoring '
                                            'must cover the full trajectory.'},
             'worked_examples': [{'title': 'Architect readout',
                                  'body': "After a prompt release, a support agent's task-success rate stays flat but tool calls per case "
                                          'triple and refund-tool blocks increase. The rollout is paused and the previous workflow version '
                                          'is restored while traces are reviewed. The design point is: Instrument end-to-end traces, '
                                          'define SLOs and budgets, canary changes, alert on behavior shifts, support tool kill switches '
                                          'and keep a tested rollback/human-fallback path.'}],
             'code_bridge': {},
             'misconception': 'Monitoring only API uptime, model latency or final-answer ratings while ignoring tool behavior, side '
                              'effects and recovery.',
             'architect_extension': 'Instrument end-to-end traces, define SLOs and budgets, canary changes, alert on behavior shifts, '
                                    'support tool kill switches and keep a tested rollback/human-fallback path.',
             'diagnostic_drill': {'question': 'The agent service is 99.99% available but refund attempts suddenly double. Is production '
                                              'healthy?',
                                  'reveal': 'Not necessarily. Availability is only one dimension; action rates, policy blocks, task '
                                            'outcomes and cost may show a serious behavior regression.'},
             'knowledge_checks': [{'kind': 'Critical',
                                   'question': 'Which dashboard signal most directly reveals a runaway agent loop?',
                                   'options': ['Steps or tool calls per completed task rising sharply while task-success rate stays flat '
                                               'or falls.',
                                               'Model-provider uptime staying above its availability objective during the same period.',
                                               'Average final-response length decreasing after the latest prompt and model release.',
                                               'Number of registered tools remaining constant while request volume increases normally.'],
                                   'answer_index': 0,
                                   'explanation': 'Trajectory length exposes loops.',
                                   'is_critical': True,
                                   'id': 'mcq_01'},
                                  {'kind': 'Critical',
                                   'question': 'A new agent release causes unsafe write attempts. What is the fastest containment control?',
                                   'options': ['Disable or gate the risky tool and route affected tasks to the defined safe fallback while '
                                               'investigating.',
                                               'Increase logging but keep the tool enabled so enough incident data can be collected for '
                                               'root-cause analysis.',
                                               "Raise the model's system-prompt warning strength and wait for the next monitoring interval "
                                               'to confirm improvement.',
                                               'Increase the step budget so the agent has more opportunities to correct the unsafe action '
                                               'before task completion.'],
                                   'answer_index': 0,
                                   'explanation': 'Containment comes before diagnosis.',
                                   'is_critical': True,
                                   'id': 'mcq_02'},
                                  {'kind': 'Critical',
                                   'question': 'What must be versioned to make rollback meaningful?',
                                   'options': ['Model, prompt/policy, workflow logic and tool/schema configuration that can change agent '
                                               'behavior.',
                                               'Only the model identifier, because prompts and tools are implementation details outside '
                                               'the agent release.',
                                               'Only the application container image, because all relevant behavior can be reconstructed '
                                               'from source control later.',
                                               'Only the final prompt text, because model and tool versions do not affect decisions when '
                                               'the prompt is unchanged.'],
                                   'answer_index': 0,
                                   'explanation': 'Agent behavior depends on multiple versioned components.',
                                   'is_critical': True,
                                   'id': 'mcq_03'},
                                  {'kind': 'Scenario',
                                   'question': 'Token cost doubles but task-success, latency and tool-call count are unchanged. What is a '
                                               'sensible first investigation?',
                                   'options': ['Compare model/prompt versions and context/retrieval size to find why each invocation now '
                                               'consumes more tokens.',
                                               'Assume the agent is more accurate because higher token usage usually indicates deeper '
                                               'reasoning.',
                                               'Disable task-success monitoring because cost is now the dominant production problem.',
                                               'Increase the monthly budget first, since stable task success proves the change is '
                                               'operationally beneficial.'],
                                   'answer_index': 0,
                                   'explanation': 'Cost regressions should be diagnosed, not normalized.',
                                   'is_critical': False,
                                   'id': 'mcq_04'},
                                  {'kind': 'Architecture',
                                   'question': 'Why use a canary rollout for an agent change?',
                                   'options': ['To expose a small controlled share of traffic to the new behavior and compare outcomes '
                                               'before wider release.',
                                               'To make the model deterministic by limiting how many users can send prompts during the '
                                               'first deployment window.',
                                               'To prevent tool calls entirely until the new model has accumulated enough conversational '
                                               'context in production.',
                                               'To avoid keeping the previous version, because canary traffic itself provides a fallback '
                                               'when the new release fails.'],
                                   'answer_index': 0,
                                   'explanation': 'Canary limits blast radius and supports comparison.',
                                   'is_critical': False,
                                   'id': 'mcq_05'},
                                  {'kind': 'Scenario',
                                   'question': 'A rollback restores the previous agent software, but a bad purchase order created by the '
                                               'new version still exists. What does this show?',
                                   'options': ['Software rollback does not reverse external side effects; compensating business actions '
                                               'may also be required.',
                                               'The rollback failed technically because a correct rollback would automatically undo every '
                                               'tool call made by the agent.',
                                               'The tool should never have written to an external system because agent architectures must '
                                               'be read-only in production.',
                                               'The previous model version should be asked to decide whether the purchase order was bad '
                                               'before any recovery action occurs.'],
                                   'answer_index': 0,
                                   'explanation': 'External side effects need compensation.',
                                   'is_critical': False,
                                   'id': 'mcq_06'},
                                  {'kind': 'Trap',
                                   'question': 'Which statement about production monitoring is most accurate?',
                                   'options': ['Service health, model behavior and business outcomes are separate signals and all can fail '
                                               'independently.',
                                               'High API availability is enough to establish agent reliability if the model passed offline '
                                               'evaluation before release.',
                                               'User satisfaction is enough to establish safety because users directly observe whether '
                                               'actions helped them.',
                                               'Tool-call logs are enough to establish task success because successful API responses prove '
                                               'correct business outcomes.'],
                                   'answer_index': 0,
                                   'explanation': 'Operational health is multidimensional.',
                                   'is_critical': False,
                                   'id': 'mcq_07'},
                                  {'kind': 'Architecture',
                                   'question': 'Which cost control is most useful at runtime?',
                                   'options': ['Per-task budgets for steps, tool calls and tokens with stop/escalation behavior when '
                                               'limits are exceeded.',
                                               'A monthly invoice review, because runtime limits may interrupt legitimate complex '
                                               'requests.',
                                               'A global token limit shared by all users, regardless of task type or business importance.',
                                               'A prompt asking the model to minimize cost, without enforcing any external budget or '
                                               'execution limit.'],
                                   'answer_index': 0,
                                   'explanation': 'Runtime budgets bound individual trajectories.',
                                   'is_critical': False,
                                   'id': 'mcq_08'},
                                  {'kind': 'Scenario',
                                   'question': 'Human overrides rise sharply for one workflow after a model upgrade. What should happen?',
                                   'options': ['Treat the override increase as a regression signal, inspect traces and compare against the '
                                               'prior version or canary.',
                                               'Ignore it if automated task-success remains high because human preferences are subjective '
                                               'and not an architecture metric.',
                                               "Remove the override option so the agent's automated outcome can be measured without human "
                                               'interference.',
                                               'Increase the approval threshold so fewer humans are allowed to disagree with the upgraded '
                                               'model.'],
                                   'answer_index': 0,
                                   'explanation': 'Overrides can reveal quality regressions.',
                                   'is_critical': False,
                                   'id': 'mcq_09'},
                                  {'kind': 'Architecture',
                                   'question': 'What makes a rollback plan testable before an incident?',
                                   'options': ['Known-good version, trigger criteria, deployment procedure, tool containment, '
                                               'data/side-effect recovery and named owner.',
                                               'A document stating that the team will revert if necessary, with the details decided by the '
                                               'incident commander later.',
                                               'A second model provider configured in the prompt, because switching models is sufficient '
                                               'recovery for any agent failure.',
                                               'Long-term retention of all logs, because complete observability eliminates the need to '
                                               'rehearse recovery actions.'],
                                   'answer_index': 0,
                                   'explanation': 'Recovery must be executable, not aspirational.',
                                   'is_critical': False,
                                   'id': 'mcq_10'}],
             'evidence_tasks': [{'question_id': 'q1',
                                 'type': 'architect_decision',
                                 'label': 'Short architect response',
                                 'purpose': 'Demonstrate the mechanism in one concrete scenario, then name one specific risk and one '
                                            'implementable control.',
                                 'question': 'In 80-140 words, explain Production agent monitoring, cost and rollback using one business '
                                             'or engineering example. Include the mechanism, one risk and one control.',
                                 'expected_focus': ['mechanism', 'example', 'risk', 'control'],
                                 'response_shape': 'Mechanism → concrete example → specific risk → implementable control.',
                                 'target_min_words': 80,
                                 'target_max_words': 140,
                                 'sample_answer': 'Production agents need operational controls around every trajectory. For a '
                                                  'refund-support agent, I would monitor task success, tool errors, steps per task, cost, '
                                                  'latency, human overrides and policy violations by model and prompt version. A risk is a '
                                                  'release that enters a repeated tool loop, raises cost sharply or performs unsafe side '
                                                  'effects. I would enforce per-task step and cost budgets, canary new versions, alert on '
                                                  'outcome and trajectory regressions, and provide a kill switch plus rollback to the last '
                                                  'approved version. Irreversible side effects also need recovery procedures and named '
                                                  'owners because rolling back code does not automatically undo external actions.'}],
             'written_rubric': {'required': [{'id': 'mechanism',
                                              'label': 'Monitoring/recovery mechanism',
                                              'description': 'Explains monitoring plus budgets/version/rollback behavior.',
                                              'phrases_any': ['monitor',
                                                              'trace',
                                                              'cost',
                                                              'budget',
                                                              'rollback',
                                                              'version',
                                                              'alert',
                                                              'kill switch'],
                                              'token_groups_all': []},
                                             {'id': 'example',
                                              'label': 'Concrete example',
                                              'description': 'Uses a production agent scenario.',
                                              'phrases_any': ['support',
                                                              'refund',
                                                              'order',
                                                              'release',
                                                              'production',
                                                              'for example',
                                                              'scenario'],
                                              'token_groups_all': []},
                                             {'id': 'risk',
                                              'label': 'Specific risk',
                                              'description': 'Names loop, cost spike, unsafe action, regression or side effect.',
                                              'phrases_any': ['runaway',
                                                              'cost',
                                                              'unsafe',
                                                              'regression',
                                                              'wrong',
                                                              'duplicate',
                                                              'spike',
                                                              'failure',
                                                              'side effect'],
                                              'token_groups_all': []},
                                             {'id': 'control',
                                              'label': 'Operating control',
                                              'description': 'Names budget, alert, canary, rollback, kill switch or fallback.',
                                              'phrases_any': ['budget',
                                                              'alert',
                                                              'canary',
                                                              'rollback',
                                                              'kill switch',
                                                              'fallback',
                                                              'limit',
                                                              'disable',
                                                              'owner'],
                                              'token_groups_all': []}],
                                'bonus': [{'id': 'versioning',
                                           'label': 'Versioning',
                                           'description': 'Mentions versioning of behavior components.',
                                           'phrases_any': ['version', 'prompt', 'model', 'tool schema'],
                                           'token_groups_all': []},
                                          {'id': 'compensation',
                                           'label': 'Side-effect recovery',
                                           'description': 'Mentions compensating external actions.',
                                           'phrases_any': ['compensat', 'side effect', 'undo', 'reconcile'],
                                           'token_groups_all': []}]},
             'sample_answer': 'Production agents need operational controls around every trajectory. For a refund-support agent, I would '
                              'monitor task success, tool errors, steps per task, cost, latency, human overrides and policy violations by '
                              'model and prompt version. A risk is a release that enters a repeated tool loop, raises cost sharply or '
                              'performs unsafe side effects. I would enforce per-task step and cost budgets, canary new versions, alert on '
                              'outcome and trajectory regressions, and provide a kill switch plus rollback to the last approved version. '
                              'Irreversible side effects also need recovery procedures and named owners because rolling back code does not '
                              'automatically undo external actions.',
             'mastery_repair_prompts': ['Can I state the mechanism without hiding behind generic AI vocabulary?',
                                        'Can I name a concrete failure that could happen in this exact scenario?',
                                        'Can I name an implementable control and what it blocks, limits or escalates?',
                                        'Can I state the stop, fallback or escalation behavior when evidence is insufficient?'],
             'is_gate': False,
             'assessment_principle': 'Normal lesson scoring is deterministic. MCQs use stable answer IDs and a published pass rule. The '
                                     'written response is scored only against the published mechanism, example, risk and control rubric. '
                                     'No hidden architecture vocabulary, essay-length preference or generic governance template may change '
                                     'the result.',
             'answer_quality_bar': {'three_star': 'Mechanism + concrete example + one specific risk + one implementable control.',
                                    'four_star': 'Adds evidence, tool boundary, stop condition or escalation behavior that is relevant to '
                                                 'the scenario.',
                                    'five_star': 'Adds multiple relevant operating details without adding unrelated architecture '
                                                 'vocabulary.'}}}

def get_agentic_learning_design(topic_id: str) -> Optional[Dict[str, Any]]:
    design = AGENTIC_AI_DESIGNS.get(str(topic_id or "").strip())
    return deepcopy(design) if design else None


def is_agentic_authored_topic(topic_id: str) -> bool:
    return str(topic_id or "").strip() in AGENTIC_AI_DESIGNS
