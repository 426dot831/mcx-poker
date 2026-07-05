"""PokerKit adapter boundary for mcx-poker."""

from __future__ import annotations

import warnings
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass
from enum import StrEnum
from typing import Any, NoReturn, cast

from pokerkit import Automation, Card, Mode, NoLimitTexasHoldem, State


class ActionType(StrEnum):
    """Platform-level poker action types."""

    FOLD = "Fold"
    CHECK = "Check"
    CALL = "Call"
    RAISE_TO = "RaiseTo"
    ALL_IN = "AllIn"

    @classmethod
    def normalize(cls, value: ActionType | str) -> ActionType:
        if isinstance(value, cls):
            return value

        try:
            return cls(value)
        except ValueError as exc:
            raise PokerKitAdapterError(
                code="pokerkit_illegal_action",
                message=f"Unsupported action type: {value!r}.",
            ) from exc


@dataclass(frozen=True)
class CreateHandRequest:
    """Input required to create a PokerKit-backed cash-game hand."""

    hand_id: str
    seat_to_player: Mapping[int, str]
    starting_stacks: Mapping[int, int] | Sequence[int]
    button_seat_index: int
    small_blind: int
    big_blind: int
    ante: int = 0


@dataclass(frozen=True)
class PlayerAction:
    """Platform action submitted to the adapter."""

    player_id: str
    seat_index: int
    hand_id: str
    turn_id: str | None
    action_type: ActionType | str
    amount: int | None = None
    source: str | None = None


@dataclass(frozen=True)
class ActorRef:
    seat_index: int
    player_id: str


@dataclass(frozen=True)
class PokerKitIndexMapping:
    seat_to_pokerkit_index: Mapping[int, int]
    pokerkit_index_to_seat: Mapping[int, int]
    player_to_pokerkit_index: Mapping[str, int]
    pokerkit_index_to_player: Mapping[int, str]


@dataclass(frozen=True)
class LegalActionBoundary:
    action_type: ActionType
    enabled: bool
    amount_min: int | None = None
    amount_max: int | None = None
    amount_fixed: int | None = None
    reason_if_disabled: str | None = None


@dataclass(frozen=True)
class LegalActionBoundaries:
    fold: LegalActionBoundary
    check: LegalActionBoundary
    call: LegalActionBoundary
    raise_to: LegalActionBoundary
    all_in: LegalActionBoundary
    call_amount: int | None
    min_raise_to: int | None
    max_raise_to: int | None


@dataclass(frozen=True)
class PotInfo:
    index: int
    amount: int
    raked_amount: int
    unraked_amount: int
    eligible_seats: tuple[int, ...]


@dataclass(frozen=True)
class PotSummary:
    total_amount: int
    pots: tuple[PotInfo, ...]


@dataclass(frozen=True)
class OperationSummary:
    operation_type: str
    details: Mapping[str, Any]


@dataclass(frozen=True)
class PokerKitStateSummary:
    hand_id: str
    is_active: bool
    current_actor: ActorRef | None
    board_cards: tuple[str, ...]
    stacks: Mapping[int, int]
    bets: Mapping[int, int]
    pot_summary: PotSummary
    hole_cards_by_seat: Mapping[int, tuple[str, ...]]
    shown_cards_by_seat: Mapping[int, tuple[str, ...]]
    legal_action_boundaries: LegalActionBoundaries
    operations_summary: tuple[OperationSummary, ...]


@dataclass(frozen=True)
class WinnerSummary:
    seat_index: int
    player_id: str
    payoff: int
    amount_pulled: int
    shown_cards: tuple[str, ...]


@dataclass(frozen=True)
class ShowdownEntry:
    seat_index: int
    player_id: str
    shown_cards: tuple[str, ...]


@dataclass(frozen=True)
class HandSettlement:
    hand_id: str
    final_stacks: Mapping[int, int]
    payoffs: Mapping[int, int]
    winners: tuple[WinnerSummary, ...]
    final_board: tuple[str, ...]
    showdown_summary: tuple[ShowdownEntry, ...]
    operations_summary: tuple[OperationSummary, ...]


