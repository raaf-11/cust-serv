from app.services.pdf_service import fix_rupee_symbol


def test_black_square_before_amount_becomes_rupee():
    assert fix_rupee_symbol("SmartCare Plus\n■2,499") == "SmartCare Plus\n₹2,499"
    assert fix_rupee_symbol("loans up to ■1,00,000") == "loans up to ₹1,00,000"


def test_black_square_not_before_amount_is_left_alone():
    assert fix_rupee_symbol("■ Step one") == "■ Step one"
