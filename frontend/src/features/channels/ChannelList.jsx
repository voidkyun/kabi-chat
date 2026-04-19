import { useEffect, useState } from "react";

import { useAuth } from "../auth/auth-context";
import { useServerState } from "../server-state/server-state-context";
import { useUIState } from "../ui-state/ui-state-context";

export function ChannelList() {
  const auth = useAuth();
  const server = useServerState();
  const ui = useUIState();
  const [name, setName] = useState("");
  const [topic, setTopic] = useState("");
  const canCreateChannel =
    auth.mode === "demo" || server.selectedWorkspace?.owner?.id === auth.user?.id;

  useEffect(() => {
    setName("");
    setTopic("");
    server.clearCreateChannelError();
  }, [server.clearCreateChannelError, ui.selectedWorkspaceId]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    const created = await server.createChannel({ name, topic });
    if (!created) {
      return;
    }
    setName("");
    setTopic("");
  };

  if (!ui.selectedWorkspaceId) {
    return <p className="status-copy">Select a workspace to load channels.</p>;
  }

  if (server.channelsLoading) {
    return <p className="status-copy">Loading channels...</p>;
  }

  if (server.channelsError) {
    return <p className="inline-error">{server.channelsError}</p>;
  }

  return (
    <div className="stack-list">
      {canCreateChannel ? (
        <form className="inline-form" onSubmit={handleSubmit}>
          <label className="inline-form__label" htmlFor="channel-name">
            New channel
          </label>
          <input
            id="channel-name"
            className="inline-form__input"
            type="text"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="general"
            disabled={server.creatingChannel}
          />
          <textarea
            className="inline-form__input inline-form__input--textarea"
            value={topic}
            onChange={(event) => setTopic(event.target.value)}
            placeholder="Channel topic"
            rows={3}
            disabled={server.creatingChannel}
          />
          <button
            className="primary-button"
            type="submit"
            disabled={!name.trim() || server.creatingChannel}
          >
            {server.creatingChannel ? "Creating..." : "Create channel"}
          </button>
          {server.createChannelError ? (
            <p className="inline-error">{server.createChannelError}</p>
          ) : null}
        </form>
      ) : (
        <p className="status-copy">Only the workspace owner can create channels.</p>
      )}

      {server.channels.length === 0 ? (
        <p className="status-copy">Create a channel in the selected workspace.</p>
      ) : null}

      {server.channels.map((channel) => {
        const selected = channel.id === ui.selectedChannelId;
        return (
          <button
            key={channel.id}
            type="button"
            className={`list-card${selected ? " list-card--selected" : ""}`}
            onClick={() => ui.selectChannel(channel.id)}
          >
            <span className="list-card__title">#{channel.name}</span>
            <span className="list-card__meta">{channel.topic || "No topic"}</span>
          </button>
        );
      })}
    </div>
  );
}
