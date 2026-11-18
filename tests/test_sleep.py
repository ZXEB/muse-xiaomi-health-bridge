from health_bridge.sleep import describe_sleep_day


def test_long_unstaged_sleep_and_secondary_staged_sleep_stay_separate():
    long_unstaged = {"asleep_min": 220}
    secondary = {"asleep_min": 180, "light_min": 130}
    main = {"asleep_min": 400, "deep_min": 80}
    nap = {"asleep_min": 15}
    day = describe_sleep_day("2026-11-18", 825, [long_unstaged, secondary, main, nap])
    assert day["main"] == main
    assert day["other"] == [long_unstaged, secondary]
    assert day["naps"] == [nap]
    assert day["nap_min"] == 15
    assert day["detail_status"] == "partial"


def test_incomplete_day_does_not_assume_zero_naps():
    main = {"asleep_min": 400, "deep_min": 80}
    day = describe_sleep_day("2026-11-18", 430, [main])
    assert day["nap_min"] is None
    assert day["total_min"] == 430
