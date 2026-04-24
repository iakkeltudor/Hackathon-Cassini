def calculate_water_quality_score(do_est: float, nutrient_est: float):
    # Rules-based / ML hybrid risk engine
    score = 100.0 - (nutrient_est * 10) + (do_est * 2)
    return max(0, min(100, score))
