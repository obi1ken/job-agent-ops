from .models import OperationType, QuotaDecision, WindowSnapshot, Zone

# Maximum OperationType priority value allowed per zone.
# Lower IntEnum value = higher priority (priority 1 is most important).
_ZONE_MAX_PRIORITY: dict[str, int] = {
    Zone.FREE:       4,  # all operations
    Zone.CAUTION:    3,  # defer BATCH_DISCOVERY_SCAN (priority 4)
    Zone.RESTRICTED: 2,  # defer standard scoring/tailoring (priority 3+)
    Zone.EMERGENCY:  1,  # only INTERVIEW_INVITE_RESPONSE / OFFER_PROCESSING
}


class QuotaPolicy:
    @staticmethod
    def evaluate(
        snapshot: WindowSnapshot,
        operation_type: OperationType,
        estimated_tokens: int,
    ) -> QuotaDecision:
        max_priority = _ZONE_MAX_PRIORITY[snapshot.zone]

        if operation_type.value > max_priority:
            return QuotaDecision(
                allowed=False,
                zone=snapshot.zone,
                used_pct=snapshot.used_pct,
                window_tokens=snapshot.window_tokens,
                window_limit=snapshot.window_limit,
                estimated_tokens=estimated_tokens,
                reason=(
                    f"Zone {snapshot.zone} ({snapshot.used_pct:.0%} used): "
                    f"{operation_type.name} (priority {operation_type.value}) deferred — "
                    f"max allowed priority is {max_priority}"
                ),
            )

        headroom = snapshot.window_limit - snapshot.window_tokens
        if estimated_tokens > headroom:
            return QuotaDecision(
                allowed=False,
                zone=snapshot.zone,
                used_pct=snapshot.used_pct,
                window_tokens=snapshot.window_tokens,
                window_limit=snapshot.window_limit,
                estimated_tokens=estimated_tokens,
                reason=(
                    f"Insufficient headroom: need ~{estimated_tokens} tokens, "
                    f"only {headroom} remaining in window"
                ),
            )

        return QuotaDecision(
            allowed=True,
            zone=snapshot.zone,
            used_pct=snapshot.used_pct,
            window_tokens=snapshot.window_tokens,
            window_limit=snapshot.window_limit,
            estimated_tokens=estimated_tokens,
            reason=f"Zone {snapshot.zone} ({snapshot.used_pct:.0%} used) — proceed",
        )
