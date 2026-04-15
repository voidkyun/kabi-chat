import { useServerState } from "../server-state/server-state-context";

export function MacroPanel() {
  const server = useServerState();

  return (
    <div>
      <div className="panel__header">
        <div>
          <p className="eyebrow">Server State</p>
          <h2>Effective TeX Macros</h2>
        </div>
      </div>

      {server.macrosLoading ? <p className="status-copy">Loading macros...</p> : null}
      {server.macrosError ? <p className="inline-error">{server.macrosError}</p> : null}

      <div className="macro-list">
        {server.macros.map((macro) => (
          <article key={macro.id} className="macro-card">
            <div className="macro-card__header">
              <strong>{macro.name}</strong>
              <span className="macro-card__scope">{macro.scope}</span>
            </div>
            <p className="macro-card__body">{`${macro.name} -> ${macro.definition}`}</p>
          </article>
        ))}
        {!server.macrosLoading && server.macros.length === 0 ? (
          <p className="status-copy">No effective TeX macros for the current selection.</p>
        ) : null}
      </div>
    </div>
  );
}
