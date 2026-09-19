from hyperliquid_bot.orderflow import compute_book_features

def test_book_features_realistic_snapshot():
    f=compute_book_features({"bids":[{"px":"100","sz":"5"}],"asks":[{"px":"101","sz":"3"}]})
    assert f is not None
    assert f.mid == 100.5
    assert f.imbalance > 0
    assert f.microprice > f.mid
