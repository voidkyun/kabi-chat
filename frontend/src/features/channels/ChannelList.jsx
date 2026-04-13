import { useServerState } from "../server-state/server-state-context";
import { useUIState } from "../ui-state/ui-state-context";

export function ChannelList() {
  const server = useServerState();
  const ui = useUIState();

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
