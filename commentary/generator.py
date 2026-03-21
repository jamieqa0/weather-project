def generate_comment(temp_c: float, precipitation_mm: float, weather_code: int) -> str:
    """날씨 조건에 따른 감성 멘트 반환. 추후 LLM으로 교체 가능."""
    if temp_c < 0:
        return "오늘은 냉동창고 수준. 나가지 마세요. 진심으로."
    if temp_c >= 35:
        return "폭염 주의. 에어컨 없는 사람은 오늘 하루 용감한 겁니다."
    if precipitation_mm >= 20:
        return "우산은 장식이 아닙니다. 폭우 수준이에요."
    if weather_code in (61, 63, 65, 80, 81, 82):
        return "비 오네요. 우산 챙기셨죠? 안 챙기셨죠?"
    if weather_code in (71, 73, 75):
        return "눈 옵니다. 길 미끄러우니 조심하세요."
    if weather_code == 0 and temp_c >= 18:
        return "날씨만큼은 인생보다 맑네요. 나가세요."
    if temp_c < 5:
        return "꽤 춥습니다. 겉옷 챙기세요."
    return "오늘 날씨: 인생처럼 그럭저럭입니다."
