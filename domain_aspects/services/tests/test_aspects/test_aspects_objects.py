"""Tests for aspect entry objects: validation, hashability, kind property."""

from __future__ import annotations

import pytest

from domain_aspects.services.aspects import aspects_objects as objs


class TestLogged:
    """Test Logged entry object."""

    def test_logged_creation_happy_path(self) -> None:
        """Create Logged with valid event."""
        entry = objs.Logged(event="test.event")
        assert entry.event == "test.event"
        assert entry.kind == objs.AspectKind.LOGGED

    def test_logged_empty_event_raises(self) -> None:
        """Logged with empty event raises ValueError."""
        with pytest.raises(ValueError, match="non-empty string"):
            objs.Logged(event="")

    def test_logged_non_string_event_raises(self) -> None:
        """Logged with non-string event raises ValueError."""
        with pytest.raises(ValueError, match="non-empty string"):
            objs.Logged(event=None)  # type: ignore

    def test_logged_is_frozen(self) -> None:
        """Logged is frozen dataclass."""
        entry = objs.Logged(event="test")
        with pytest.raises(AttributeError):
            entry.event = "modified"  # type: ignore

    def test_logged_hashable(self) -> None:
        """Logged is hashable for frozenset membership."""
        entry1 = objs.Logged(event="test")
        entry2 = objs.Logged(event="test")
        entry3 = objs.Logged(event="other")
        assert hash(entry1) == hash(entry2)
        assert hash(entry1) != hash(entry3)


class TestRequires:
    """Test Requires entry object."""

    def test_requires_creation_happy_path(self) -> None:
        """Create Requires with valid permission."""
        entry = objs.Requires(permission="admin.read")
        assert entry.permission == "admin.read"
        assert entry.kind == objs.AspectKind.REQUIRES

    def test_requires_empty_permission_raises(self) -> None:
        """Requires with empty permission raises ValueError."""
        with pytest.raises(ValueError, match="non-empty string"):
            objs.Requires(permission="")

    def test_requires_hashable(self) -> None:
        """Requires is hashable for frozenset membership."""
        entry1 = objs.Requires(permission="admin.read")
        entry2 = objs.Requires(permission="admin.read")
        assert hash(entry1) == hash(entry2)


class TestTenantScoped:
    """Test TenantScoped entry object."""

    def test_tenant_scoped_creation_with_default(self) -> None:
        """Create TenantScoped with default param_name."""
        entry = objs.TenantScoped()
        assert entry.param_name == "tenant_id"
        assert entry.kind == objs.AspectKind.TENANT_SCOPED

    def test_tenant_scoped_creation_with_custom_param(self) -> None:
        """Create TenantScoped with custom param_name."""
        entry = objs.TenantScoped(param_name="org_id")
        assert entry.param_name == "org_id"

    def test_tenant_scoped_empty_param_name_raises(self) -> None:
        """TenantScoped with empty param_name raises ValueError."""
        with pytest.raises(ValueError, match="non-empty string"):
            objs.TenantScoped(param_name="")

    def test_tenant_scoped_hashable(self) -> None:
        """TenantScoped is hashable for frozenset membership."""
        entry1 = objs.TenantScoped(param_name="tenant_id")
        entry2 = objs.TenantScoped(param_name="tenant_id")
        entry3 = objs.TenantScoped(param_name="org_id")
        assert hash(entry1) == hash(entry2)
        assert hash(entry1) != hash(entry3)


