import React, { useEffect, useMemo, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  createInteraction,
  extractInteraction,
  fetchHcps,
  setSelectedHcpId,
  updateInteraction,
} from "./store";

const defaultForm = {
  interaction_type: "Meeting",
  channel: "In-person",
  product_discussed: "",
  objective: "Log HCP interaction",
  notes: "",
  commitment: "",
  next_step: "",
  follow_up_date: "",
};

function getCurrentDateTimeFields() {
  const now = new Date();
  return formatDateTimeForInputs(now);
}

function padDatePart(value) {
  return String(value).padStart(2, "0");
}

function formatDateTimeForInputs(date) {
  return {
    date: `${date.getFullYear()}-${padDatePart(date.getMonth() + 1)}-${padDatePart(date.getDate())}`,
    time: `${padDatePart(date.getHours())}:${padDatePart(date.getMinutes())}`,
  };
}

const defaultUiFields = {
  hcp_name: "",
  ...getCurrentDateTimeFields(),
  attendees: "",
  topics_discussed: "",
  materials_shared: "",
  samples_distributed: "",
  sentiment: "Neutral",
  outcomes: "",
  follow_up_actions: "",
};

function normalizeSentiment(value = "") {
  const lowered = value.toLowerCase();
  if (lowered.includes("positive")) return "Positive";
  if (lowered.includes("negative") || lowered.includes("cautious")) return "Negative";
  return "Neutral";
}

function inferMaterials(text = "") {
  const lowered = text.toLowerCase();
  if (lowered.includes("brochure")) return "Brochures.";
  if (lowered.includes("deck")) return "Clinical deck.";
  if (lowered.includes("paper") || lowered.includes("study")) return "Clinical paper.";
  return "";
}

function inferSamples(text = "") {
  return text.toLowerCase().includes("sample") ? "Samples recorded." : "";
}

function inferDoctorName(text = "") {
  const match = text.match(/\b(?:dr\.?|doctor)\s+([a-z][a-z.\s-]{1,40})/i);
  if (!match) return "";
  const rawName = match[1]
    .split(/,|\.|\band\b|\bdiscussed\b|\bmet\b|\btoday\b/i)[0]
    .trim();
  if (!rawName) return "";
  return `Dr. ${rawName
    .split(/\s+/)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(" ")}`;
}

function inferOutcome(text = "") {
  const lowered = text.toLowerCase();
  if (lowered.includes("positive")) return "Positive discussion.";
  if (lowered.includes("requested")) return "HCP requested follow-up information.";
  if (lowered.includes("discussed")) return "Discussion completed.";
  return "";
}

function inferFollowUp(text = "") {
  const lowered = text.toLowerCase();
  if (lowered.includes("follow")) return "Schedule follow-up meeting.";
  if (lowered.includes("brochure") || lowered.includes("material")) return "Send approved material.";
  return "";
}

function inferTimeParts(text = "") {
  const explicitTime =
    text.match(/\b(?:at|on)\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b/i) ||
    text.match(/\b(\d{1,2})(?::(\d{2}))\s*(am|pm)?\b/i) ||
    text.match(/\b(\d{1,2})\s*(am|pm)\b/i);

  if (!explicitTime) return null;

  let hour = Number(explicitTime[1]);
  const minute = Number(explicitTime[2] && /^\d{2}$/.test(explicitTime[2]) ? explicitTime[2] : 0);
  const period = (explicitTime[3] || explicitTime[2] || "").toLowerCase();

  if (period === "pm" && hour < 12) hour += 12;
  if (period === "am" && hour === 12) hour = 0;
  if (hour > 23 || minute > 59) return null;

  return { hour, minute };
}

