import { useEffect, useMemo, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  Activity,
  Bot,
  CalendarClock,
  CheckCircle2,
  ClipboardList,
  Edit3,
  MessageSquareText,
  Save,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  UserRoundSearch,
} from "lucide-react";
import {
  addUserChat,
  createInteraction,
  fetchAgentRuns,
  fetchHcps,
  fetchInteractions,
  fetchTools,
  runToolDemo,
  sendChat,
  setMode,
  setSelectedHcpId,
  updateInteraction,
} from "./store";

const toolIcons = {
  log_interaction: ClipboardList,
  edit_interaction: Edit3,
  suggest_next_best_action: Sparkles,
  schedule_follow_up: CalendarClock,
  retrieve_hcp_profile: UserRoundSearch,
  check_compliance: ShieldCheck,
  summarize_history: Activity,
};

const defaultForm = {
  interaction_type: "Detailing Call",
  channel: "In-person",
  product_discussed: "CardioGuard",
  objective: "Discuss appropriate patient profiles and understand current barriers",
  notes:
    "Dr. Mehra was interested in the updated clinical evidence, asked about safety profile, and requested a follow-up with a patient profile checklist.",
  commitment: "Review clinical paper",
  next_step: "Share approved evidence deck and schedule follow-up",
  follow_up_date: "",
};