@dataclass(frozen=True)
class ActionSubmissionResult:
    hand_id: str
    action: PlayerAction
    operation: OperationSummary
    state_summary: PokerKitStateSummary
    settlement: HandSettlement | None


class PokerKitAdapterError(Exception):
    """Platform error raised by the PokerKit adapter."""

    code: str
    message: str
    player_id: str | None
    hand_id: str | None
    turn_id: str | None
    retry_same_player: bool

    def __init__(
        self,
        *,
        code: str,
        message: str,
        player_id: str | None = None,
        hand_id: str | None = None,
        turn_id: str | None = None,
        retry_same_player: bool = True,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.player_id = player_id
        self.hand_id = hand_id
        self.turn_id = turn_id
        self.retry_same_player = retry_same_player

    def to_dict(self) -> dict[str, object | None]:
        return {
            "code": self.code,
            "message": self.message,
            "player_id": self.player_id,
            "hand_id": self.hand_id,
            "turn_id": self.turn_id,
            "retry_same_player": self.retry_same_player,
        }


@dataclass(frozen=True)
class _HandRecord:
    hand_id: str
    state: State
    mapping: PokerKitIndexMapping


@dataclass(frozen=True)
class _AllInPlan:
    method: str
    amount: int | None


class PokerKitAdapter:
    """Owns all direct PokerKit interactions."""

    _MVP_AUTOMATIONS = (
        Automation.ANTE_POSTING,
        Automation.BET_COLLECTION,
        Automation.BLIND_OR_STRADDLE_POSTING,
        Automation.CARD_BURNING,
        Automation.HOLE_DEALING,
        Automation.BOARD_DEALING,
        Automation.HOLE_CARDS_SHOWING_OR_MUCKING,
        Automation.HAND_KILLING,
        Automation.CHIPS_PUSHING,
        Automation.CHIPS_PULLING,
    )

    def __init__(self) -> None:
        self._hands: dict[str, _HandRecord] = {}

    def create_hand(self, request: CreateHandRequest) -> PokerKitStateSummary:
        self._validate_create_request(request)

        active_seats = self._active_seats_after_button(
            tuple(request.seat_to_player),
            request.button_seat_index,
        )
        mapping = self._build_mapping(active_seats, request.seat_to_player)
        starting_stacks = self._normalize_starting_stacks(request.starting_stacks, active_seats)

        try:
            state = NoLimitTexasHoldem.create_state(
                self._MVP_AUTOMATIONS,
                True,
                request.ante,
                (request.small_blind, request.big_blind),
                request.big_blind,
                starting_stacks,
                len(active_seats),
                mode=Mode.CASH_GAME,
            )
        except ValueError:
            raise PokerKitAdapterError(
                code="pokerkit_adapter_bug",
                message=f"PokerKit rejected hand creation for hand {request.hand_id!r}.",
                hand_id=request.hand_id,
            ) from None

        self._hands[request.hand_id] = _HandRecord(request.hand_id, state, mapping)
        return self.get_state_summary(request.hand_id)

    def get_hand_mapping(self, hand_id: str) -> PokerKitIndexMapping:
        record = self._get_record(hand_id)
        mapping = record.mapping
        return PokerKitIndexMapping(
            seat_to_pokerkit_index=dict(mapping.seat_to_pokerkit_index),
            pokerkit_index_to_seat=dict(mapping.pokerkit_index_to_seat),
            player_to_pokerkit_index=dict(mapping.player_to_pokerkit_index),
            pokerkit_index_to_player=dict(mapping.pokerkit_index_to_player),
        )

    def get_state_summary(self, hand_id: str) -> PokerKitStateSummary:
        record = self._get_record(hand_id)
        state = record.state
        mapping = record.mapping
        current_actor = self._actor_ref(record, state.turn_index)

        return PokerKitStateSummary(
            hand_id=hand_id,
            is_active=state.status,
            current_actor=current_actor,
            board_cards=self._board_cards(state),
            stacks=self._seat_amounts(state.stacks, mapping),
            bets=self._seat_amounts(state.bets, mapping),
            pot_summary=self._pot_summary(state, mapping),
            hole_cards_by_seat=self._hole_cards_by_seat(state, mapping),
            shown_cards_by_seat=self._shown_cards_by_seat(state, mapping),
            legal_action_boundaries=self._legal_action_boundaries(record),
            operations_summary=tuple(
                self._operation_summary(operation, mapping) for operation in state.operations
            ),
        )

    def legal_action_boundaries(self, hand_id: str) -> LegalActionBoundaries:
        return self.get_state_summary(hand_id).legal_action_boundaries

    def submit_action(self, action: PlayerAction) -> ActionSubmissionResult:
        normalized_type = ActionType.normalize(action.action_type)
        self._validate_action_shape(action, normalized_type)

        record = self._get_record(action.hand_id)
        state = record.state

        if not state.status:
            self._raise_action_error(
                action,
                code="pokerkit_hand_not_active",
                message="The hand is not active.",
            )

        self._validate_actor(action, record)

        try:
            operation = self._submit_to_pokerkit(action, normalized_type, record)
        except ValueError as exc:
            raise self._map_pokerkit_exception(action, record, exc) from None

        operation_summary = self._operation_summary(operation, record.mapping)
        state_summary = self.get_state_summary(action.hand_id)
        settlement = None if state.status else self.get_hand_settlement(action.hand_id)

        return ActionSubmissionResult(
            hand_id=action.hand_id,
            action=action,
            operation=operation_summary,
            state_summary=state_summary,
            settlement=settlement,
        )

    def get_hand_settlement(self, hand_id: str) -> HandSettlement:
        record = self._get_record(hand_id)
        state = record.state

        if state.status:
            raise PokerKitAdapterError(
                code="pokerkit_state_mismatch",
                message="The hand is still active; settlement is not available.",
                hand_id=hand_id,
            )

        mapping = record.mapping
        operations_summary = tuple(
            self._operation_summary(operation, mapping) for operation in state.operations
        )
        return HandSettlement(
            hand_id=hand_id,
            final_stacks=self._seat_amounts(state.stacks, mapping),
            payoffs=self._seat_amounts(state.payoffs, mapping),
            winners=self._winners(record),
            final_board=self._board_cards(state),
            showdown_summary=self._showdown_summary(record),
            operations_summary=operations_summary,
        )

    def _validate_create_request(self, request: CreateHandRequest) -> None:
        if request.hand_id in self._hands:
            raise PokerKitAdapterError(
                code="pokerkit_state_mismatch",
                message=f"Hand {request.hand_id!r} already exists.",
                hand_id=request.hand_id,
            )
        if len(request.seat_to_player) < 2:
            raise PokerKitAdapterError(
                code="pokerkit_adapter_bug",
                message="At least two active seats are required.",
                hand_id=request.hand_id,
            )
        if len(set(request.seat_to_player.values())) != len(request.seat_to_player):
            raise PokerKitAdapterError(
                code="pokerkit_adapter_bug",
                message="Duplicate player ids are not allowed in a hand.",
                hand_id=request.hand_id,
            )
        if request.button_seat_index not in request.seat_to_player:
            raise PokerKitAdapterError(
                code="pokerkit_adapter_bug",
                message="The button seat must be an active seat.",
                hand_id=request.hand_id,
            )
        if request.small_blind <= 0 or request.big_blind <= 0 or request.ante < 0:
            raise PokerKitAdapterError(
                code="pokerkit_adapter_bug",
                message="Blinds must be positive and ante must be non-negative.",
                hand_id=request.hand_id,
            )

    def _submit_to_pokerkit(
        self,
        action: PlayerAction,
        action_type: ActionType,
        record: _HandRecord,
    ) -> Any:
        state = record.state

        match action_type:
            case ActionType.FOLD:
                if not self._legal_action_boundaries(record).fold.enabled:
                    self._raise_action_error(
                        action,
                        code="pokerkit_illegal_action",
                        message="Fold is not legal for the current actor.",
                    )
                return state.fold()
            case ActionType.CHECK:
                boundaries = self._legal_action_boundaries(record)
                if not boundaries.check.enabled:
                    self._raise_action_error(
                        action,
                        code="pokerkit_illegal_action",
                        message="Check is not legal because the actor must call or fold.",
                    )
                return state.check_or_call()
            case ActionType.CALL:
                boundaries = self._legal_action_boundaries(record)
                if not boundaries.call.enabled:
                    self._raise_action_error(
                        action,
                        code="pokerkit_illegal_action",
                        message="Call is not legal for the current actor.",
                    )
                return state.check_or_call()
            case ActionType.RAISE_TO:
                assert action.amount is not None
                if not state.can_complete_bet_or_raise_to(action.amount):
                    self._raise_action_error(
                        action,
                        code="pokerkit_illegal_action",
                        message=f"RaiseTo({action.amount}) is outside PokerKit boundaries.",
                    )
                return state.complete_bet_or_raise_to(action.amount)
            case ActionType.ALL_IN:
                plan = self._all_in_plan(state)
                if plan is None:
                    self._raise_action_error(
                        action,
                        code="pokerkit_illegal_action",
                        message="AllIn is not legal for the current actor.",
                    )
                if plan.method == "check_or_call":
                    return state.check_or_call()
                assert plan.amount is not None
                return state.complete_bet_or_raise_to(plan.amount)

    def _validate_action_shape(self, action: PlayerAction, action_type: ActionType) -> None:
        if action_type == ActionType.RAISE_TO:
            if action.amount is None:
                self._raise_action_error(
                    action,
                    code="pokerkit_illegal_action",
                    message="RaiseTo requires an amount.",
                )
            if action.amount <= 0:
                self._raise_action_error(
                    action,
                    code="pokerkit_illegal_action",
                    message="RaiseTo amount must be positive.",
                )
            return

        if action.amount is not None:
            self._raise_action_error(
                action,
                code="pokerkit_illegal_action",
                message=f"{action_type.value} must not carry an amount.",
            )

    def _validate_actor(self, action: PlayerAction, record: _HandRecord) -> None:
        mapping = record.mapping
        pokerkit_index = mapping.seat_to_pokerkit_index.get(action.seat_index)
        if pokerkit_index is None:
            self._raise_action_error(
                action,
                code="pokerkit_actor_mismatch",
                message="The action seat is not active in this hand.",
            )
        if mapping.pokerkit_index_to_player[pokerkit_index] != action.player_id:
            self._raise_action_error(
                action,
                code="pokerkit_actor_mismatch",
                message="The action player does not match the action seat.",
            )

        turn_index = record.state.turn_index
        if turn_index is None:
            self._raise_action_error(
                action,
                code="pokerkit_state_mismatch",
                message="PokerKit has no current actor.",
            )
        if turn_index != pokerkit_index:
            self._raise_action_error(
                action,
                code="pokerkit_actor_mismatch",
                message="The submitted actor does not match PokerKit's current actor.",
            )

    def _legal_action_boundaries(self, record: _HandRecord) -> LegalActionBoundaries:
        state = record.state
        disabled_reason = None if state.status and state.turn_index is not None else "no_actor"

        call_amount = state.checking_or_calling_amount
        min_raise_to = state.min_completion_betting_or_raising_to_amount
        max_raise_to = state.max_completion_betting_or_raising_to_amount
        can_check_or_call = state.can_check_or_call()
        can_raise_min = (
            min_raise_to is not None
            and max_raise_to is not None
            and min_raise_to <= max_raise_to
            and state.can_complete_bet_or_raise_to(min_raise_to)
        )

        fold_enabled = (
            disabled_reason is None
            and call_amount is not None
            and call_amount > 0
            and self._can_fold_without_warning(state)
        )
        check_enabled = disabled_reason is None and can_check_or_call and call_amount == 0
        call_enabled = (
            disabled_reason is None
            and can_check_or_call
            and call_amount is not None
            and call_amount > 0
        )
        raise_enabled = disabled_reason is None and can_raise_min

        all_in_plan = self._all_in_plan(state)
        all_in_amount = all_in_plan.amount if all_in_plan is not None else None

        return LegalActionBoundaries(
            fold=LegalActionBoundary(
                ActionType.FOLD,
                fold_enabled,
                reason_if_disabled=None if fold_enabled else disabled_reason or "no_call_pressure",
            ),
            check=LegalActionBoundary(
                ActionType.CHECK,
                check_enabled,
                amount_fixed=0 if check_enabled else None,
                reason_if_disabled=None if check_enabled else disabled_reason or "call_required",
            ),
            call=LegalActionBoundary(
                ActionType.CALL,
                call_enabled,
                amount_fixed=call_amount if call_enabled else None,
                reason_if_disabled=None if call_enabled else disabled_reason or "nothing_to_call",
            ),
            raise_to=LegalActionBoundary(
                ActionType.RAISE_TO,
                raise_enabled,
                amount_min=min_raise_to if raise_enabled else None,
                amount_max=max_raise_to if raise_enabled else None,
                reason_if_disabled=(
                    None if raise_enabled else disabled_reason or "raise_unavailable"
                ),
            ),
            all_in=LegalActionBoundary(
                ActionType.ALL_IN,
                all_in_plan is not None,
                amount_fixed=all_in_amount,
                reason_if_disabled=(
                    None if all_in_plan is not None else disabled_reason or "all_in_unavailable"
                ),
            ),
            call_amount=call_amount,
            min_raise_to=min_raise_to,
            max_raise_to=max_raise_to,
        )

    def _all_in_plan(self, state: State) -> _AllInPlan | None:
        actor_index = state.actor_index
        if not state.status or actor_index is None:
            return None

        max_raise_to = state.max_completion_betting_or_raising_to_amount
        if (
            max_raise_to is not None
            and state.can_complete_bet_or_raise_to(max_raise_to)
            and max_raise_to == state.stacks[actor_index] + state.bets[actor_index]
        ):
            return _AllInPlan("complete_bet_or_raise_to", max_raise_to)

        call_amount = state.checking_or_calling_amount
        if (
            call_amount is not None
            and call_amount > 0
            and state.can_check_or_call()
            and call_amount == state.stacks[actor_index]
        ):
            return _AllInPlan("check_or_call", call_amount)

        return None

    def _map_pokerkit_exception(
        self,
        action: PlayerAction,
        record: _HandRecord,
        exc: ValueError,
    ) -> PokerKitAdapterError:
        if not record.state.status:
            code = "pokerkit_hand_not_active"
            message = "PokerKit rejected the action because the hand is no longer active."
        elif "There is no player to act" in str(exc):
            code = "pokerkit_state_mismatch"
            message = "PokerKit rejected the action because there is no current actor."
        else:
            code = "pokerkit_illegal_action"
            message = "PokerKit rejected the submitted action."

        return PokerKitAdapterError(
            code=code,
            message=message,
            player_id=action.player_id,
            hand_id=action.hand_id,
            turn_id=action.turn_id,
        )

    def _raise_action_error(
        self,
        action: PlayerAction,
        *,
        code: str,
        message: str,
    ) -> NoReturn:
        raise PokerKitAdapterError(
            code=code,
            message=message,
            player_id=action.player_id,
            hand_id=action.hand_id,
            turn_id=action.turn_id,
        )

    def _get_record(self, hand_id: str) -> _HandRecord:
        try:
            return self._hands[hand_id]
        except KeyError:
            raise PokerKitAdapterError(
                code="pokerkit_state_mismatch",
                message=f"Unknown hand id: {hand_id!r}.",
                hand_id=hand_id,
            ) from None

    def _active_seats_after_button(
        self,
        active_seats: tuple[int, ...],
        button_seat_index: int,
    ) -> tuple[int, ...]:
        sorted_seats = tuple(sorted(active_seats))
        button_position = sorted_seats.index(button_seat_index)
        ordered = sorted_seats[button_position + 1 :] + sorted_seats[: button_position + 1]

        # PokerKit has no button argument. For blind games, index 0 is the
        # first blind seat and the button is the last active index in this order.
        if ordered[-1] != button_seat_index:
            raise PokerKitAdapterError(
                code="pokerkit_adapter_bug",
                message="Button rotation did not put the button at the final PokerKit index.",
            )

        return ordered

    def _build_mapping(
        self,
        active_seats: tuple[int, ...],
        seat_to_player: Mapping[int, str],
    ) -> PokerKitIndexMapping:
        seat_to_pokerkit_index = {
            seat_index: pokerkit_index for pokerkit_index, seat_index in enumerate(active_seats)
        }
        pokerkit_index_to_seat = {
            pokerkit_index: seat_index
            for seat_index, pokerkit_index in seat_to_pokerkit_index.items()
        }
        player_to_pokerkit_index = {
            seat_to_player[seat_index]: pokerkit_index
            for seat_index, pokerkit_index in seat_to_pokerkit_index.items()
        }
        pokerkit_index_to_player = {
            pokerkit_index: seat_to_player[seat_index]
            for pokerkit_index, seat_index in pokerkit_index_to_seat.items()
        }

        return PokerKitIndexMapping(
            seat_to_pokerkit_index=seat_to_pokerkit_index,
            pokerkit_index_to_seat=pokerkit_index_to_seat,
            player_to_pokerkit_index=player_to_pokerkit_index,
            pokerkit_index_to_player=pokerkit_index_to_player,
        )

    def _normalize_starting_stacks(
        self,
        starting_stacks: Mapping[int, int] | Sequence[int],
        active_seats: tuple[int, ...],
    ) -> tuple[int, ...]:
        if isinstance(starting_stacks, Mapping):
            if all(seat_index in starting_stacks for seat_index in active_seats):
                stacks = tuple(starting_stacks[seat_index] for seat_index in active_seats)
            elif all(index in starting_stacks for index in range(len(active_seats))):
                stacks = tuple(starting_stacks[index] for index in range(len(active_seats)))
            else:
                raise PokerKitAdapterError(
                    code="pokerkit_adapter_bug",
                    message=(
                        "Starting stacks mapping must be keyed by active seat or PokerKit index."
                    ),
                )
        else:
            stacks = tuple(starting_stacks)

        if len(stacks) != len(active_seats):
            raise PokerKitAdapterError(
                code="pokerkit_adapter_bug",
                message="Starting stacks must match active player count.",
            )
        if any(stack <= 0 for stack in stacks):
            raise PokerKitAdapterError(
                code="pokerkit_adapter_bug",
                message="Starting stacks must be positive.",
            )

        return stacks

    def _actor_ref(self, record: _HandRecord, pokerkit_index: int | None) -> ActorRef | None:
        if pokerkit_index is None:
            return None

        try:
            seat_index = record.mapping.pokerkit_index_to_seat[pokerkit_index]
            player_id = record.mapping.pokerkit_index_to_player[pokerkit_index]
        except KeyError:
            raise PokerKitAdapterError(
                code="pokerkit_adapter_bug",
                message=f"PokerKit actor index {pokerkit_index} is not mapped.",
                hand_id=record.hand_id,
            ) from None

        return ActorRef(seat_index=seat_index, player_id=player_id)

    def _seat_amounts(
        self,
        amounts: Sequence[int],
        mapping: PokerKitIndexMapping,
    ) -> dict[int, int]:
        return {
            mapping.pokerkit_index_to_seat[pokerkit_index]: amount
            for pokerkit_index, amount in enumerate(amounts)
        }

    def _board_cards(self, state: State) -> tuple[str, ...]:
        try:
            return tuple(str(card) for card in state.get_board_cards(0))
        except ValueError:
            return ()

    def _pot_summary(self, state: State, mapping: PokerKitIndexMapping) -> PotSummary:
        pots = tuple(state.pots)
        return PotSummary(
            total_amount=state.total_pot_amount,
            pots=tuple(
                PotInfo(
                    index=index,
                    amount=pot.amount,
                    raked_amount=pot.raked_amount,
                    unraked_amount=pot.unraked_amount,
                    eligible_seats=tuple(
                        mapping.pokerkit_index_to_seat[player_index]
                        for player_index in pot.player_indices
                    ),
                )
                for index, pot in enumerate(pots)
            ),
        )

    def _hole_cards_by_seat(
        self,
        state: State,
        mapping: PokerKitIndexMapping,
    ) -> dict[int, tuple[str, ...]]:
        return {
            mapping.pokerkit_index_to_seat[pokerkit_index]: tuple(str(card) for card in cards)
            for pokerkit_index, cards in enumerate(state.hole_cards)
        }

    def _shown_cards_by_seat(
        self,
        state: State,
        mapping: PokerKitIndexMapping,
    ) -> dict[int, tuple[str, ...]]:
        return {
            mapping.pokerkit_index_to_seat[pokerkit_index]: tuple(
                str(card) for card in state.get_up_cards(pokerkit_index)
            )
            for pokerkit_index in mapping.pokerkit_index_to_seat
        }

    def _can_fold_without_warning(self, state: State) -> bool:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            return state.can_fold()

    def _operation_summary(
        self,
        operation: Any,
        mapping: PokerKitIndexMapping,
    ) -> OperationSummary:
        details: dict[str, Any] = {}

        if is_dataclass(operation):
            for field in fields(operation):
                if field.name == "commentary":
                    continue
                value = getattr(operation, field.name)
                if field.name == "player_index":
                    details["pokerkit_player_index"] = value
                    details["seat_index"] = mapping.pokerkit_index_to_seat[value]
                    details["player_id"] = mapping.pokerkit_index_to_player[value]
                elif field.name in {"bets", "amounts"} and len(value) == len(
                    mapping.pokerkit_index_to_seat
                ):
                    details[field.name] = self._seat_amounts(value, mapping)
                else:
                    details[field.name] = self._serialize_value(value, mapping)

        return OperationSummary(
            operation_type=operation.__class__.__name__,
            details=details,
        )

    def _serialize_value(self, value: Any, mapping: PokerKitIndexMapping) -> Any:
        if isinstance(value, Card):
            return str(value)
        if isinstance(value, tuple):
            return tuple(self._serialize_value(item, mapping) for item in value)
        if isinstance(value, list):
            return tuple(self._serialize_value(item, mapping) for item in value)
        if isinstance(value, dict):
            return {
                self._serialize_value(key, mapping): self._serialize_value(item, mapping)
                for key, item in value.items()
            }
        return value

    def _winners(self, record: _HandRecord) -> tuple[WinnerSummary, ...]:
        state = record.state
        mapping = record.mapping
        pulled_amounts: dict[int, int] = {}

        for operation in state.operations:
            if operation.__class__.__name__ == "ChipsPulling":
                operation_data = cast(Any, operation)
                player_index = operation_data.player_index
                pulled_amounts[player_index] = (
                    pulled_amounts.get(player_index, 0) + operation_data.amount
                )

        max_payoff = max(state.payoffs, default=0)
        winner_indices = [
            player_index
            for player_index, payoff in enumerate(state.payoffs)
            if payoff == max_payoff
        ]
        if max_payoff <= 0:
            winner_indices = [
                player_index
                for player_index, amount in pulled_amounts.items()
                if amount == max(pulled_amounts.values(), default=0) and amount > 0
            ]

        return tuple(
            WinnerSummary(
                seat_index=mapping.pokerkit_index_to_seat[player_index],
                player_id=mapping.pokerkit_index_to_player[player_index],
                payoff=state.payoffs[player_index],
                amount_pulled=pulled_amounts.get(player_index, 0),
                shown_cards=tuple(str(card) for card in state.get_up_cards(player_index)),
            )
            for player_index in winner_indices
        )

    def _showdown_summary(self, record: _HandRecord) -> tuple[ShowdownEntry, ...]:
        entries: list[ShowdownEntry] = []

        for operation in record.state.operations:
            if operation.__class__.__name__ != "HoleCardsShowingOrMucking":
                continue
            operation_data = cast(Any, operation)
            player_index = operation_data.player_index
            entries.append(
                ShowdownEntry(
                    seat_index=record.mapping.pokerkit_index_to_seat[player_index],
                    player_id=record.mapping.pokerkit_index_to_player[player_index],
                    shown_cards=tuple(str(card) for card in operation_data.hole_cards),
                )
            )

        return tuple(entries)