function inferDateTime(text = "") {
  const lowered = text.toLowerCase();
  const now = new Date();
  const inferred = new Date(now);

  if (lowered.includes("tomorrow")) inferred.setDate(now.getDate() + 1);
  if (lowered.includes("yesterday")) inferred.setDate(now.getDate() - 1);

  const dateMatch = text.match(/\b(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?\b/);
  if (dateMatch) {
    const first = Number(dateMatch[1]);
    const second = Number(dateMatch[2]);
    const year = dateMatch[3] ? Number(dateMatch[3].length === 2 ? `20${dateMatch[3]}` : dateMatch[3]) : now.getFullYear();
    inferred.setFullYear(year);
    inferred.setMonth(second - 1);
    inferred.setDate(first);
  }

  const timeParts = inferTimeParts(text);
  if (timeParts) {
    inferred.setHours(timeParts.hour);
    inferred.setMinutes(timeParts.minute);
    inferred.setSeconds(0);
    inferred.setMilliseconds(0);
  }

  return formatDateTimeForInputs(inferred);
}

function inferHcpIdFromText(text, hcps) {
  const lowered = text.toLowerCase();
  const matched = hcps.find((hcp) => {
    const fullName = hcp.name.toLowerCase();
    const lastName = fullName.split(" ").at(-1);
    return lowered.includes(fullName) || lowered.includes(lastName);
  });
  return matched?.id;
}

function formatTimeForInput(value) {
  if (!value) return "";
  return value;
}

function App() {
  const dispatch = useDispatch();
  const { hcps, selectedHcpId, extractedDraft, status, error } = useSelector((state) => state.crm);
  const [form, setForm] = useState(defaultForm);
  const [uiFields, setUiFields] = useState(defaultUiFields);
  const [editingInteractionId] = useState(null);
  const [assistantText, setAssistantText] = useState("");
  const [assistantMessages, setAssistantMessages] = useState([
    {
      role: "info",
      text: 'Log interaction details here (e.g., "Met Dr. Smith, discussed Prodo-X efficacy, positive sentiment, shared brochure") or ask for help.',
    },
  ]);

  useEffect(() => {
    dispatch(fetchHcps());
  }, [dispatch]);

  const selectedHcp = useMemo(
    () => hcps.find((hcp) => hcp.id === Number(selectedHcpId)) || hcps[0],
    [hcps, selectedHcpId]
  );

  const applyAssistantTextToLeftPanel = (text, hcpId = selectedHcpId) => {
    const matchedHcp = hcps.find((hcp) => hcp.id === Number(hcpId));
    const inferredDoctorName = inferDoctorName(text);
    const displayName = inferredDoctorName || matchedHcp?.name || "";
    const inferredMaterial = inferMaterials(text);
    const inferredSample = inferSamples(text);
    const inferredSentiment = normalizeSentiment(text);
    const inferredDateTime = inferDateTime(text);

    setUiFields((current) => ({
      ...current,
      date: inferredDateTime.date,
      time: inferredDateTime.time,
      hcp_name: displayName || current.hcp_name,
      attendees: displayName || current.attendees,
      topics_discussed: text,
      materials_shared: inferredMaterial || current.materials_shared,
      samples_distributed: inferredSample || current.samples_distributed,
      sentiment: inferredSentiment,
      outcomes: inferOutcome(text) || current.outcomes,
      follow_up_actions: inferFollowUp(text) || current.follow_up_actions,
    }));
    setForm((current) => ({
      ...current,
      notes: text,
      product_discussed: text.toLowerCase().includes("product x") ? "Product X" : current.product_discussed,
    }));
  };

  useEffect(() => {
    if (!extractedDraft?.interaction) return;
    const draft = extractedDraft.interaction;
    const notes = draft.notes || assistantText;
    setForm((current) => ({
      ...current,
      interaction_type: draft.interaction_type || current.interaction_type,
      channel: draft.channel || current.channel,
      product_discussed: draft.product_discussed || current.product_discussed,
      objective: draft.objective || current.objective,
      notes: notes || current.notes,
      commitment: draft.commitment || current.commitment,
      next_step: draft.next_step || current.next_step,
      follow_up_date: draft.follow_up_date || current.follow_up_date,
    }));
    setUiFields((current) => ({
      ...current,
      hcp_name: current.hcp_name || selectedHcp?.name || "",
      attendees: current.attendees || selectedHcp?.name || "",
      topics_discussed: notes || current.topics_discussed,
      materials_shared: inferMaterials(notes) || current.materials_shared,
      samples_distributed: inferSamples(notes) || current.samples_distributed,
      sentiment: normalizeSentiment(draft.sentiment || notes),
      outcomes: draft.commitment || current.outcomes,
      follow_up_actions: draft.next_step || current.follow_up_actions,
    }));
    setAssistantMessages((messages) => [
      ...messages,
      {
        role: "success",
        text:
          "**Interaction logged successfully!** The details (HCP Name, Date, Sentiment, and Materials) have been automatically populated based on your summary. Would you like me to suggest a specific follow-up action, such as scheduling a meeting?",
      },
    ]);
  }, [extractedDraft, selectedHcp, assistantText]);

  const submitPayload = () => ({
    ...form,
    hcp_id: Number(selectedHcpId),
    notes: form.notes || uiFields.topics_discussed,
    commitment: form.commitment || uiFields.outcomes,
    next_step: form.next_step || uiFields.follow_up_actions,
  });

  const onSubmit = (event) => {
    event.preventDefault();
    if (editingInteractionId) {
      dispatch(updateInteraction({ interactionId: editingInteractionId, payload: submitPayload() }));
      return;
    }
    dispatch(createInteraction(submitPayload()));
  };

  const onAssistantSubmit = (event) => {
    event.preventDefault();
    const text = assistantText.trim();
    if (!text) return;
    const inferredHcpId = inferHcpIdFromText(text, hcps);
    if (inferredHcpId) {
      dispatch(setSelectedHcpId(inferredHcpId));
    }
    applyAssistantTextToLeftPanel(text, inferredHcpId || selectedHcpId);
    setAssistantMessages((messages) => [...messages, { role: "user", text }]);
    setAssistantText("");
    dispatch(extractInteraction({ message: text, hcp_id: Number(inferredHcpId || selectedHcpId) }));
  };

  return (
    <main className="page-shell">
      <section className="interaction-card">
        <form onSubmit={onSubmit}>
          <h1>Log HCP Interaction</h1>
          <h2>Interaction Details</h2>

          <div className="field-grid two">
            <label>
              HCP Name
              <input value={uiFields.hcp_name} readOnly tabIndex="-1" placeholder="Search or select HCP..." />
            </label>

            <label>
              Interaction Type
              <select value={form.interaction_type} disabled>
                <option>Meeting</option>
                <option>Detailing Call</option>
                <option>Phone Call</option>
                <option>Email Follow-up</option>
              </select>
            </label>
          </div>

          <div className="field-grid two">
            <label>
              Date
              <input type="date" value={uiFields.date} readOnly tabIndex="-1" />
            </label>

            <label>
              Time
              <input type="time" value={formatTimeForInput(uiFields.time)} readOnly tabIndex="-1" />
            </label>
          </div>

          <label>
            Attendees
            <input value={uiFields.attendees} readOnly tabIndex="-1" placeholder="Enter names or search..." />
          </label>

          <label>
            Topics Discussed
            <textarea rows="5" value={uiFields.topics_discussed} readOnly tabIndex="-1" placeholder="Enter key discussion points..." />
          </label>

          <button className="voice-link" type="button" disabled>🎙️ Summarize from Voice Note (Requires Consent)</button>

          <section className="plain-section">
            <h2>Materials Shared / Samples Distributed</h2>
            <div className="plain-row">
              <div>
                <h3>Materials Shared</h3>
                <p>{uiFields.materials_shared || "No materials added."}</p>
              </div>
              <button type="button" disabled>🔍 Search/Add</button>
            </div>
            <div className="plain-row">
              <div>
                <h3>Samples Distributed</h3>
                <p>{uiFields.samples_distributed || "No samples added."}</p>
              </div>
              <button type="button" disabled>✚ Add Sample</button>
            </div>
          </section>

          <section className="sentiment-block">
            <h2>Observed/Inferred HCP Sentiment</h2>
            <div className="sentiment-row">
              {[
                ["Positive", "🙂"],
                ["Neutral", "😐"],
                ["Negative", "😟"],
              ].map(([label, icon]) => (
                <label key={label}>
                  <input
                    type="radio"
                    checked={uiFields.sentiment === label}
                    disabled
                  />
                  <span>{icon}</span>
                  {label}
                </label>
              ))}
            </div>
          </section>

          <label>
            Outcomes
            <textarea rows="5" value={uiFields.outcomes} readOnly tabIndex="-1" placeholder="Key outcomes or agreements..." />
          </label>

          <label>
            Follow-up Actions
            <textarea rows="4" value={uiFields.follow_up_actions} readOnly tabIndex="-1" placeholder="Enter next steps or tasks..." />
          </label>

          <div className="ai-followups">
            <h2>AI Suggested Follow-ups:</h2>
            <button type="button" disabled>+ Schedule follow-up meeting in 2 weeks</button>
            <button type="button" disabled>+ Send OncoBoost Phase III PDF</button>
            <button type="button" disabled>+ Add Dr. Sharma to advisory board invite list</button>
          </div>

          <button className="hidden-submit" type="submit" disabled={status === "saving"}>
            {status === "saving" ? "Saving..." : "Save"}
          </button>
          {error && <p className="error">{error}</p>}
        </form>
      </section>

      <aside className="assistant-card">
        <div className="assistant-header">
          <h2>🤖 AI Assistant</h2>
          <p>Log Interaction details here via chat</p>
        </div>

        <div className="assistant-messages">
          {assistantMessages.map((message, index) => (
            <div key={`${message.role}-${index}`} className={`message ${message.role}`}>
              {message.text}
            </div>
          ))}
        </div>

        <form className="assistant-input" onSubmit={onAssistantSubmit}>
          <textarea value={assistantText} onChange={(event) => setAssistantText(event.target.value)} placeholder="Describe Interaction..." />
          <button type="submit">
            A<br />
            Log
          </button>
        </form>
      </aside>
    </main>
  );
}

export default App;