class TestThrottled:
    """Test Throttled entry object."""

    def test_throttled_creation_happy_path(self) -> None:
        """Create Throttled with valid scope and rate."""
        entry = objs.Throttled(scope="api.documents", rate="100/hour")
        assert entry.scope == "api.documents"
        assert entry.rate == "100/hour"
        assert entry.tiers == ()
        assert entry.kind == objs.AspectKind.THROTTLED

    def test_throttled_with_tiers(self) -> None:
        """Create Throttled with tier overrides."""
        tiers = (("free", "10/hour"), ("pro", "1000/hour"))
        entry = objs.Throttled(scope="api.documents", rate="100/hour", tiers=tiers)
        assert entry.tiers == tiers

    def test_throttled_empty_scope_raises(self) -> None:
        """Throttled with empty scope raises ValueError."""
        with pytest.raises(ValueError, match="non-empty string"):
            objs.Throttled(scope="", rate="100/hour")

    def test_throttled_empty_rate_raises(self) -> None:
        """Throttled with empty rate raises ValueError."""
        with pytest.raises(ValueError, match="non-empty string"):
            objs.Throttled(scope="api.documents", rate="")

    def test_throttled_non_tuple_tiers_raises(self) -> None:
        """Throttled with non-tuple tiers raises ValueError."""
        with pytest.raises(ValueError, match="tuple"):
            objs.Throttled(scope="api", rate="100/hour", tiers={"free": "10/hour"})  # type: ignore

    def test_throttled_hashable(self) -> None:
        """Throttled is hashable for frozenset membership."""
        entry1 = objs.Throttled(scope="api.documents", rate="100/hour")
        entry2 = objs.Throttled(scope="api.documents", rate="100/hour")
        assert hash(entry1) == hash(entry2)


class TestMonitored:
    """Test Monitored entry object."""

    def test_monitored_creation_happy_path(self) -> None:
        """Create Monitored with valid event."""
        entry = objs.Monitored(event="document.classify")
        assert entry.event == "document.classify"
        assert entry.sink is None
        assert entry.kind == objs.AspectKind.MONITORED

    def test_monitored_creation_with_sink(self) -> None:
        """Create Monitored with custom sink."""
        sink = object()
        entry = objs.Monitored(event="document.classify", sink=sink)  # type: ignore[arg-type]
        assert entry.event == "document.classify"
        assert entry.sink is sink

    def test_monitored_empty_event_raises(self) -> None:
        """Monitored with empty event raises ValueError."""
        with pytest.raises(ValueError, match="non-empty string"):
            objs.Monitored(event="")

    def test_monitored_non_string_event_raises(self) -> None:
        """Monitored with non-string event raises ValueError."""
        with pytest.raises(ValueError, match="non-empty string"):
            objs.Monitored(event=None)  # type: ignore

    def test_monitored_is_frozen(self) -> None:
        """Monitored is frozen dataclass."""
        entry = objs.Monitored(event="test")
        with pytest.raises(AttributeError):
            entry.event = "modified"  # type: ignore

    def test_monitored_hashable(self) -> None:
        """Monitored is hashable for frozenset membership."""
        entry1 = objs.Monitored(event="document.classify")
        entry2 = objs.Monitored(event="document.classify")
        entry3 = objs.Monitored(event="document.extract")
        assert hash(entry1) == hash(entry2)
        assert hash(entry1) != hash(entry3)


class TestWrapErrors:
    """Test WrapErrors entry object."""

    def test_wrap_errors_creation_happy_path(self) -> None:
        """Create WrapErrors with valid exception class and catch tuple."""
        entry = objs.WrapErrors(
            as_=ValueError,
            catch=(RuntimeError, TypeError),
        )
        assert entry.as_ is ValueError
        assert entry.catch == (RuntimeError, TypeError)
        assert entry.kind == objs.AspectKind.WRAP_ERRORS

    def test_wrap_errors_default_catch(self) -> None:
        """Create WrapErrors with default catch tuple."""
        entry = objs.WrapErrors(as_=ValueError)
        assert entry.catch == (Exception,)

    def test_wrap_errors_non_type_as_raises(self) -> None:
        """WrapErrors with non-type as_ raises ValueError."""
        with pytest.raises(ValueError, match="exception class"):
            objs.WrapErrors(as_="not_a_type", catch=(Exception,))  # type: ignore

    def test_wrap_errors_empty_catch_raises(self) -> None:
        """WrapErrors with empty catch tuple raises ValueError."""
        with pytest.raises(ValueError, match="non-empty tuple"):
            objs.WrapErrors(as_=ValueError, catch=())  # type: ignore

    def test_wrap_errors_hashable(self) -> None:
        """WrapErrors is hashable for frozenset membership."""
        entry1 = objs.WrapErrors(as_=ValueError)
        entry2 = objs.WrapErrors(as_=ValueError)
        assert hash(entry1) == hash(entry2)


