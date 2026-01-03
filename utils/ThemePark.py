import time
import requests
from dataclasses import dataclass
from utils.Scraper import QueueTimesScraper


def get_walk_time_osrm(lat1, lon1, lat2, lon2):
    url = (
        f"https://router.project-osrm.org/route/v1/foot/"
        f"{lon1},{lat1};{lon2},{lat2}"
        f"?overview=false"
    )
    r = requests.get(url)
    data = r.json()

    if data["code"] != "Ok":
        raise Exception("Routing failed")

    duration_seconds = data["routes"][0]["duration"]
    return duration_seconds / 60  # 转为分钟


@dataclass
class ThemePark:
    park_id: int
    park_name: str
    valid_rides: list[str]
    osm_results: dict[str, tuple[float, float]]
    history_results: dict
    walking_time: list[list[float]]
    open_time: int
    close_time: int

    @classmethod
    def from_scraper(cls, park_name: str, ride_name_list: list[str] | None = None,
                     open_time: int=8, close_time: int=20):
        scraper = QueueTimesScraper()
        park_id, full_park_name = scraper.get_park_id(park_name)

        if not park_id:
            raise ValueError("未找到该乐园")

        print(f"确定乐园: {full_park_name} (ID: {park_id})")
        all_rides = scraper.get_ride_list(park_id)

        if ride_name_list:
            final_targets = {n: all_rides[n] for n in ride_name_list if n in all_rides}
        else:
            final_targets = all_rides

        osm_results = {}
        for name, r_id in final_targets.items():
            print(f"\n正在处理项目: {name}")
            osm_results[name] = scraper.scrape_osm_info(park_id, r_id)
            time.sleep(1)

        history_results = scraper.get_hourly_history(park_id, final_targets)

        # 只有信息完整的项目才是有效的
        valid_rides = [
            r for r in final_targets
            if osm_results[r] and history_results[r]
        ]

        osm_results = {r: osm_results[r] for r in valid_rides}
        history_results = {r: history_results[r] for r in valid_rides}

        walking_time = cls._compute_walking_time(valid_rides, osm_results)

        return cls(
            park_id=park_id,
            park_name=full_park_name,
            valid_rides=valid_rides,
            osm_results=osm_results,
            history_results=history_results,
            walking_time=walking_time,
            open_time=open_time,
            close_time=close_time
        )

    @staticmethod
    def _compute_walking_time(valid_rides, osm_results):
        n = len(valid_rides)
        matrix = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                lat1, lon1 = osm_results[valid_rides[i]]
                lat2, lon2 = osm_results[valid_rides[j]]
                t = get_walk_time_osrm(lat1, lon1, lat2, lon2)
                matrix[i][j] = matrix[j][i] = t
                print(f"{valid_rides[i]} -> {valid_rides[j]}: {t} min")
        return matrix


if __name__ == "__main__":
    from dataclasses import asdict
    import json

    disney = ThemePark.from_scraper(
        "Shanghai Disney Resort",
        # ["Camp Discovery", "Soaring Over the Horizon"]
    )

    with open("../parks/ShanghaiDisney.json", "w", encoding="utf-8") as f:
        json.dump(asdict(disney), f, ensure_ascii=False, indent=2)
