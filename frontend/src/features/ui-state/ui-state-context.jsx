import { createContext, useCallback, useContext, useMemo, useState } from "react";

const UIStateContext = createContext(null);

export function UIStateProvider({ children }) {
  const [selectedWorkspaceId, setSelectedWorkspaceId] = useState(null);
  const [selectedChannelId, setSelectedChannelId] = useState(null);
  const [messageModes, setMessageModes] = useState({});
  const [composerDraft, setComposerDraft] = useState("");

  const selectWorkspace = useCallback((workspaceId) => {
    setSelectedWorkspaceId(workspaceId);
    setSelectedChannelId(null);
  }, []);

  const selectChannel = useCallback((channelId) => {
    setSelectedChannelId(channelId);
  }, []);

  const toggleMessageMode = useCallback((messageId) => {
    setMessageModes((current) => ({
      ...current,
      [messageId]: current[messageId] === "raw" ? "view" : "raw",
    }));
  }, []);

  const resetComposerDraft = useCallback(() => {
    setComposerDraft("");
  }, []);

  const value = useMemo(() => ({
    composerDraft,
    resetComposerDraft,
    selectChannel,
    selectedChannelId,
    selectedWorkspaceId,
    selectWorkspace,
    setComposerDraft,
    setSelectedChannelId,
    setSelectedWorkspaceId,
    toggleMessageMode,
    viewModeByMessageId: messageModes,
  }), [composerDraft, messageModes, resetComposerDraft, selectChannel, selectedChannelId, selectedWorkspaceId, selectWorkspace]);

  return <UIStateContext.Provider value={value}>{children}</UIStateContext.Provider>;
}

export function useUIState() {
  const value = useContext(UIStateContext);
  if (!value) {
    throw new Error("useUIState must be used inside UIStateProvider.");
  }
  return value;
}
