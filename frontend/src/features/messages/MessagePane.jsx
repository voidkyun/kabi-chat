import { useMemo } from "react";

import { useServerState } from "../server-state/server-state-context";
import { useUIState } from "../ui-state/ui-state-context";

function formatDate(value) {
  return new Intl.DateTimeFormat("ja-JP", {
    hour: "2-digit",
    minute: "2-digit",
    month: "2-digit",
    day: "2-digit",
  }).format(new Date(value));
}

function MessageBody({ messageId, body }) {
  const ui = useUIState();
  const mode = ui.viewModeByMessageId[messageId] === "raw" ? "raw" : "view";

  if (mode === "raw") {
    return <pre className="message-card__body message-card__body--raw">{body}</pre>;
  }

  return <div className="message-card__body">{body}</div>;
}

export function MessagePane() {
  const server = useServerState();
  const ui = useUIState();

  const title = useMemo(() => {
    if (!server.selectedWorkspace) {
      return "Main View";
    }
    if (!server.selectedChannel) {
      return server.selectedWorkspace.name;
    }
    return `${server.selectedWorkspace.name} / #${server.selectedChannel.name}`;
  }, [server.selectedChannel, server.selectedWorkspace]);

  return (
    <div className="message-pane">
      <div className="panel__header panel__header--message">
        <div>
          <p className="eyebrow">Authenticated Main Screen</p>
          <h2>{title}</h2>
          <p className="panel__description">
            message list と composer は同じ channel 選択に接続されています。
          </p>
        </div>
      </div>

      <div className="message-stream">
        {!ui.selectedChannelId ? (
          <p className="status-copy">Select a channel to inspect the message stream.</p>
        ) : null}
        {server.messagesLoading ? <p className="status-copy">Loading messages...</p> : null}
        {server.messagesError ? <p className="inline-error">{server.messagesError}</p> : null}
        {server.messages.map((message) => {
          const rawMode = ui.viewModeByMessageId[message.id] === "raw";
          return (
            <article key={message.id} className="message-card">
              <header className="message-card__header">
                <div>
                  <p className="message-card__author">{message.author.display_name}</p>
                  <p className="message-card__timestamp">{formatDate(message.created_at)}</p>
                </div>
                <button
                  className="mode-toggle"
                  type="button"
                  onClick={() => ui.toggleMessageMode(message.id)}
                >
                  {rawMode ? "Switch to view" : "Switch to raw"}
                </button>
              </header>
              <MessageBody messageId={message.id} body={message.body} />
            </article>
          );
        })}
      </div>

      <form
        className="composer"
        onSubmit={async (event) => {
          event.preventDefault();
          await server.submitMessage();
        }}
      >
        <label className="composer__label" htmlFor="composer-input">
          Message Composer
        </label>
        <textarea
          id="composer-input"
          className="composer__input"
          value={ui.composerDraft}
          onChange={(event) => ui.setComposerDraft(event.target.value)}
          placeholder="Type a message for the selected channel"
          rows={5}
          disabled={!ui.selectedChannelId || server.submitting}
        />
        <div className="composer__footer">
          <span className="panel__meta">
            {ui.selectedChannelId
              ? `channel_id=${ui.selectedChannelId}`
              : "channel is not selected"}
          </span>
          <button
            className="primary-button"
            type="submit"
            disabled={!ui.selectedChannelId || !ui.composerDraft.trim() || server.submitting}
          >
            {server.submitting ? "Posting..." : "Post message"}
          </button>
        </div>
        {server.submitError ? <p className="inline-error">{server.submitError}</p> : null}
      </form>
    </div>
  );
}
