import { createContext, startTransition, useContext, useEffect, useMemo, useState } from "react";

import {
  demoChannels,
  demoMacros,
  demoMessages as initialDemoMessages,
  demoWorkspaces,
} from "../../shared/data/demo-data";
import { useAuth } from "../auth/auth-context";
import { useUIState } from "../ui-state/ui-state-context";

const ServerStateContext = createContext(null);

function createResourceState() {
  return {
    data: [],
    error: "",
    loading: false,
  };
}

export function ServerStateProvider({ children }) {
  const auth = useAuth();
  const ui = useUIState();
  const [workspacesState, setWorkspacesState] = useState(createResourceState);
  const [channelsState, setChannelsState] = useState(createResourceState);
  const [messagesState, setMessagesState] = useState(createResourceState);
  const [macrosState, setMacrosState] = useState(createResourceState);
  const [demoMessageRows, setDemoMessageRows] = useState(initialDemoMessages);
  const [submitError, setSubmitError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (auth.mode !== "demo") {
      setDemoMessageRows(initialDemoMessages);
    }
  }, [auth.mode]);

  useEffect(() => {
    if (auth.mode === "demo") {
      setWorkspacesState({
        data: demoWorkspaces,
        error: "",
        loading: false,
      });
      return;
    }

    let cancelled = false;
    setWorkspacesState((current) => ({ ...current, loading: true, error: "" }));

    auth
      .apiRequest("/workspaces/")
      .then((payload) => {
        if (cancelled) {
          return;
        }
        setWorkspacesState({
          data: payload,
          error: "",
          loading: false,
        });
      })
      .catch((resourceError) => {
        if (cancelled) {
          return;
        }
        setWorkspacesState({
          data: [],
          error: resourceError.message,
          loading: false,
        });
      });

    return () => {
      cancelled = true;
    };
  }, [auth]);

  useEffect(() => {
    const selectedExists = workspacesState.data.some(
      (workspace) => workspace.id === ui.selectedWorkspaceId,
    );
    if (selectedExists) {
      return;
    }

    const fallbackWorkspaceId = workspacesState.data[0]?.id ?? null;
    startTransition(() => {
      ui.setSelectedWorkspaceId(fallbackWorkspaceId);
    });
  }, [ui, workspacesState.data]);

  useEffect(() => {
    if (!ui.selectedWorkspaceId) {
      setChannelsState(createResourceState());
      return;
    }

    if (auth.mode === "demo") {
      setChannelsState({
        data: demoChannels.filter((channel) => channel.workspace_id === ui.selectedWorkspaceId),
        error: "",
        loading: false,
      });
      return;
    }

    let cancelled = false;
    setChannelsState((current) => ({ ...current, loading: true, error: "" }));

    auth
      .apiRequest(`/channels/?workspace_id=${ui.selectedWorkspaceId}`)
      .then((payload) => {
        if (cancelled) {
          return;
        }
        setChannelsState({
          data: payload,
          error: "",
          loading: false,
        });
      })
      .catch((resourceError) => {
        if (cancelled) {
          return;
        }
        setChannelsState({
          data: [],
          error: resourceError.message,
          loading: false,
        });
      });

    return () => {
      cancelled = true;
    };
  }, [auth, ui.selectedWorkspaceId]);

  useEffect(() => {
    const selectedExists = channelsState.data.some(
      (channel) => channel.id === ui.selectedChannelId,
    );
    if (selectedExists) {
      return;
    }

    const fallbackChannelId = channelsState.data[0]?.id ?? null;
    startTransition(() => {
      ui.setSelectedChannelId(fallbackChannelId);
    });
  }, [channelsState.data, ui]);

  useEffect(() => {
    if (!ui.selectedChannelId) {
      setMessagesState(createResourceState());
      return;
    }

    if (auth.mode === "demo") {
      setMessagesState({
        data: demoMessageRows.filter((message) => message.channel_id === ui.selectedChannelId),
        error: "",
        loading: false,
      });
      return;
    }

    let cancelled = false;
    setMessagesState((current) => ({ ...current, loading: true, error: "" }));

    auth
      .apiRequest(`/messages/?channel_id=${ui.selectedChannelId}`)
      .then((payload) => {
        if (cancelled) {
          return;
        }
        setMessagesState({
          data: payload,
          error: "",
          loading: false,
        });
      })
      .catch((resourceError) => {
        if (cancelled) {
          return;
        }
        setMessagesState({
          data: [],
          error: resourceError.message,
          loading: false,
        });
      });

    return () => {
      cancelled = true;
    };
  }, [auth, demoMessageRows, ui.selectedChannelId]);

  useEffect(() => {
    if (!ui.selectedWorkspaceId && !ui.selectedChannelId) {
      setMacrosState(createResourceState());
      return;
    }

    if (auth.mode === "demo") {
      const rows = demoMacros.filter((macro) => {
        if (macro.channel_id && macro.channel_id === ui.selectedChannelId) {
          return true;
        }
        return (
          macro.workspace_id &&
          macro.workspace_id === ui.selectedWorkspaceId &&
          macro.channel_id === null
        );
      });
      setMacrosState({
        data: rows,
        error: "",
        loading: false,
      });
      return;
    }

    const params = new URLSearchParams();
    params.set("effective", "true");
    if (ui.selectedWorkspaceId) {
      params.set("workspace_id", String(ui.selectedWorkspaceId));
    }
    if (ui.selectedChannelId) {
      params.set("channel_id", String(ui.selectedChannelId));
    }

    let cancelled = false;
    setMacrosState((current) => ({ ...current, loading: true, error: "" }));

    auth
      .apiRequest(`/macros/?${params.toString()}`)
      .then((payload) => {
        if (cancelled) {
          return;
        }
        setMacrosState({
          data: payload,
          error: "",
          loading: false,
        });
      })
      .catch((resourceError) => {
        if (cancelled) {
          return;
        }
        setMacrosState({
          data: [],
          error: resourceError.message,
          loading: false,
        });
      });

    return () => {
      cancelled = true;
    };
  }, [auth, ui.selectedChannelId, ui.selectedWorkspaceId]);

  const submitMessage = async () => {
    const body = ui.composerDraft.trim();
    if (!body || !ui.selectedChannelId) {
      return;
    }

    setSubmitting(true);
    setSubmitError("");

    try {
      if (auth.mode === "demo") {
        const nextMessage = {
          id: Date.now(),
          channel_id: ui.selectedChannelId,
          body,
          author: auth.user,
          created_at: new Date().toISOString(),
        };
        setDemoMessageRows((current) => [...current, nextMessage]);
        ui.resetComposerDraft();
        return;
      }

      const created = await auth.apiRequest("/messages/", {
        method: "POST",
        body: {
          body,
          channel_id: ui.selectedChannelId,
        },
      });
      setMessagesState((current) => ({
        ...current,
        data: [...current.data, created],
      }));
      ui.resetComposerDraft();
    } catch (messageError) {
      setSubmitError(messageError.message);
    } finally {
      setSubmitting(false);
    }
  };

  const selectedWorkspace = useMemo(
    () => workspacesState.data.find((workspace) => workspace.id === ui.selectedWorkspaceId) ?? null,
    [ui.selectedWorkspaceId, workspacesState.data],
  );
  const selectedChannel = useMemo(
    () => channelsState.data.find((channel) => channel.id === ui.selectedChannelId) ?? null,
    [channelsState.data, ui.selectedChannelId],
  );

  const value = useMemo(() => ({
    channels: channelsState.data,
    channelsError: channelsState.error,
    channelsLoading: channelsState.loading,
    macros: macrosState.data,
    macrosError: macrosState.error,
    macrosLoading: macrosState.loading,
    messages: messagesState.data,
    messagesError: messagesState.error,
    messagesLoading: messagesState.loading,
    selectedChannel,
    selectedWorkspace,
    submitError,
    submitMessage,
    submitting,
    workspaces: workspacesState.data,
    workspacesError: workspacesState.error,
    workspacesLoading: workspacesState.loading,
  }), [channelsState.data, channelsState.error, channelsState.loading, macrosState.data, macrosState.error, macrosState.loading, messagesState.data, messagesState.error, messagesState.loading, selectedChannel, selectedWorkspace, submitError, submitting, workspacesState.data, workspacesState.error, workspacesState.loading]);

  return <ServerStateContext.Provider value={value}>{children}</ServerStateContext.Provider>;
}

export function useServerState() {
  const value = useContext(ServerStateContext);
  if (!value) {
    throw new Error("useServerState must be used inside ServerStateProvider.");
  }
  return value;
}
