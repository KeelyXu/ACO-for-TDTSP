import requests
from bs4 import BeautifulSoup
import re
import time


class QueueTimesScraper:
    def __init__(self):
        self.base_url = "https://queue-times.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def get_park_id(self, park_name):
        """获取乐园 ID"""
        res = requests.get(f"{self.base_url}/parks.json", headers=self.headers)
        for group in res.json():
            for park in group['parks']:
                if park_name.lower() in park['name'].lower():
                    return park['id'], park['name']
        return None, None

    def get_ride_list(self, park_id):
        """获取乐园内所有设施的名称和 ID 映射"""
        url = f"{self.base_url}/parks/{park_id}/queue_times.json"
        data = requests.get(url, headers=self.headers).json()
        ride_map = {}
        for land in data.get('lands', []):
            for ride in land.get('rides', []):
                ride_map[ride['name']] = ride['id']
        # 有些乐园设施不在 lands 下
        for ride in data.get('rides', []):
            ride_map[ride['name']] = ride['id']
        return ride_map

    def scrape_osm_info(self, park_id, ride_id):
        """从设施详情页抓取 OSM 链接"""
        url = f"{self.base_url}/parks/{park_id}/rides/{ride_id}"
        print(f"  -> 正在抓取详情页: {url}")

        res = requests.get(url, headers=self.headers, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        text = soup.text
        # 用正则提取 lat,lon 格式
        match = re.search(r"Coordinates \(OSM\)\s*([\d\.\-]+),\s*([\d\.\-]+)", text)
        if match:
            lat, lon = float(match.group(1)), float(match.group(2))
        else:
            print("坐标提取失败")
            return None

        return lat, lon

    def get_hourly_history(self, park_id, target_rides_map):
        """
        从每个项目详情页抓取：
        Average queue time by hour (all time)
        返回格式：
        {
            ride_name: [[hour, avg_wait], ...]
        }
        """
        results = {}

        for ride_name, ride_id in target_rides_map.items():
            url = f"{self.base_url}/parks/{park_id}/rides/{ride_id}"
            print(f"\n正在处理项目: {ride_name}")
            print(f"  -> 正在抓取逐小时数据: {url}")

            try:
                res = requests.get(url, headers=self.headers, timeout=10)
                soup = BeautifulSoup(res.text, "html.parser")

                hourly_data = []

                headers = soup.find_all(["h2", "h3"])
                target_header = None
                for h in headers:
                    if "Average queue time by hour" in h.get_text():
                        target_header = h
                        break

                if not target_header:
                    print(f"     未找到逐小时表格标题: {ride_name}")
                    results[ride_name] = []
                    continue

                table = target_header.find_next("table")
                if not table:
                    print(f"     未找到逐小时表格: {ride_name}")
                    results[ride_name] = []
                    continue

                rows = table.find_all("tr")[1:]  # 跳过表头
                for row in rows:
                    cols = [c.get_text(strip=True) for c in row.find_all("td")]
                    if len(cols) >= 2:
                        hour = int(cols[0])
                        avg_wait = cols[1].replace("mins", "").strip()
                        try:
                            hourly_data.append([hour, float(avg_wait)])
                        except ValueError:
                            continue

                results[ride_name] = hourly_data

                time.sleep(1)  # 礼貌延迟

            except Exception as e:
                print(f"     抓取失败 {ride_name}: {e}")
                results[ride_name] = []

        return results


# --- 执行主程序 ---
if __name__ == "__main__":
    scraper = QueueTimesScraper()

    # 1. 配置
    park_query = "Shanghai Disney Resort"  # 乐园名称关键词
    target_ride_names = ["Seven Dwarfs Mine Train"]  # 指定项目列表

    # 2. 获取乐园信息
    park_id, full_park_name = scraper.get_park_id(park_query)

    if park_id:
        print(f"确定乐园: {full_park_name} (ID: {park_id})")

        # 3. 获取设施 ID 映射
        all_rides = scraper.get_ride_list(park_id)

        # 筛选出用户指定的项目
        final_targets = {name: all_rides[name] for name in target_ride_names if name in all_rides}

        # 4. 抓取 OSM 和 历史时间
        osm_results = {}
        for name, r_id in final_targets.items():
            print(f"正在处理项目: {name}")
            osm_results[name] = scraper.scrape_osm_info(park_id, r_id)
            time.sleep(1)  # 礼貌抓取，避免频率过高

        history_results = scraper.get_hourly_history(park_id, final_targets)

        # 5. 打印结果
        print("\n" + "=" * 50)
        for name in final_targets:
            print(f"\n项目名称: {name}")
            print(f"OSM : {osm_results.get(name)}")
            history = history_results.get(name, [])
            if history:
                print(f"逐小时历史排队时间:")
                for h in history:
                    print(f"  {h[0]} -> {h[1]} 分钟")
            else:
                print("未找到历史记录。")
    else:
        print("未找到该乐园，请检查名称。")
