import { useState } from "react";

import { useServerState } from "../server-state/server-state-context";
import { useUIState } from "../ui-state/ui-state-context";

export function WorkspaceList() {
  const server = useServerState();
  const ui = useUIState();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  const handleSubmit = async (event) => {
    event.preventDefault();
    const created = await server.createWorkspace({ description, name });
    if (!created) {
      return;
    }
    setName("");
    setDescription("");
  };

  if (server.workspacesLoading) {
    return <p className="status-copy">Loading workspaces...</p>;
  }

  if (server.workspacesError) {
    return <p className="inline-error">{server.workspacesError}</p>;
  }

  return (
    <div className="stack-list">
      <form className="inline-form" onSubmit={handleSubmit}>
        <label className="inline-form__label" htmlFor="workspace-name">
          New workspace
        </label>
        <input
          id="workspace-name"
          className="inline-form__input"
          type="text"
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="Workspace name"
          disabled={server.creatingWorkspace}
        />
        <textarea
          className="inline-form__input inline-form__input--textarea"
          value={description}
          onChange={(event) => setDescription(event.target.value)}
          placeholder="Short description"
          rows={3}
          disabled={server.creatingWorkspace}
        />
        <button
          className="primary-button"
          type="submit"
          disabled={!name.trim() || server.creatingWorkspace}
        >
          {server.creatingWorkspace ? "Creating..." : "Create workspace"}
        </button>
        {server.createWorkspaceError ? (
          <p className="inline-error">{server.createWorkspaceError}</p>
        ) : null}
      </form>

      {server.workspaces.length === 0 ? (
        <p className="status-copy">Create a workspace to start the chat flow.</p>
      ) : null}

      {server.workspaces.map((workspace) => {
        const selected = workspace.id === ui.selectedWorkspaceId;
        return (
          <button
            key={workspace.id}
            type="button"
            className={`list-card${selected ? " list-card--selected" : ""}`}
            onClick={() => ui.selectWorkspace(workspace.id)}
          >
            <span className="list-card__title">{workspace.name}</span>
            <span className="list-card__meta">{workspace.description || "No description"}</span>
          </button>
        );
      })}
    </div>
  );
}
