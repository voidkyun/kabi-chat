import { AuthProvider, useAuth } from "../features/auth/auth-context";
import { AuthCallbackScreen } from "../features/auth/AuthCallbackScreen";
import { AuthScreen } from "../features/auth/AuthScreen";
import { ServerStateProvider } from "../features/server-state/server-state-context";
import { UIStateProvider, useUIState } from "../features/ui-state/ui-state-context";
import { ChannelList } from "../features/channels/ChannelList";
import { MacroPanel } from "../features/macros/MacroPanel";
import { MessagePane } from "../features/messages/MessagePane";
import { WorkspaceList } from "../features/workspaces/WorkspaceList";

function AppContent() {
  const auth = useAuth();

  if (auth.isHandlingCallback) {
    return <AuthCallbackScreen />;
  }

  if (auth.status !== "authenticated") {
    return <AuthScreen />;
  }

  return (
    <UIStateProvider>
      <ServerStateProvider>
        <MainScreen />
      </ServerStateProvider>
    </UIStateProvider>
  );
}

function MainScreen() {
  const auth = useAuth();
  const ui = useUIState();

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Authenticated Workspace</p>
          <h1>Kabi Chat SPA Skeleton</h1>
        </div>
        <div className="topbar-actions">
          <div className="user-chip">
            <span className="user-chip__label">{auth.user.display_name}</span>
            <span className="user-chip__meta">
              {auth.mode === "demo" ? "demo mode" : "jwt session"}
            </span>
          </div>
          <button className="secondary-button" type="button" onClick={auth.logout}>
            Log out
          </button>
        </div>
      </header>

      <main className="workspace-layout">
        <section className="panel panel--workspace">
          <div className="panel__header">
            <div>
              <p className="eyebrow">UI State</p>
              <h2>Workspaces</h2>
            </div>
            {ui.selectedWorkspaceId ? (
              <span className="panel__meta">selected #{ui.selectedWorkspaceId}</span>
            ) : null}
          </div>
          <WorkspaceList />
        </section>

        <section className="panel panel--channel">
          <div className="panel__header">
            <div>
              <p className="eyebrow">Server State</p>
              <h2>Channels</h2>
            </div>
            {ui.selectedChannelId ? (
              <span className="panel__meta">selected #{ui.selectedChannelId}</span>
            ) : null}
          </div>
          <ChannelList />
        </section>

        <section className="panel panel--message">
          <MessagePane />
        </section>

        <aside className="panel panel--macro">
          <MacroPanel />
        </aside>
      </main>
    </div>
  );
}

export function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
