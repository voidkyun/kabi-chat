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
  demoMacros as initialDemoMacros,
  demoMessages as initialDemoMessages,
  demoWorkspaces,
} from "../../shared/data/demo-data";
import { useAuth } from "../auth/auth-context";
import { useUIState } from "../ui-state/ui-state-context";
import {
  buildWorkspaceInviteUrl,
  clearPendingWorkspaceInviteToken,
  getWorkspaceInviteTokenFromLocation,
  loadPendingWorkspaceInviteToken,
  persistPendingWorkspaceInviteToken,
  stripWorkspaceInviteTokenFromLocation,
} from "../workspaces/invite-token";

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

function replaceRowById(rows, nextRow) {
  const hasExisting = rows.some((row) => row.id === nextRow.id);
  if (!hasExisting) {
    return [...rows, nextRow];
  }
  return rows.map((row) => (row.id === nextRow.id ? nextRow : row));
}

function removeRowById(rows, rowId) {
  return rows.filter((row) => row.id !== rowId);
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
  const [demoMacroRows, setDemoMacroRows] = useState(initialDemoMacros);
  const [demoMessageRows, setDemoMessageRows] = useState(initialDemoMessages);
  const [createWorkspaceError, setCreateWorkspaceError] = useState("");
  const [updateWorkspaceError, setUpdateWorkspaceError] = useState("");
  const [deleteWorkspaceError, setDeleteWorkspaceError] = useState("");
  const [createWorkspaceInviteError, setCreateWorkspaceInviteError] = useState("");
  const [createChannelError, setCreateChannelError] = useState("");
  const [updateChannelError, setUpdateChannelError] = useState("");
  const [deleteChannelError, setDeleteChannelError] = useState("");
  const [submitError, setSubmitError] = useState("");
  const [creatingWorkspace, setCreatingWorkspace] = useState(false);
  const [updatingWorkspace, setUpdatingWorkspace] = useState(false);
  const [deletingWorkspace, setDeletingWorkspace] = useState(false);
  const [creatingWorkspaceInvite, setCreatingWorkspaceInvite] = useState(false);
  const [creatingChannel, setCreatingChannel] = useState(false);
  const [updatingChannel, setUpdatingChannel] = useState(false);
  const [deletingChannel, setDeletingChannel] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [workspaceInviteUrl, setWorkspaceInviteUrl] = useState("");
  const [acceptingWorkspaceInvite, setAcceptingWorkspaceInvite] = useState(false);
  const [workspaceInviteAcceptanceError, setWorkspaceInviteAcceptanceError] = useState("");
  const [workspaceInviteAcceptanceMessage, setWorkspaceInviteAcceptanceMessage] = useState("");
  const selectedWorkspaceIdRef = useRef(ui.selectedWorkspaceId);

  useEffect(() => {
    selectedWorkspaceIdRef.current = ui.selectedWorkspaceId;
  }, [ui.selectedWorkspaceId]);

  useEffect(() => {
    if (auth.mode !== "demo") {
      setDemoWorkspaceRows(demoWorkspaces);
      setDemoChannelRows(demoChannels);
      setDemoMacroRows(initialDemoMacros);
      setDemoMessageRows(initialDemoMessages);
    }
  }, [auth.mode]);

  useEffect(() => {
    const tokenFromLocation = getWorkspaceInviteTokenFromLocation();
    if (!tokenFromLocation) {
      return;
    }

    persistPendingWorkspaceInviteToken(tokenFromLocation);
    if (auth.status === "authenticated") {
      stripWorkspaceInviteTokenFromLocation();
    }
  }, [auth.status]);

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
    if (auth.mode !== "api" || auth.status !== "authenticated") {
      return;
    }

    const token = loadPendingWorkspaceInviteToken();
    if (!token) {
      return;
    }

    let cancelled = false;
    setAcceptingWorkspaceInvite(true);
    setWorkspaceInviteAcceptanceError("");
    setWorkspaceInviteAcceptanceMessage("");
    clearPendingWorkspaceInviteToken();
    stripWorkspaceInviteTokenFromLocation();

    auth
      .apiRequest("/workspaces/invites/accept/", {
        method: "POST",
        body: { token },
      })
      .then((payload) => {
        if (cancelled) {
          return;
        }
        setWorkspacesState((current) => ({
          ...current,
          data: sortWorkspaces(replaceRowById(current.data, payload.workspace)),
        }));
        setWorkspaceInviteAcceptanceMessage(
          payload.joined
            ? `${payload.workspace.name} に参加しました。`
            : `${payload.workspace.name} にはすでに参加しています。`,
        );
        ui.selectWorkspace(payload.workspace.id);
      })
      .catch((inviteError) => {
        if (cancelled) {
          return;
        }
        setWorkspaceInviteAcceptanceError(inviteError.message);
      })
      .finally(() => {
        if (!cancelled) {
          setAcceptingWorkspaceInvite(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [auth.apiRequest, auth.mode, auth.status, ui.selectWorkspace]);

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
      const rows = demoMacroRows.filter((macro) => {
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
  }, [auth, demoMacroRows, ui.selectedChannelId, ui.selectedWorkspaceId]);

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

  const clearWorkspaceManagementState = useCallback(() => {
    setUpdateWorkspaceError("");
    setDeleteWorkspaceError("");
    setCreateWorkspaceInviteError("");
    setWorkspaceInviteUrl("");
  }, []);

  const clearWorkspaceInviteAcceptanceState = useCallback(() => {
    setWorkspaceInviteAcceptanceError("");
    setWorkspaceInviteAcceptanceMessage("");
  }, []);

  const updateWorkspace = useCallback(async ({ workspaceId, description, name }) => {
    const trimmedName = name.trim();
    const trimmedDescription = description.trim();

    if (!trimmedName || !workspaceId) {
      return false;
    }

    setUpdatingWorkspace(true);
    setUpdateWorkspaceError("");

    try {
      if (auth.mode === "demo") {
        const nextWorkspaces = sortWorkspaces(
          demoWorkspaceRows.map((workspace) => (
            workspace.id === workspaceId
              ? { ...workspace, name: trimmedName, description: trimmedDescription }
              : workspace
          )),
        );
        setDemoWorkspaceRows(nextWorkspaces);
        setWorkspacesState({
          data: nextWorkspaces,
          error: "",
          loading: false,
        });
        return true;
      }

      const updated = await auth.apiRequest(`/workspaces/${workspaceId}/`, {
        method: "PATCH",
        body: {
          name: trimmedName,
          description: trimmedDescription,
        },
      });
      setWorkspacesState((current) => ({
        ...current,
        data: sortWorkspaces(replaceRowById(current.data, updated)),
      }));
      return true;
    } catch (workspaceError) {
      setUpdateWorkspaceError(workspaceError.message);
      return false;
    } finally {
      setUpdatingWorkspace(false);
    }
  }, [auth, demoWorkspaceRows]);

  const deleteWorkspace = useCallback(async (workspaceId) => {
    if (!workspaceId) {
      return false;
    }

    setDeletingWorkspace(true);
    setDeleteWorkspaceError("");

    try {
      if (auth.mode === "demo") {
        const nextChannels = demoChannelRows.filter((channel) => channel.workspace_id !== workspaceId);
        const deletedChannelIds = new Set(
          demoChannelRows
            .filter((channel) => channel.workspace_id === workspaceId)
            .map((channel) => channel.id),
        );
        const nextWorkspaces = sortWorkspaces(
          demoWorkspaceRows.filter((workspace) => workspace.id !== workspaceId),
        );
        setDemoWorkspaceRows(nextWorkspaces);
        setDemoChannelRows(nextChannels);
        setDemoMacroRows(
          demoMacroRows.filter((macro) => {
            if (macro.workspace_id === workspaceId) {
              return false;
            }
            return !deletedChannelIds.has(macro.channel_id);
          }),
        );
        setDemoMessageRows(
          demoMessageRows.filter((message) => !deletedChannelIds.has(message.channel_id)),
        );
        setWorkspacesState({
          data: nextWorkspaces,
          error: "",
          loading: false,
        });
        setChannelsState((current) => ({
          ...current,
          data: current.data.filter((channel) => channel.workspace_id !== workspaceId),
        }));
        return true;
      }

      await auth.apiRequest(`/workspaces/${workspaceId}/`, {
        method: "DELETE",
      });
      setWorkspacesState((current) => ({
        ...current,
        data: sortWorkspaces(removeRowById(current.data, workspaceId)),
      }));
      return true;
    } catch (workspaceError) {
      setDeleteWorkspaceError(workspaceError.message);
      return false;
    } finally {
      setDeletingWorkspace(false);
    }
  }, [auth, demoChannelRows, demoMacroRows, demoMessageRows, demoWorkspaceRows]);

  const createWorkspaceInvite = useCallback(async (workspaceId) => {
    if (!workspaceId) {
      return "";
    }

    setCreatingWorkspaceInvite(true);
    setCreateWorkspaceInviteError("");

    try {
      if (auth.mode === "demo") {
        const inviteUrl = buildWorkspaceInviteUrl(`demo-${workspaceId}-${Date.now()}`);
        setWorkspaceInviteUrl(inviteUrl);
        return inviteUrl;
      }

      const created = await auth.apiRequest(`/workspaces/${workspaceId}/invites/`, {
        method: "POST",
      });
      const inviteUrl = buildWorkspaceInviteUrl(created.invite_token);
      setWorkspaceInviteUrl(inviteUrl);
      return inviteUrl;
    } catch (inviteError) {
      setCreateWorkspaceInviteError(inviteError.message);
      return "";
    } finally {
      setCreatingWorkspaceInvite(false);
    }
  }, [auth]);

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

  const clearChannelManagementState = useCallback(() => {
    setUpdateChannelError("");
    setDeleteChannelError("");
  }, []);

  const updateChannel = useCallback(async ({ channelId, name, topic }) => {
    const trimmedName = name.trim();
    const trimmedTopic = topic.trim();

    if (!trimmedName || !channelId) {
      return false;
    }

    setUpdatingChannel(true);
    setUpdateChannelError("");

    try {
      if (auth.mode === "demo") {
        const nextChannels = sortChannels(
          demoChannelRows.map((channel) => (
            channel.id === channelId
              ? { ...channel, name: trimmedName, topic: trimmedTopic }
              : channel
          )),
        );
        setDemoChannelRows(nextChannels);
        setChannelsState({
          data: nextChannels.filter((channel) => channel.workspace_id === ui.selectedWorkspaceId),
          error: "",
          loading: false,
        });
        return true;
      }

      const updated = await auth.apiRequest(`/channels/${channelId}/`, {
        method: "PATCH",
        body: {
          name: trimmedName,
          topic: trimmedTopic,
        },
      });
      if (selectedWorkspaceIdRef.current === updated.workspace_id) {
        setChannelsState((current) => ({
          ...current,
          data: sortChannels(replaceRowById(current.data, updated)),
        }));
      }
      return true;
    } catch (channelError) {
      setUpdateChannelError(channelError.message);
      return false;
    } finally {
      setUpdatingChannel(false);
    }
  }, [auth, demoChannelRows, ui.selectedWorkspaceId]);

  const deleteChannel = useCallback(async (channelId) => {
    if (!channelId) {
      return false;
    }

    setDeletingChannel(true);
    setDeleteChannelError("");

    try {
      if (auth.mode === "demo") {
        const nextChannels = sortChannels(
          demoChannelRows.filter((channel) => channel.id !== channelId),
        );
        setDemoChannelRows(nextChannels);
        setDemoMacroRows(
          demoMacroRows.filter((macro) => macro.channel_id !== channelId),
        );
        setDemoMessageRows(
          demoMessageRows.filter((message) => message.channel_id !== channelId),
        );
        setChannelsState({
          data: nextChannels.filter((channel) => channel.workspace_id === ui.selectedWorkspaceId),
          error: "",
          loading: false,
        });
        return true;
      }

      await auth.apiRequest(`/channels/${channelId}/`, {
        method: "DELETE",
      });
      setChannelsState((current) => ({
        ...current,
        data: sortChannels(removeRowById(current.data, channelId)),
      }));
      return true;
    } catch (channelError) {
      setDeleteChannelError(channelError.message);
      return false;
    } finally {
      setDeletingChannel(false);
    }
  }, [auth, demoChannelRows, demoMacroRows, demoMessageRows, ui.selectedWorkspaceId]);

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
    acceptingWorkspaceInvite,
    channels: channelsState.data,
    channelsError: channelsState.error,
    channelsLoading: channelsState.loading,
    clearCreateChannelError,
    clearCreateWorkspaceError,
    clearChannelManagementState,
    clearWorkspaceInviteAcceptanceState,
    clearWorkspaceManagementState,
    createChannel,
    createChannelError,
    createWorkspaceInvite,
    createWorkspaceInviteError,
    createWorkspace,
    createWorkspaceError,
    creatingChannel,
    creatingWorkspaceInvite,
    creatingWorkspace,
    deleteChannel,
    deleteChannelError,
    deleteWorkspace,
    deleteWorkspaceError,
    deletingChannel,
    deletingWorkspace,
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
    updateChannel,
    updateChannelError,
    updateWorkspace,
    updateWorkspaceError,
    updatingChannel,
    updatingWorkspace,
    workspaceInviteAcceptanceError,
    workspaceInviteAcceptanceMessage,
    workspaceInviteUrl,
    workspaces: workspacesState.data,
    workspacesError: workspacesState.error,
    workspacesLoading: workspacesState.loading,
  }), [acceptingWorkspaceInvite, channelsState.data, channelsState.error, channelsState.loading, clearChannelManagementState, clearCreateChannelError, clearCreateWorkspaceError, clearWorkspaceInviteAcceptanceState, clearWorkspaceManagementState, createChannel, createChannelError, createWorkspace, createWorkspaceError, createWorkspaceInvite, createWorkspaceInviteError, creatingChannel, creatingWorkspace, creatingWorkspaceInvite, deleteChannel, deleteChannelError, deleteWorkspace, deleteWorkspaceError, deletingChannel, deletingWorkspace, macrosState.data, macrosState.error, macrosState.loading, messagesState.data, messagesState.error, messagesState.loading, selectedChannel, selectedWorkspace, submitError, submitting, updateChannel, updateChannelError, updateWorkspace, updateWorkspaceError, updatingChannel, updatingWorkspace, workspaceInviteAcceptanceError, workspaceInviteAcceptanceMessage, workspaceInviteUrl, workspacesState.data, workspacesState.error, workspacesState.loading]);

  return <ServerStateContext.Provider value={value}>{children}</ServerStateContext.Provider>;
}

export function useServerState() {
  const value = useContext(ServerStateContext);
  if (!value) {
    throw new Error("useServerState must be used inside ServerStateProvider.");
  }
  return value;
}