function App() {
  const dispatch = useDispatch();
  const { hcps, interactions, tools, agentRuns, selectedHcpId, mode, lastAiResult, chatMessages, status, error } =
    useSelector((state) => state.crm);
  const [form, setForm] = useState(defaultForm);
  const [editingInteractionId, setEditingInteractionId] = useState(null);
  const [chatText, setChatText] = useState(
    "Log that Dr. Mehra discussed CardioGuard today, showed interest, asked about safety data, and requested a follow-up next week."
  );

  useEffect(() => {
    dispatch(fetchHcps());
    dispatch(fetchInteractions());
    dispatch(fetchTools());
    dispatch(fetchAgentRuns());
  }, [dispatch]);

  const selectedHcp = useMemo(
    () => hcps.find((hcp) => hcp.id === Number(selectedHcpId)) || hcps[0],
    [hcps, selectedHcpId]
  );

  const onSubmit = (event) => {
    event.preventDefault();
    if (editingInteractionId) {
      dispatch(updateInteraction({ interactionId: editingInteractionId, payload: form }));
      return;
    }
    dispatch(createInteraction({ ...form, hcp_id: Number(selectedHcpId) }));
  };

  const startEdit = (interaction) => {
    setEditingInteractionId(interaction.id);
    dispatch(setMode("form"));
    dispatch(setSelectedHcpId(interaction.hcp_id));
    setForm({
      interaction_type: interaction.interaction_type,
      channel: interaction.channel,
      product_discussed: interaction.product_discussed,
      objective: interaction.objective,
      notes: interaction.notes,
      commitment: interaction.commitment,
      next_step: interaction.next_step,
      follow_up_date: interaction.follow_up_date,
    });
  };

  const resetForm = () => {
    setEditingInteractionId(null);
    setForm(defaultForm);
  };

  const onChat = (event) => {
    event.preventDefault();
    if (!chatText.trim()) return;
    dispatch(addUserChat(chatText));
    dispatch(sendChat({ message: chatText, hcp_id: Number(selectedHcpId) }));
    setChatText("");
  };

  const runAllTools = () => {
    tools.forEach((tool, index) => {
      window.setTimeout(() => {
        dispatch(runToolDemo({ tool_name: tool.name, payload: demoPayload(tool.name) }));
      }, index * 250);
    });
  };

  const demoPayload = (toolName) => {
    const base = { hcp_id: Number(selectedHcpId) };
    if (toolName === "log_interaction") return { ...base, ...defaultForm };
    if (toolName === "edit_interaction") {
      return {
        ...base,
        interaction_id: interactions[0]?.id || 1,
        notes: "Updated note: HCP requested published safety evidence and a compliant follow-up.",
      };
    }
    if (toolName === "schedule_follow_up") return { ...base, days_from_now: 5, purpose: "Evidence follow-up" };
    if (toolName === "check_compliance") return { text: "Check this note for off-label or gift language." };
    return base;
  };

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">AI-First CRM</p>
          <h1>HCP Log Interaction</h1>
        </div>
        <div className="agent-badge">
          <Bot size={18} />
          LangGraph + Groq gemma2-9b-it
        </div>
      </header>

      <section className="workspace">
        <aside className="sidebar">
          <div className="panel-title">
            <Stethoscope size={18} />
            Healthcare Professionals
          </div>
          <select value={selectedHcpId} onChange={(event) => dispatch(setSelectedHcpId(event.target.value))}>
            {hcps.map((hcp) => (
              <option key={hcp.id} value={hcp.id}>
                {hcp.name}
              </option>
            ))}
          </select>
          {selectedHcp && (
            <div className="hcp-profile">
              <strong>{selectedHcp.specialty}</strong>
              <span>{selectedHcp.territory}</span>
              <span>Segment {selectedHcp.segment}</span>
              <span>{selectedHcp.preferred_channel}</span>
            </div>
          )}

          <div className="panel-title compact">
            <Sparkles size={18} />
            Agent Tools
          </div>
          <div className="tool-metrics">
            <strong>{tools.length}</strong>
            <span>LangGraph tools ready</span>
          </div>
          <button className="run-all" onClick={runAllTools}>
            <Sparkles size={16} />
            Demo All Tools
          </button>
          <div className="tool-list">
            {tools.map((tool) => {
              const Icon = toolIcons[tool.name] || CheckCircle2;
              return (
                <button
                  key={tool.name}
                  className="tool-button"
                  title={tool.description}
                  onClick={() => dispatch(runToolDemo({ tool_name: tool.name, payload: demoPayload(tool.name) }))}
                >
                  <Icon size={16} />
                  <span>{tool.name.replaceAll("_", " ")}</span>
                </button>
              );
            })}
          </div>
        </aside>

        <section className="main-panel">
          <div className="mode-tabs" aria-label="Log mode">
            <button className={mode === "form" ? "active" : ""} onClick={() => dispatch(setMode("form"))}>
              <ClipboardList size={18} />
              Structured
            </button>
            <button className={mode === "chat" ? "active" : ""} onClick={() => dispatch(setMode("chat"))}>
              <MessageSquareText size={18} />
              Conversational
            </button>
          </div>

          {mode === "form" ? (
            <form className="log-form" onSubmit={onSubmit}>
              {editingInteractionId && (
                <div className="edit-banner">
                  <Edit3 size={16} />
                  Editing interaction #{editingInteractionId}
                  <button type="button" onClick={resetForm}>New Log</button>
                </div>
              )}
              <div className="grid two">
                <label>
                  Interaction Type
                  <input value={form.interaction_type} onChange={(e) => setForm({ ...form, interaction_type: e.target.value })} />
                </label>
                <label>
                  Channel
                  <select value={form.channel} onChange={(e) => setForm({ ...form, channel: e.target.value })}>
                    <option>In-person</option>
                    <option>Phone</option>
                    <option>Email</option>
                    <option>WhatsApp</option>
                    <option>Video call</option>
                  </select>
                </label>
              </div>
              <div className="grid two">
                <label>
                  Product Discussed
                  <input value={form.product_discussed} onChange={(e) => setForm({ ...form, product_discussed: e.target.value })} />
                </label>
                <label>
                  Follow-up Date
                  <input type="date" value={form.follow_up_date} onChange={(e) => setForm({ ...form, follow_up_date: e.target.value })} />
                </label>
              </div>
              <label>
                Objective
                <input value={form.objective} onChange={(e) => setForm({ ...form, objective: e.target.value })} />
              </label>
              <label>
                Notes
                <textarea rows="7" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
              </label>
              <div className="grid two">
                <label>
                  HCP Commitment
                  <input value={form.commitment} onChange={(e) => setForm({ ...form, commitment: e.target.value })} />
                </label>
                <label>
                  Next Step
                  <input value={form.next_step} onChange={(e) => setForm({ ...form, next_step: e.target.value })} />
                </label>
              </div>
              <button className="primary-action" type="submit" disabled={status === "saving"}>
                {editingInteractionId ? <Edit3 size={18} /> : <Save size={18} />}
                {status === "saving" ? "Saving" : editingInteractionId ? "Update Interaction" : "Log Interaction"}
              </button>
              {error && <p className="error">{error}</p>}
            </form>
          ) : (
            <section className="chat-panel">
              <div className="messages">
                {chatMessages.map((message, index) => (
                  <div key={`${message.role}-${index}`} className={`message ${message.role}`}>
                    {message.text}
                  </div>
                ))}
              </div>
              <form className="chat-input" onSubmit={onChat}>
                <input value={chatText} onChange={(event) => setChatText(event.target.value)} placeholder="Describe the HCP interaction..." />
                <button className="icon-action" title="Send to LangGraph agent">
                  <MessageSquareText size={18} />
                </button>
              </form>
            </section>
          )}
        </section>

        <aside className="insights">
          <div className="panel-title">
            <Sparkles size={18} />
            AI Output
          </div>
          <pre>{JSON.stringify(lastAiResult || { status: "No AI action yet" }, null, 2)}</pre>

          <div className="panel-title compact">
            <Bot size={18} />
            Agent Trace
          </div>
          <div className="trace-list">
            {agentRuns.slice(0, 4).map((run) => (
              <article key={run.id} className="trace-card">
                <strong>{run.selected_tool?.replaceAll("_", " ")}</strong>
                <span>{run.result?.routing_reason || run.user_message}</span>
              </article>
            ))}
          </div>

          <div className="panel-title compact">
            <ClipboardList size={18} />
            Recent Interactions
          </div>
          <div className="recent-list">
            {interactions.slice(0, 5).map((interaction) => (
              <article key={interaction.id} className="interaction-card">
                <strong>{interaction.hcp_name}</strong>
                <span>{interaction.product_discussed}</span>
                <p>{interaction.summary}</p>
                <button title="Edit interaction" onClick={() => startEdit(interaction)}>
                  <Edit3 size={14} />
                  Edit
                </button>
              </article>
            ))}
          </div>
        </aside>
      </section>
    </main>
  );
}

export default App;
