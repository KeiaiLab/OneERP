from __future__ import annotations

from scripts.ci.normalize_g2_i18n import LOCALES, MESSAGE_KEYS, render_messages


def test_render_messages_has_required_keys_for_all_locales() -> None:
    expected = set(MESSAGE_KEYS)

    for locale in LOCALES:
        messages = render_messages("selling", locale)
        assert expected <= set(messages)
        assert all(messages[key] for key in expected)