class TestAspectKindEnum:
    """Test AspectKind enumeration."""

    def test_aspect_kind_values(self) -> None:
        """AspectKind has all required values."""
        assert objs.AspectKind.LOGGED == "LOGGED"
        assert objs.AspectKind.REQUIRES == "REQUIRES"
        assert objs.AspectKind.TENANT_SCOPED == "TENANT_SCOPED"
        assert objs.AspectKind.THROTTLED == "THROTTLED"
        assert objs.AspectKind.MONITORED == "MONITORED"
        assert objs.AspectKind.WRAP_ERRORS == "WRAP_ERRORS"
        assert objs.AspectKind.RETRIED == "RETRIED"
        assert objs.AspectKind.REQUIRE_MIXINS == "REQUIRE_MIXINS"


class TestEntryHashability:
    """Test all entries are hashable and usable in frozensets."""

    def test_entries_in_frozenset(
        self,
        stub_logged: objs.Logged,
        stub_requires: objs.Requires,
        stub_tenant_scoped: objs.TenantScoped,
        stub_throttled: objs.Throttled,
        stub_monitored: objs.Monitored,
        stub_wrap_errors: objs.WrapErrors,
    ) -> None:
        """All entries can be members of a frozenset."""
        entry_set = frozenset(
            {
                stub_logged,
                stub_requires,
                stub_tenant_scoped,
                stub_throttled,
                stub_monitored,
                stub_wrap_errors,
            }
        )
        assert len(entry_set) == 6

    def test_entries_can_be_dict_keys(self) -> None:
        """All entries can be dict keys."""
        entry1 = objs.Logged(event="test")
        entry2 = objs.Requires(permission="read")
        d = {entry1: "logged", entry2: "requires"}
        assert d[entry1] == "logged"
        assert d[entry2] == "requires"


class TestRetried:
    """Test Retried entry object."""

    def test_retried_with_static_policy(self) -> None:
        """Create Retried with static retry policy."""
        from mixin_retry import RetryPolicy

        policy = RetryPolicy(
            max_attempts=3,
            backoff_base_seconds=0.1,
            backoff_multiplier=2.0,
            backoff_max_seconds=10.0,
            jitter=True,
        )
        entry = objs.Retried(policy=policy)
        assert entry.policy is policy
        assert entry.policy_from_request is None
        assert entry.kind == objs.AspectKind.RETRIED

    def test_retried_with_dynamic_policy_selector(self) -> None:
        """Create Retried with dynamic policy selector."""
        from mixin_retry import RetryPolicy

        def selector(*args: object, **kwargs: object) -> RetryPolicy | None:
            return None

        entry = objs.Retried(policy_from_request=selector)
        assert entry.policy is None
        assert entry.policy_from_request is selector
        assert entry.kind == objs.AspectKind.RETRIED

    def test_retried_neither_policy_raises(self) -> None:
        """Retried with neither policy raises ValueError."""
        with pytest.raises(ValueError, match="exactly one"):
            objs.Retried()

    def test_retried_both_policies_raises(self) -> None:
        """Retried with both policy and selector raises ValueError."""
        from mixin_retry import RetryPolicy

        policy = RetryPolicy(
            max_attempts=3,
            backoff_base_seconds=0.1,
            backoff_multiplier=2.0,
            backoff_max_seconds=10.0,
            jitter=True,
        )

        def selector(*args: object, **kwargs: object) -> RetryPolicy | None:
            return None

        with pytest.raises(ValueError, match="both"):
            objs.Retried(policy=policy, policy_from_request=selector)

    def test_retried_is_frozen(self) -> None:
        """Retried is frozen dataclass."""
        from mixin_retry import RetryPolicy

        policy = RetryPolicy(
            max_attempts=3,
            backoff_base_seconds=0.1,
            backoff_multiplier=2.0,
            backoff_max_seconds=10.0,
            jitter=True,
        )
        entry = objs.Retried(policy=policy)
        with pytest.raises(AttributeError):
            entry.policy = None  # type: ignore

    def test_retried_hashable(self) -> None:
        """Retried is hashable for frozenset membership."""
        from mixin_retry import RetryPolicy

        policy = RetryPolicy(
            max_attempts=3,
            backoff_base_seconds=0.1,
            backoff_multiplier=2.0,
            backoff_max_seconds=10.0,
            jitter=True,
        )
        entry1 = objs.Retried(policy=policy)
        entry2 = objs.Retried(policy=policy)
        assert hash(entry1) == hash(entry2)


