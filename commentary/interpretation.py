from datetime import datetime, timezone, timedelta


def interpret_correlation(pearson: float | None) -> str:
    """Pearson 상관계수를 한국어 해석 문장으로 반환."""
    if pearson is None:
        return "데이터 없음"

    abs_p = abs(pearson)
    direction = "음" if pearson < 0 else "양"
    toward = "낮을수록" if pearson < 0 else "높을수록"

    if abs_p < 0.1:
        return "거의 상관없음 — 기온은 지하철 혼잡도에 영향을 주지 않는 것으로 보여요."
    if abs_p < 0.3:
        return (
            f"약한 {direction}의 상관관계 — 기온이 {toward} 지하철이 약간 더 붐비는 경향이 있지만,"
            " 통계적으로 유의미하지 않아요."
        )
    if abs_p < 0.7:
        return (
            f"중간 {direction}의 상관관계 — 기온이 {toward} 지하철 이용객이 늘어나는 경향이 있어요."
        )
    return (
        f"강한 {direction}의 상관관계 — 기온이 {toward} 지하철 이용객이 뚜렷이 증가해요."
    )


def format_last_updated(dt: datetime = None) -> str:
    """datetime을 'M월 D일 오전/오후 H시 M분 기준' 형식으로 반환. (KST 기준)"""
    if dt is None:
        # KST(한국 표준시) 타임존으로 현재 시간 가져오기
        kst = timezone(timedelta(hours=9))
        dt = datetime.now(kst)

    if dt.hour == 0:
        hour, meridiem = 12, "오전"
    elif dt.hour < 12:
        hour, meridiem = dt.hour, "오전"
    elif dt.hour == 12:
        hour, meridiem = 12, "오후"
    else:
        hour, meridiem = dt.hour - 12, "오후"
    return f"{dt.month}월 {dt.day}일 {meridiem} {hour}시 {dt.minute}분 기준"


def format_montevideo_time(dt: datetime = None) -> str:
    """몬테비데오(우루과이) 시간을 'M월 D일 오전/오후 H시 M분' 형식으로 반환."""
    if dt is None:
        # UTC-3 (우루과이 표준시)
        utc_minus_3 = timezone(timedelta(hours=-3))
        dt = datetime.now(utc_minus_3)

    if dt.hour == 0:
        hour, meridiem = 12, "오전"
    elif dt.hour < 12:
        hour, meridiem = dt.hour, "오전"
    elif dt.hour == 12:
        hour, meridiem = 12, "오후"
    else:
        hour, meridiem = dt.hour - 12, "오후"
    return f"{dt.month}월 {dt.day}일 {meridiem} {hour}시 {dt.minute}분"


def get_anomaly_algorithm_info() -> str:
    """이상치 탐지에 사용된 알고리즘 및 파라미터 정보 반환."""
    return "🤖 Isolation Forest · 이상치 비율 5% · 전체 데이터 중 상위 5%의 극단적인 날을 이상 기후로 분류해요"
