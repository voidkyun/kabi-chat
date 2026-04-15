import { useServerState } from "../server-state/server-state-context";
import { useUIState } from "../ui-state/ui-state-context";

export function WorkspaceList() {
  const server = useServerState();
  const ui = useUIState();

  if (server.workspacesLoading) {
    return <p className="status-copy">Loading workspaces...</p>;
  }

  if (server.workspacesError) {
    return <p className="inline-error">{server.workspacesError}</p>;
  }

  return (
    <div className="stack-list">
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
