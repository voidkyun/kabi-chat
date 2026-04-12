from .models import MacroDefinition


def resolve_effective_macros(*, workspace=None, channel=None):
    if channel is not None:
        workspace = channel.workspace

    resolved = {
        macro.name: macro
        for macro in MacroDefinition.objects.filter(scope=MacroDefinition.Scope.GLOBAL).order_by("name", "id")
    }

    if workspace is not None:
        for macro in MacroDefinition.objects.filter(
            scope=MacroDefinition.Scope.WORKSPACE,
            workspace=workspace,
        ).order_by("name", "id"):
            resolved[macro.name] = macro

    if channel is not None:
        for macro in MacroDefinition.objects.filter(
            scope=MacroDefinition.Scope.CHANNEL,
            channel=channel,
        ).order_by("name", "id"):
            resolved[macro.name] = macro

    return [resolved[name] for name in sorted(resolved)]
