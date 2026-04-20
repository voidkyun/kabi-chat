import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

const authState = vi.hoisted(() => ({ current: null }));

vi.mock("./auth/auth-context", () => ({
  useAuth: () => authState.current,
}));

import { ChannelList } from "./channels/ChannelList";
import { MessagePane } from "./messages/MessagePane";
import { ServerStateProvider } from "./server-state/server-state-context";
import { UIStateProvider, useUIState } from "./ui-state/ui-state-context";
import { WorkspaceList } from "./workspaces/WorkspaceList";

function createDeferred() {
  let resolve;
  let reject;
  const promise = new Promise((res, rej) => {
    resolve = res;
    reject = rej;
  });

  return { promise, reject, resolve };
}

function SelectionProbe() {
  const ui = useUIState();

  return (
    <div>
      <span data-testid="selected-workspace">{ui.selectedWorkspaceId ?? ""}</span>
      <span data-testid="selected-channel">{ui.selectedChannelId ?? ""}</span>
    </div>
  );
}

function renderChatFlow(children) {
  return render(
    <UIStateProvider>
      <ServerStateProvider>{children}</ServerStateProvider>
    </UIStateProvider>,
  );
}

function buildUser(overrides = {}) {
  return {
    id: 1,
    username: "owner",
    display_name: "Owner",
    avatar_url: "",
    discord_user_id: null,
    ...overrides,
  };
}

function buildWorkspace({ id, name, owner }) {
  return {
    id,
    name,
    description: "",
    owner,
    members: [owner],
    member_ids: [owner.id],
    created_at: "2026-04-19T00:00:00+09:00",
    updated_at: "2026-04-19T00:00:00+09:00",
  };
}

function buildChannel({ id, name, workspaceId, createdBy }) {
  return {
    id,
    workspace_id: workspaceId,
    name,
    topic: "",
    created_by: createdBy,
    created_at: "2026-04-19T00:00:00+09:00",
    updated_at: "2026-04-19T00:00:00+09:00",
  };
}

afterEach(() => {
  authState.current = null;
  window.sessionStorage.clear();
  window.history.replaceState({}, document.title, "/");
  vi.restoreAllMocks();
});

