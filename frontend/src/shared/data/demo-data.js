export const demoUser = {
  id: 1,
  username: "demo-user",
  display_name: "Demo User",
  avatar_url: "",
  discord_user_id: null,
};

export const demoWorkspaces = [
  {
    id: 1,
    name: "Kabi Core",
    description: "MVP backlog and rollout discussions.",
  },
  {
    id: 2,
    name: "Math Lab",
    description: "Markdown + TeX rendering experiments.",
  },
];

export const demoChannels = [
  {
    id: 101,
    workspace_id: 1,
    name: "general",
    topic: "Project overview and daily coordination.",
  },
  {
    id: 102,
    workspace_id: 1,
    name: "frontend",
    topic: "SPA structure, auth flow, and screen composition.",
  },
  {
    id: 201,
    workspace_id: 2,
    name: "rendering",
    topic: "Formula preview and renderer behavior.",
  },
];

export const demoMessages = [
  {
    id: 1001,
    channel_id: 102,
    body: "# Frontend shell\n\n- workspace / channel / message の責務を分離する\n- raw/view 切替を UI state に持つ",
    author: demoUser,
    created_at: "2026-04-13T09:00:00+09:00",
  },
  {
    id: 1002,
    channel_id: 102,
    body: "Composer はこの段階では投稿骨格に留め、API 連携は /messages に揃える。",
    author: {
      id: 2,
      username: "reviewer",
      display_name: "Frontend Reviewer",
      avatar_url: "",
      discord_user_id: null,
    },
    created_at: "2026-04-13T09:18:00+09:00",
  },
  {
    id: 2001,
    channel_id: 201,
    body: "View mode では将来的に Markdown + TeX を描画する。",
    author: demoUser,
    created_at: "2026-04-13T10:30:00+09:00",
  },
];

export const demoMacros = [
  {
    id: 301,
    name: "/summary",
    definition: "議論を 3 行で要約する",
    scope: "workspace",
    workspace_id: 1,
    channel_id: null,
  },
  {
    id: 302,
    name: "/tex-check",
    definition: "数式表現を確認し、必要な TeX 記法に整える",
    scope: "channel",
    workspace_id: null,
    channel_id: 201,
  },
];
