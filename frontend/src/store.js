import { configureStore, createAsyncThunk, createSlice } from "@reduxjs/toolkit";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000/api";

const api = async (path, options = {}) => {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Request failed");
  }
  return response.json();
};

export const fetchHcps = createAsyncThunk("crm/fetchHcps", () => api("/hcps"));
export const fetchInteractions = createAsyncThunk("crm/fetchInteractions", () => api("/interactions"));
export const createInteraction = createAsyncThunk("crm/createInteraction", async (payload) => {
  const result = await api("/interactions", { method: "POST", body: JSON.stringify(payload) });
  return result.interaction;
});
export const updateInteraction = createAsyncThunk("crm/updateInteraction", async ({ interactionId, payload }) => {
  const result = await api(`/interactions/${interactionId}`, { method: "PUT", body: JSON.stringify(payload) });
  return result.interaction;
});
export const sendChat = createAsyncThunk("crm/sendChat", (payload) =>
  api("/agent/chat", { method: "POST", body: JSON.stringify(payload) })
);
export const fetchTools = createAsyncThunk("crm/fetchTools", () => api("/agent/tools"));
export const fetchAgentRuns = createAsyncThunk("crm/fetchAgentRuns", () => api("/agent/runs"));
export const runToolDemo = createAsyncThunk("crm/runToolDemo", (payload) =>
  api("/agent/demo", { method: "POST", body: JSON.stringify(payload) })
);

const crmSlice = createSlice({
  name: "crm",
  initialState: {
    hcps: [],
    interactions: [],
    tools: [],
    agentRuns: [],
    selectedHcpId: 1,
    mode: "form",
    lastAiResult: null,
    chatMessages: [
      {
        role: "assistant",
        text: "Select an HCP and describe the interaction. I will route it through the LangGraph agent.",
      },
    ],
    status: "idle",
    error: "",
  },
  reducers: {
    setSelectedHcpId: (state, action) => {
      state.selectedHcpId = Number(action.payload);
    },
    setMode: (state, action) => {
      state.mode = action.payload;
    },
    addUserChat: (state, action) => {
      state.chatMessages.push({ role: "user", text: action.payload });
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchHcps.fulfilled, (state, action) => {
        state.hcps = action.payload;
        if (!state.selectedHcpId && action.payload[0]) state.selectedHcpId = action.payload[0].id;
      })
      .addCase(fetchInteractions.fulfilled, (state, action) => {
        state.interactions = action.payload;
      })
      .addCase(createInteraction.pending, (state) => {
        state.status = "saving";
      })
      .addCase(createInteraction.fulfilled, (state, action) => {
        state.status = "idle";
        state.error = "";
        state.interactions.unshift(action.payload);
        state.lastAiResult = action.payload;
      })
      .addCase(createInteraction.rejected, (state, action) => {
        state.status = "idle";
        state.error = action.error.message;
      })
      .addCase(updateInteraction.pending, (state) => {
        state.status = "saving";
      })
      .addCase(updateInteraction.fulfilled, (state, action) => {
        state.status = "idle";
        state.error = "";
        const existingIndex = state.interactions.findIndex((item) => item.id === action.payload.id);
        if (existingIndex >= 0) {
          state.interactions[existingIndex] = action.payload;
        }
        state.lastAiResult = action.payload;
      })
      .addCase(updateInteraction.rejected, (state, action) => {
        state.status = "idle";
        state.error = action.error.message;
      })
      .addCase(sendChat.fulfilled, (state, action) => {
        state.lastAiResult = action.payload.data;
        state.chatMessages.push({ role: "assistant", text: action.payload.answer });
        const interaction = action.payload.data?.interaction;
        if (interaction) state.interactions.unshift(interaction);
      })
      .addCase(fetchTools.fulfilled, (state, action) => {
        state.tools = action.payload;
      })
      .addCase(fetchAgentRuns.fulfilled, (state, action) => {
        state.agentRuns = action.payload;
      })
      .addCase(runToolDemo.fulfilled, (state, action) => {
        state.lastAiResult = action.payload.result;
        state.agentRuns.unshift({
          id: `local-${Date.now()}`,
          selected_tool: action.payload.selected_tool,
          user_message: `Demo exact tool ${action.payload.selected_tool}`,
          result: action.payload.result,
        });
        const interaction = action.payload.result?.interaction;
        if (interaction) {
          const existingIndex = state.interactions.findIndex((item) => item.id === interaction.id);
          if (existingIndex >= 0) {
            state.interactions[existingIndex] = interaction;
          } else {
            state.interactions.unshift(interaction);
          }
        }
      });
  },
});

export const { setSelectedHcpId, setMode, addUserChat } = crmSlice.actions;

export const store = configureStore({
  reducer: {
    crm: crmSlice.reducer,
  },
});