describe("minimum chat flow", () => {
  it("creates a workspace and channel in API mode, then shows the empty message state", async () => {
    const user = buildUser();
    const workspace = buildWorkspace({ id: 101, name: "Launch Room", owner: user });
    const channel = buildChannel({ id: 301, name: "general", workspaceId: workspace.id, createdBy: user });

    const apiRequest = vi.fn(async (path, options = {}) => {
      if (path === "/workspaces/" && !options.method) {
        return [];
      }
      if (path === "/workspaces/" && options.method === "POST") {
        return workspace;
      }
      if (path === `/channels/?workspace_id=${workspace.id}`) {
        return [];
      }
      if (path === "/channels/" && options.method === "POST") {
        return channel;
      }
      if (path === `/messages/?channel_id=${channel.id}`) {
        return [];
      }
      if (path === `/macros/?effective=true&workspace_id=${workspace.id}`) {
        return [];
      }
      if (path === `/macros/?effective=true&workspace_id=${workspace.id}&channel_id=${channel.id}`) {
        return [];
      }
      throw new Error(`Unexpected API request: ${path}`);
    });

    authState.current = {
      apiRequest,
      mode: "api",
      user,
    };

    const actor = userEvent.setup();

    renderChatFlow(
      <>
        <WorkspaceList />
        <ChannelList />
        <MessagePane />
      </>,
    );

    await screen.findByText("Create a workspace to start the chat flow.");

    await actor.type(screen.getByLabelText("New workspace"), "Launch Room");
    await actor.click(screen.getByRole("button", { name: "Create workspace" }));

    await screen.findByRole("button", { name: "Create channel" });

    expect(screen.getByLabelText("New workspace")).toHaveValue("");

    await actor.type(screen.getByLabelText("New channel"), "general");
    await actor.click(screen.getByRole("button", { name: "Create channel" }));

    await screen.findByText("No messages yet. Post the first message to start the channel.");
    expect(screen.getByLabelText("New channel")).toHaveValue("");
    expect(screen.getByRole("button", { name: /#general/ })).toBeInTheDocument();
  });

  it("hides channel creation from non-owners", async () => {
    const user = buildUser({ id: 1 });
    const owner = buildUser({ id: 2, username: "manager", display_name: "Manager" });
    const workspace = buildWorkspace({ id: 201, name: "Shared", owner });

    authState.current = {
      apiRequest: vi.fn(async (path) => {
        if (path === "/workspaces/") {
          return [workspace];
        }
        if (path === `/channels/?workspace_id=${workspace.id}`) {
          return [];
        }
        if (path === `/macros/?effective=true&workspace_id=${workspace.id}`) {
          return [];
        }
        throw new Error(`Unexpected API request: ${path}`);
      }),
      mode: "api",
      user,
    };

    renderChatFlow(<ChannelList />);

    await screen.findByText("Only the workspace owner can create channels.");
    expect(screen.queryByLabelText("New channel")).not.toBeInTheDocument();
  });

  it("keeps the newly created workspace and channel selected in demo mode", async () => {
    authState.current = {
      apiRequest: vi.fn(),
      mode: "demo",
      user: buildUser(),
    };

    const actor = userEvent.setup();
    let currentNow = 5001;
    vi.spyOn(Date, "now").mockImplementation(() => currentNow);

    renderChatFlow(
      <>
        <WorkspaceList />
        <ChannelList />
        <SelectionProbe />
      </>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("selected-workspace")).toHaveTextContent("1");
    });

    await actor.type(screen.getByLabelText("New workspace"), "Zeta");
    await actor.click(screen.getByRole("button", { name: "Create workspace" }));

    await waitFor(() => {
      expect(screen.getByTestId("selected-workspace")).toHaveTextContent("5001");
    });

    currentNow = 6001;
    await actor.type(screen.getByLabelText("New channel"), "fresh-room");
    await actor.click(screen.getByRole("button", { name: "Create channel" }));

    await waitFor(() => {
      expect(screen.getByTestId("selected-channel")).toHaveTextContent("6001");
    });
  });

  it("shows channel creation errors and keeps the draft intact", async () => {
    const user = buildUser();
    const workspace = buildWorkspace({ id: 301, name: "Errors", owner: user });

    authState.current = {
      apiRequest: vi.fn(async (path, options = {}) => {
        if (path === "/workspaces/") {
          return [workspace];
        }
        if (path === `/channels/?workspace_id=${workspace.id}`) {
          return [];
        }
        if (path === "/channels/" && options.method === "POST") {
          throw new Error("Channel create failed");
        }
        if (path === `/macros/?effective=true&workspace_id=${workspace.id}`) {
          return [];
        }
        throw new Error(`Unexpected API request: ${path}`);
      }),
      mode: "api",
      user,
    };

    const actor = userEvent.setup();

    renderChatFlow(<ChannelList />);

    await screen.findByRole("button", { name: "Create channel" });

    const input = screen.getByLabelText("New channel");
    await actor.type(input, "broken-room");
    await actor.click(screen.getByRole("button", { name: "Create channel" }));

    await screen.findByText("Channel create failed");
    expect(input).toHaveValue("broken-room");
    expect(screen.getByRole("button", { name: "Create channel" })).toBeEnabled();
  });

  it("shows workspace creation errors and keeps the drafts intact", async () => {
    authState.current = {
      apiRequest: vi.fn(async (path, options = {}) => {
        if (path === "/workspaces/" && !options.method) {
          return [];
        }
        if (path === "/workspaces/" && options.method === "POST") {
          throw new Error("Workspace create failed");
        }
        throw new Error(`Unexpected API request: ${path}`);
      }),
      mode: "api",
      user: buildUser(),
    };

    const actor = userEvent.setup();

    renderChatFlow(<WorkspaceList />);

    const nameInput = await screen.findByLabelText("New workspace");
    const descriptionInput = screen.getByPlaceholderText("Short description");

    await actor.type(nameInput, "Broken Workspace");
    await actor.type(descriptionInput, "Still drafting");
    await actor.click(screen.getByRole("button", { name: "Create workspace" }));

    await screen.findByText("Workspace create failed");
    expect(nameInput).toHaveValue("Broken Workspace");
    expect(descriptionInput).toHaveValue("Still drafting");
    expect(screen.getByRole("button", { name: "Create workspace" })).toBeEnabled();
  });

  it("does not leak a created channel into a different workspace after switching", async () => {
    const user = buildUser();
    const workspaceA = buildWorkspace({ id: 401, name: "Alpha", owner: user });
    const workspaceB = buildWorkspace({ id: 402, name: "Beta", owner: user });
    const deferred = createDeferred();

    authState.current = {
      apiRequest: vi.fn(async (path, options = {}) => {
        if (path === "/workspaces/") {
          return [workspaceA, workspaceB];
        }
        if (path === `/channels/?workspace_id=${workspaceA.id}`) {
          return [];
        }
        if (path === `/channels/?workspace_id=${workspaceB.id}`) {
          return [buildChannel({ id: 901, name: "beta-room", workspaceId: workspaceB.id, createdBy: user })];
        }
        if (path === "/channels/" && options.method === "POST") {
          return deferred.promise;
        }
        if (path === `/macros/?effective=true&workspace_id=${workspaceA.id}`) {
          return [];
        }
        if (path === `/macros/?effective=true&workspace_id=${workspaceB.id}`) {
          return [];
        }
        throw new Error(`Unexpected API request: ${path}`);
      }),
      mode: "api",
      user,
    };

    const actor = userEvent.setup();

    renderChatFlow(
      <>
        <WorkspaceList />
        <ChannelList />
      </>,
    );

    await screen.findByRole("button", { name: "Create channel" });

    await actor.type(screen.getByLabelText("New channel"), "alpha-room");
    await actor.click(screen.getByRole("button", { name: "Create channel" }));
    await actor.click(screen.getByRole("button", { name: /Beta/ }));

    await act(async () => {
      deferred.resolve(
        buildChannel({ id: 902, name: "alpha-room", workspaceId: workspaceA.id, createdBy: user }),
      );
      await deferred.promise;
    });

    await screen.findByRole("button", { name: /#beta-room/ });
    expect(screen.queryByRole("button", { name: /#alpha-room/ })).not.toBeInTheDocument();
  });

  it("accepts a pending workspace invite after authentication", async () => {
    const user = buildUser();
    const workspace = buildWorkspace({ id: 501, name: "Invited Room", owner: buildUser({ id: 9 }) });

    window.sessionStorage.setItem("kabi-chat.pending-workspace-invite", "invite-token");

    authState.current = {
      apiRequest: vi.fn(async (path, options = {}) => {
        if (path === "/workspaces/") {
          return [];
        }
        if (path === "/workspaces/invites/accept/" && options.method === "POST") {
          return {
            joined: true,
            workspace,
          };
        }
        if (path === `/channels/?workspace_id=${workspace.id}`) {
          return [];
        }
        if (path === `/macros/?effective=true&workspace_id=${workspace.id}`) {
          return [];
        }
        throw new Error(`Unexpected API request: ${path}`);
      }),
      mode: "api",
      status: "authenticated",
      user,
    };

    renderChatFlow(<WorkspaceList />);

    await screen.findByText("Invited Room に参加しました。");
    expect(screen.getByRole("button", { name: /Invited Room/ })).toBeInTheDocument();
    expect(window.sessionStorage.getItem("kabi-chat.pending-workspace-invite")).toBeNull();
  });

  it("clears the pending invite token before the acceptance request resolves", async () => {
    const user = buildUser();
    const workspace = buildWorkspace({ id: 601, name: "Async Invite", owner: buildUser({ id: 9 }) });
    const deferred = createDeferred();

    window.sessionStorage.setItem("kabi-chat.pending-workspace-invite", "invite-token");

    authState.current = {
      apiRequest: vi.fn(async (path, options = {}) => {
        if (path === "/workspaces/") {
          return [];
        }
        if (path === "/workspaces/invites/accept/" && options.method === "POST") {
          return deferred.promise;
        }
        if (path === `/channels/?workspace_id=${workspace.id}`) {
          return [];
        }
        if (path === `/macros/?effective=true&workspace_id=${workspace.id}`) {
          return [];
        }
        throw new Error(`Unexpected API request: ${path}`);
      }),
      mode: "api",
      status: "authenticated",
      user,
    };

    renderChatFlow(<WorkspaceList />);

    await waitFor(() => {
      expect(window.sessionStorage.getItem("kabi-chat.pending-workspace-invite")).toBeNull();
    });

    await act(async () => {
      deferred.resolve({
        joined: true,
        workspace,
      });
      await deferred.promise;
    });

    await screen.findByText("Async Invite に参加しました。");
  });

  it("updates and deletes the selected workspace and channel in demo mode", async () => {
    authState.current = {
      apiRequest: vi.fn(),
      mode: "demo",
      status: "authenticated",
      user: buildUser(),
    };

    const actor = userEvent.setup();

    renderChatFlow(
      <>
        <WorkspaceList />
        <ChannelList />
        <SelectionProbe />
      </>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("selected-workspace")).toHaveTextContent("1");
      expect(screen.getByTestId("selected-channel")).toHaveTextContent("101");
    });

    await actor.clear(screen.getByLabelText("Selected workspace"));
    await actor.type(screen.getByLabelText("Selected workspace"), "Kabi Core Updated");
    await actor.click(screen.getByRole("button", { name: "Save workspace" }));
    expect(screen.getByRole("button", { name: /Kabi Core Updated/ })).toBeInTheDocument();

    await actor.clear(screen.getByLabelText("Selected channel"));
    await actor.type(screen.getByLabelText("Selected channel"), "general-updated");
    await actor.click(screen.getByRole("button", { name: "Save channel" }));
    expect(screen.getByRole("button", { name: /#general-updated/ })).toBeInTheDocument();

    await actor.click(screen.getByRole("button", { name: "Delete channel" }));
    await waitFor(() => {
      expect(screen.getByTestId("selected-channel")).toHaveTextContent("102");
    });

    await actor.click(screen.getByRole("button", { name: "Delete workspace" }));
    await waitFor(() => {
      expect(screen.getByTestId("selected-workspace")).toHaveTextContent("2");
    });
    expect(screen.queryByRole("button", { name: /Kabi Core Updated/ })).not.toBeInTheDocument();
  });
});