class TestRequireMixins:
    """Test RequireMixins validation marker."""

    def test_require_mixins_creation_happy_path(self) -> None:
        """Create RequireMixins with valid base types."""

        class MixinA:
            pass

        class MixinB:
            pass

        entry = objs.RequireMixins(bases=(MixinA, MixinB))
        assert entry.bases == (MixinA, MixinB)
        assert entry.kind == objs.AspectKind.REQUIRE_MIXINS

    def test_require_mixins_empty_bases_raises(self) -> None:
        """RequireMixins with empty bases raises ValueError."""
        with pytest.raises(ValueError, match="non-empty tuple"):
            objs.RequireMixins(bases=())

    def test_require_mixins_non_tuple_bases_raises(self) -> None:
        """RequireMixins with non-tuple bases raises ValueError."""

        class MixinA:
            pass

        with pytest.raises(ValueError, match="non-empty tuple"):
            objs.RequireMixins(bases=[MixinA])  # type: ignore

    def test_require_mixins_is_frozen(self) -> None:
        """RequireMixins is frozen dataclass."""

        class MixinA:
            pass

        entry = objs.RequireMixins(bases=(MixinA,))
        with pytest.raises(AttributeError):
            entry.bases = ()  # type: ignore

    def test_require_mixins_hashable(self) -> None:
        """RequireMixins is hashable for frozenset membership."""

        class MixinA:
            pass

        class MixinB:
            pass

        entry1 = objs.RequireMixins(bases=(MixinA, MixinB))
        entry2 = objs.RequireMixins(bases=(MixinA, MixinB))
        assert hash(entry1) == hash(entry2)

    def test_require_mixins_build_class_all_bases_present(self) -> None:
        """RequireMixins.build() validates class has all required bases."""

        class MixinA:
            pass

        class MixinB:
            pass

        class GoodClass(MixinA, MixinB):
            pass

        entry = objs.RequireMixins(bases=(MixinA, MixinB))
        decorator = entry.build()
        result = decorator(GoodClass)
        assert result is GoodClass

    def test_require_mixins_build_class_missing_base_raises(self) -> None:
        """RequireMixins.build() raises if class missing required base."""

        class MixinA:
            pass

        class MixinB:
            pass

        class BadClass(MixinA):
            pass

        entry = objs.RequireMixins(bases=(MixinA, MixinB))
        decorator = entry.build()
        with pytest.raises(ValueError, match="MixinB"):
            decorator(BadClass)

    def test_require_mixins_build_function_target_raises(self) -> None:
        """RequireMixins.build() rejects function targets."""

        class MixinA:
            pass

        def some_function() -> None:
            pass

        entry = objs.RequireMixins(bases=(MixinA,))
        decorator = entry.build()
        with pytest.raises(ValueError, match="class-only marker"):
            decorator(some_function)

    def test_require_mixins_build_enumerates_all_missing_bases(self) -> None:
        """RequireMixins.build() enumerates all missing bases in error."""

        class MixinA:
            pass

        class MixinB:
            pass

        class MixinC:
            pass

        class BadClass:
            pass

        entry = objs.RequireMixins(bases=(MixinA, MixinB, MixinC))
        decorator = entry.build()
        with pytest.raises(ValueError) as exc_info:
            decorator(BadClass)
        error_msg = str(exc_info.value)
        assert "MixinA" in error_msg
        assert "MixinB" in error_msg
        assert "MixinC" in error_msg


class TestRootExport:
    """Test root-level exports of aspect entry types."""

    def test_all_aspect_entries_importable_from_root(self) -> None:
        """Verify all aspect entry types are importable from domain_aspects root."""
        from domain_aspects import (
            AspectEntry,
            AspectKind,
            Logged,
            Monitored,
            RequireMixins,
            Requires,
            Retried,
            TenantScoped,
            Throttled,
            WrapErrors,
        )

        assert Logged is objs.Logged
        assert Monitored is objs.Monitored
        assert RequireMixins is objs.RequireMixins
        assert Requires is objs.Requires
        assert Retried is objs.Retried
        assert TenantScoped is objs.TenantScoped
        assert Throttled is objs.Throttled
        assert WrapErrors is objs.WrapErrors
        assert AspectKind is objs.AspectKind
        assert AspectEntry is objs.AspectEntry
