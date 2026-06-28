from core.ai_analysis.prompt_ai_context import build_template_prompt


def test_build_template_prompt_normalizes_to_standard_payload_schema():
    context = {
        'meta': {'symbol': 'EURUSD-OTC', 'timestamp': '2026-06-29T12:00:00'},
        'market_state': {'state': 'TRENDING', 'description': 'Strong move'},
        'm1': {'close': 1.1234, 'rsi': 54.2},
        'm5': {'bias': 'BULLISH', 'ema5': 1.1226},
        'm15': {'bias': 'BULLISH'},
        'news': {'impact': 'medium'},
        'decision_layer': {'suggested_action': 'WAIT'},
        'engines': {'trend': {'direction': 'UP'}},
        'signals': {'triggered': [], 'count': 0, 'top_signal': 'NO'},
    }

    rendered = build_template_prompt(context)

    assert 'meta:' in rendered
    assert 'market_context:' in rendered
    assert 'timeframes:' in rendered
    assert 'price_action:' in rendered
    assert 'volume:' in rendered
    assert 'analysis:' in rendered
    assert 'signals:' in rendered
    assert 'decision_layer:' in rendered

    assert 'market_state:' not in rendered
    assert 'm1:' not in rendered
    assert 'm5:' not in rendered
    assert 'm15:' not in rendered
    assert 'news:' not in rendered
    assert 'engines:' not in rendered
