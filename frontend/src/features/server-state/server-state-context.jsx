import {
  createContext,
  startTransition,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  demoChannels,
  demoMacros,
  demoMessages as initialDemoMessages,
  demoWorkspaces,
} from "../../shared/data/demo-data";
import { useAuth } from "../auth/auth-context";
import { useUIState } from "../ui-state/ui-state-context";

const ServerStateContext = createContext(null);

function sortWorkspaces(rows) {
  return [...rows].sort((left, right) => {
    const nameResult = left.name.localeCompare(right.name, "ja");
    if (nameResult !== 0) {
      return nameResult;
    }
    return left.id - right.id;
  });
}

function sortChannels(rows) {
  return [...rows].sort((left, right) => {
    if (left.workspace_id !== right.workspace_id) {
      return left.workspace_id - right.workspace_id;
    }
    return left.id - right.id;
  });
}

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
  const [demoWorkspaceRows, setDemoWorkspaceRows] = useState(demoWorkspaces);
  const [demoChannelRows, setDemoChannelRows] = useState(demoChannels);
  const [demoMessageRows, setDemoMessageRows] = useState(initialDemoMessages);
  const [createWorkspaceError, setCreateWorkspaceError] = useState("");
  const [createChannelError, setCreateChannelError] = useState("");
  const [submitError, setSubmitError] = useState("");
  const [creatingWorkspace, setCreatingWorkspace] = useState(false);
  const [creatingChannel, setCreatingChannel] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const selectedWorkspaceIdRef = useRef(ui.selectedWorkspaceId);

  useEffect(() => {
    selectedWorkspaceIdRef.current = ui.selectedWorkspaceId;
  }, [ui.selectedWorkspaceId]);

  useEffect(() => {
    if (auth.mode !== "demo") {
      setDemoWorkspaceRows(demoWorkspaces);
      setDemoChannelRows(demoChannels);
      setDemoMessageRows(initialDemoMessages);
    }
  }, [auth.mode]);

  useEffect(() => {
    if (auth.mode === "demo") {
      setWorkspacesState({
        data: demoWorkspaceRows,
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
  }, [auth, demoWorkspaceRows]);

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
        data: demoChannelRows.filter((channel) => channel.workspace_id === ui.selectedWorkspaceId),
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
  }, [auth, demoChannelRows, ui.selectedWorkspaceId]);

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

  const createWorkspace = useCallback(async ({ description, name }) => {
    const trimmedName = name.trim();
    const trimmedDescription = description.trim();

    if (!trimmedName) {
      return false;
    }

    setCreatingWorkspace(true);
    setCreateWorkspaceError("");

    try {
      if (auth.mode === "demo") {
        const nextWorkspace = {
          id: Date.now(),
          name: trimmedName,
          description: trimmedDescription,
        };
        const nextWorkspaces = sortWorkspaces([...demoWorkspaceRows, nextWorkspace]);
        setDemoWorkspaceRows(nextWorkspaces);
        setWorkspacesState({
          data: nextWorkspaces,
          error: "",
          loading: false,
        });
        ui.selectWorkspace(nextWorkspace.id);
        return true;
      }

      const created = await auth.apiRequest("/workspaces/", {
        method: "POST",
        body: {
          name: trimmedName,
          description: trimmedDescription,
        },
      });
      setWorkspacesState((current) => ({
        ...current,
        data: sortWorkspaces([...current.data, created]),
      }));
      ui.selectWorkspace(created.id);
      return true;
    } catch (workspaceError) {
      setCreateWorkspaceError(workspaceError.message);
      return false;
    } finally {
      setCreatingWorkspace(false);
    }
  }, [auth, demoWorkspaceRows, ui]);

  const clearCreateWorkspaceError = useCallback(() => {
    setCreateWorkspaceError("");
  }, []);

  const createChannel = useCallback(async ({ name, topic }) => {
    const trimmedName = name.trim();
    const trimmedTopic = topic.trim();
    const workspaceId = ui.selectedWorkspaceId;

    if (!trimmedName || !workspaceId) {
      return false;
    }

    setCreatingChannel(true);
    setCreateChannelError("");

    try {
      if (auth.mode === "demo") {
        const nextChannel = {
          id: Date.now(),
          workspace_id: workspaceId,
          name: trimmedName,
          topic: trimmedTopic,
        };
        const nextChannels = sortChannels([...demoChannelRows, nextChannel]);
        setDemoChannelRows(nextChannels);
        setChannelsState({
          data: nextChannels.filter((channel) => channel.workspace_id === workspaceId),
          error: "",
          loading: false,
        });
        ui.selectChannel(nextChannel.id);
        return true;
      }

      const created = await auth.apiRequest("/channels/", {
        method: "POST",
        body: {
          workspace_id: workspaceId,
          name: trimmedName,
          topic: trimmedTopic,
        },
      });
      if (
        selectedWorkspaceIdRef.current === workspaceId
        && created.workspace_id === workspaceId
      ) {
        setChannelsState((current) => ({
          ...current,
          data: sortChannels([...current.data, created]),
        }));
        ui.selectChannel(created.id);
      }
      return true;
    } catch (channelError) {
      setCreateChannelError(channelError.message);
      return false;
    } finally {
      setCreatingChannel(false);
    }
  }, [auth, demoChannelRows, ui]);

  const clearCreateChannelError = useCallback(() => {
    setCreateChannelError("");
  }, []);

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
    clearCreateChannelError,
    clearCreateWorkspaceError,
    createChannel,
    createChannelError,
    createWorkspace,
    createWorkspaceError,
    creatingChannel,
    creatingWorkspace,
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
  }), [channelsState.data, channelsState.error, channelsState.loading, clearCreateChannelError, clearCreateWorkspaceError, createChannel, createChannelError, createWorkspace, createWorkspaceError, creatingChannel, creatingWorkspace, macrosState.data, macrosState.error, macrosState.loading, messagesState.data, messagesState.error, messagesState.loading, selectedChannel, selectedWorkspace, submitError, submitting, workspacesState.data, workspacesState.error, workspacesState.loading]);

  return <ServerStateContext.Provider value={value}>{children}</ServerStateContext.Provider>;
}

export function useServerState() {
  const value = useContext(ServerStateContext);
  if (!value) {
    throw new Error("useServerState must be used inside ServerStateProvider.");
  }
  return value;
}
