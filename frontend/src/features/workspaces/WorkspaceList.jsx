import { useEffect, useState } from "react";

import { useAuth } from "../auth/auth-context";
import { useServerState } from "../server-state/server-state-context";
import { useUIState } from "../ui-state/ui-state-context";

export function WorkspaceList() {
  const auth = useAuth();
  const server = useServerState();
  const ui = useUIState();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const canManageSelectedWorkspace =
    auth.mode === "demo" || server.selectedWorkspace?.owner?.id === auth.user?.id;

  useEffect(() => {
    setEditName(server.selectedWorkspace?.name ?? "");
    setEditDescription(server.selectedWorkspace?.description ?? "");
    server.clearWorkspaceManagementState();
  }, [
    server.clearWorkspaceManagementState,
    server.selectedWorkspace?.description,
    server.selectedWorkspace?.id,
    server.selectedWorkspace?.name,
  ]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    const created = await server.createWorkspace({ description, name });
    if (!created) {
      return;
    }
    setName("");
    setDescription("");
  };

  const handleWorkspaceUpdate = async (event) => {
    event.preventDefault();
    const updated = await server.updateWorkspace({
      workspaceId: server.selectedWorkspace?.id,
      name: editName,
      description: editDescription,
    });
    if (!updated) {
      return;
    }
  };

  const handleWorkspaceDelete = async () => {
    await server.deleteWorkspace(server.selectedWorkspace?.id);
  };

  const handleCreateInvite = async () => {
    await server.createWorkspaceInvite(server.selectedWorkspace?.id);
  };

  if (server.workspacesLoading) {
    return <p className="status-copy">Loading workspaces...</p>;
  }

  if (server.workspacesError) {
    return <p className="inline-error">{server.workspacesError}</p>;
  }

  return (
    <div className="stack-list">
      {server.acceptingWorkspaceInvite ? (
        <p className="status-copy">Joining workspace from invite...</p>
      ) : null}
      {server.workspaceInviteAcceptanceMessage ? (
        <p className="status-copy">{server.workspaceInviteAcceptanceMessage}</p>
      ) : null}
      {server.workspaceInviteAcceptanceError ? (
        <p className="inline-error">{server.workspaceInviteAcceptanceError}</p>
      ) : null}
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

      {server.selectedWorkspace ? (
        <form className="inline-form" onSubmit={handleWorkspaceUpdate}>
          <label className="inline-form__label" htmlFor="workspace-edit-name">
            Selected workspace
          </label>
          <input
            id="workspace-edit-name"
            className="inline-form__input"
            type="text"
            value={editName}
            onChange={(event) => setEditName(event.target.value)}
            disabled={!canManageSelectedWorkspace || server.updatingWorkspace || server.deletingWorkspace}
          />
          <textarea
            className="inline-form__input inline-form__input--textarea"
            value={editDescription}
            onChange={(event) => setEditDescription(event.target.value)}
            rows={3}
            disabled={!canManageSelectedWorkspace || server.updatingWorkspace || server.deletingWorkspace}
          />
          {canManageSelectedWorkspace ? (
            <div className="inline-form__actions">
              <button
                className="primary-button"
                type="button"
                onClick={handleCreateInvite}
                disabled={server.creatingWorkspaceInvite || server.deletingWorkspace}
              >
                {server.creatingWorkspaceInvite ? "Generating..." : "Generate invite link"}
              </button>
              <button
                className="secondary-button"
                type="submit"
                disabled={!editName.trim() || server.updatingWorkspace || server.deletingWorkspace}
              >
                {server.updatingWorkspace ? "Saving..." : "Save workspace"}
              </button>
              <button
                className="danger-button"
                type="button"
                onClick={handleWorkspaceDelete}
                disabled={server.deletingWorkspace || server.updatingWorkspace}
              >
                {server.deletingWorkspace ? "Deleting..." : "Delete workspace"}
              </button>
            </div>
          ) : (
            <p className="status-copy">Only the workspace owner can manage settings and invites.</p>
          )}
          {server.workspaceInviteUrl ? (
            <>
              <label className="inline-form__label" htmlFor="workspace-invite-url">
                Invite link
              </label>
              <input
                id="workspace-invite-url"
                className="inline-form__input"
                type="text"
                value={server.workspaceInviteUrl}
                readOnly
              />
              <p className="status-copy">
                この URL を共有すると、有効期限内に 1 人だけ workspace に参加できます。
              </p>
            </>
          ) : null}
          {server.createWorkspaceInviteError ? (
            <p className="inline-error">{server.createWorkspaceInviteError}</p>
          ) : null}
          {server.updateWorkspaceError ? (
            <p className="inline-error">{server.updateWorkspaceError}</p>
          ) : null}
          {server.deleteWorkspaceError ? (
            <p className="inline-error">{server.deleteWorkspaceError}</p>
          ) : null}
        </form>
      ) : null}
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
