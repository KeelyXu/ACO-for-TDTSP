import random
from datetime import datetime, timedelta


# define ant class
class Ant:

    attractions_to_visit = None
    start_pos = None
    start_datetime = None

    def __init__(self, ant_key: tuple[str, str]):
        assert ant_key in PARAM_ANT.keys()
        self.stage = ant_key[0]
        self.ant_type = ant_key[1]
        self.params = PARAM_ANT[ant_key]
        self.route = [] # 访问的游乐项目名称顺序
        self.route_length = 0.0

    def get_route_length(self, end_times: list = None, record_time=False):
        current_datetime = Ant.start_datetime
        current_pos = Ant.start_pos
        T_total = 0
        start_id = 0

        if record_time:
            self.record_time = []

        if end_times is not None:
            if len(end_times) == len(self.route):
                return end_times[-1]
            current_datetime = current_datetime + timedelta(minutes=end_times[-1])
            current_pos = self.route[len(end_times) - 1]
            T_total = end_times[-1]
            start_id = len(end_times)

        for i in range(start_id, len(self.route)):
            tmp_destination = self.route[i]
            # 到这个点的路途用时
            T_travel = TRAVEL_TIME[No[current_pos]][No[tmp_destination]]
            # 在这个项目排队用时
            T_wait = predict_waiting_time(tmp_destination, current_datetime + timedelta(minutes=T_travel))
            # 在这个项目游玩用时
            T_enjoy = STAY_TIME[No[tmp_destination]]
            T_delta = T_travel + T_wait + T_enjoy
            T_total += T_delta
            current_datetime = current_datetime + timedelta(minutes=T_delta)
            current_pos = tmp_destination
            if record_time:
                self.record_time.append(current_datetime)

        return T_total

    def get_end_times(self):
        current_datetime = Ant.start_datetime
        current_pos = Ant.start_pos
        T_total = 0

        end_times = []

        for i in range(len(self.route)):
            tmp_destination = self.route[i]
            T_travel = TRAVEL_TIME[No[current_pos]][No[tmp_destination]]
            T_wait = predict_waiting_time(tmp_destination,
                                          current_datetime + timedelta(
                                              minutes=T_travel))
            T_enjoy = STAY_TIME[No[tmp_destination]]
            T_delta = T_travel + T_wait + T_enjoy
            T_total += T_delta
            end_times.append(T_total)
            current_datetime = current_datetime + timedelta(minutes=T_delta)
            current_pos = tmp_destination

        return end_times

    def construct_route(self, constructed_routes: list = None, F: dict = None, LF: dict = None):
        assert self.ant_type != "elite"
        self.route_length = 0.0
        attractions_to_visit = Ant.attractions_to_visit[:]
        if self.ant_type in ["stochastic", "deterministic"]:
            current_datetime = Ant.start_datetime
            current_pos = Ant.start_pos
            t = 1
            while len(attractions_to_visit) > 0:
                weights = []
                for attraction in attractions_to_visit:
                    # 到这个点的路途用时
                    T_travel = TRAVEL_TIME[No[current_pos]][No[attraction]]
                    # 在这个项目排队用时
                    T_wait = predict_waiting_time(attraction, current_datetime + timedelta(minutes=T_travel))
                    # 在这个项目游玩用时
                    T_enjoy = STAY_TIME[No[attraction]]
                    T_delta = T_travel + T_wait + T_enjoy
                    C = T_delta
                    A = (F[current_pos, attraction, t]**self.params['alpha'] * C ** (-self.params['beta'])
                         * LF[current_pos, attraction, t] ** self.params['gamma'])
                    weights.append(A)
                if self.ant_type == "stochastic":
                    next_attraction = random.choices(attractions_to_visit, weights=weights, k=1)[0]
                else:
                    next_attraction = attractions_to_visit[weights.index(max(weights))]
                attractions_to_visit.remove(next_attraction)
                self.route.append(next_attraction)
                T_travel = TRAVEL_TIME[No[current_pos]][No[next_attraction]]
                T_wait = predict_waiting_time(next_attraction,
                                              current_datetime + timedelta(minutes=T_travel))
                T_enjoy = STAY_TIME[No[next_attraction]]
                T_delta = T_travel + T_wait + T_enjoy
                current_datetime = current_datetime + timedelta(minutes=T_delta)
                current_pos = next_attraction
                t += 1
                self.route_length += T_delta
        else:
            iter = 0
            while iter < 10:
                random.shuffle(attractions_to_visit)
                if attractions_to_visit not in constructed_routes:
                    break
                iter += 1
            self.route = attractions_to_visit
            self.route_length = self.get_route_length()


# helper function
def predict_waiting_time(attraction: str, start_datetime: datetime):
    # use a simple way to predict: interpolate linearly
    queue_time = WAIT_TIME[attraction]
    open_time = queue_time[0][0]
    close_time = queue_time[-1][0]
    hour = start_datetime.hour
    minute = start_datetime.minute

    if hour < open_time or hour > close_time:
        wait_time1 = 10000
    else:
        wait_time1 = queue_time[hour - open_time][1]

    if hour + 1 < open_time or hour + 1 > close_time:
        wait_time2 = 10000
    else:
        wait_time2 = queue_time[hour + 1 - open_time][1]

    predicted_wait_time = wait_time1 + minute / 60 * (wait_time2 - wait_time1)
    return predicted_wait_time


def local_search(best_ant: Ant):
    best_ant.route = best_ant.route[:]  # 防止与其它的route之间存在引用关系
    initial_route = best_ant.route[:]
    end_times = best_ant.get_end_times()
    best_route = initial_route
    min_route_len = best_ant.route_length
    for s in range(1, len(initial_route)):
        best_ant.route[s - 1] = initial_route[s]
        best_ant.route[s] = initial_route[s - 1]
        if s >= 2:
            best_ant.get_route_length(end_times[:s - 1])
        else:
            best_ant.get_route_length()
        # update best solution if it's obtained
        if best_ant.route_length < min_route_len:
            min_route_len = best_ant.route_length
            best_route = best_ant.route
        best_ant.route = initial_route[:]
    best_ant.route = best_route
    best_ant.route_length = min_route_len
    return best_ant


def plan_route(attractions_to_visit: list,
               start_time: str = "9:30", current_pos: str = "Fantasia Carousel"):
    for attraction in attractions_to_visit:
        assert attraction in ATTRACTIONS
    start_time = ''.join(start_time.split())
    start_time = datetime.strptime(start_time, '%H:%M').time()
    today = datetime.now().date()
    start_datetime = datetime.combine(today, start_time)

    Ant.attractions_to_visit = attractions_to_visit
    Ant.start_datetime = start_datetime
    Ant.start_pos = current_pos

    attractions = attractions_to_visit + [current_pos]
    T = [i + 1 for i in range(len(attractions) - 1)]
    F = dict()
    LF = dict()
    for i in attractions:
        for j in attractions:
            for t in T:
                F[i, j, t] = 1
                LF[i, j, t] = 1

    stagn_start_iter = -1
    best_route = None
    min_route_len = 1e8

    for l in range(PARAM_PROGRAM["maxTime"]):
        if l < PARAM_PROGRAM["initTime"]:
            stage = "init"
        elif l > PARAM_PROGRAM["maxTime"] - PARAM_PROGRAM["finishTime"]:
            stage = "final"
        else:
            if stagn_start_iter >= 0 and l - stagn_start_iter >= PARAM_PROGRAM["stagnCounter"]:
                stage = "stagnate"
            else:
                stage = "main"

        # create ants
        explored_routes = []
        route_len = []
        ants = []
        for ant_key in PARAM_ANT.keys():
            if stage in ant_key:
                ant_num = PARAM_ANT[ant_key]["count"]
                ant_type = ant_key[1]
            else:
                continue

            for ant_id in range(ant_num):
                # create an ant
                if ant_type == "elite":
                    ant = Ant(ant_key)
                    ant.route = best_route
                    ant.route_length = min_route_len
                    explored_routes.append(best_route)
                    route_len.append(min_route_len)
                else:
                    # construct route for this ant
                    ant = Ant(ant_key)
                    ant.construct_route(explored_routes, F, LF)
                    explored_routes.append(ant.route)
                    route_len.append(ant.route_length)
                ants.append(ant)

        # find best solution in this interation
        min_route_len_of_iteration = min(route_len)
        id_in_list = route_len.index(min_route_len_of_iteration)
        best_ant_in_a_iter = ants[id_in_list]

        # do local research
        if PARAM_PROGRAM['improvePath']:
            improved_ant = local_search(best_ant_in_a_iter)
            explored_routes[id_in_list] = improved_ant.route
            route_len[id_in_list] = improved_ant.route_length
        else:
            improved_ant = best_ant_in_a_iter

        # check whether the best solution has been improved
        if improved_ant.route_length >= min_route_len:
            if stagn_start_iter == -1:
                stagn_start_iter = l
        else:
            min_route_len = improved_ant.route_length
            best_ant = improved_ant
            # print(min_route_len)    # print optimization process
            best_route = improved_ant.route
            if stage == "stagnate":
                stagn_start_iter = -1

        # update pheromones
        # update F
        for key in F:
            F[key] = F[key] * RHO[stage]

        for ant in ants:
            route = ant.route
            for j in range(len(route)):
                if j == 0:
                    F[current_pos, route[j], 1] += (1 - RHO[stage]) / (M * ant.route_length)
                else:
                    F[route[j - 1], route[j], j + 1] += (1 - RHO[stage]) / (M * ant.route_length)

        # update LF
        if stage != "init" and stage != "stagnate":
            for key in LF:
                LF[key] = LF[key] * RHO[stage]
            for ant in ants:
                route = ant.route
                LR = ant.params['LR']
                for j in range(min(LR, len(route))):
                    if j == 0:
                        LF[current_pos, route[j], 1] += (1 - RHO[stage]) / (M * ant.route_length) / (LR + 1)
                    else:
                        LF[route[j - 1], route[j], j + 1] += (1 - RHO[stage]) / (M * ant.route_length) * (LR - j) / (LR**2 + LR)

    print(f"Total Time Needed (Estimates): {min_route_len} min")

    return best_route


if __name__ == '__main__':
    import json
    from utils.ThemePark import ThemePark

    with open("parks/ShanghaiDisney.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    disney = ThemePark(**data)

    # 读取一些全局变量
    WAIT_TIME = disney.history_results
    TRAVEL_TIME = disney.walking_time
    ATTRACTIONS = disney.valid_rides

    # 每个项目游玩的时间，这里做了简单化处理，认为都是10分钟
    STAY_TIME = [10] * len(WAIT_TIME)

    # set id of attractions
    No = dict()
    i = 0
    for entertainment in WAIT_TIME:
        No[entertainment] = i
        i += 1

    # set parameters
    PARAM_PROGRAM = {"maxTime": 100, "finishTime": 10, "initTime": 10,
                     "stagnCounter": 10, "improvePath": True}
    RHO = {"init": 0.9, "main": 0.9, "stagnate": 0.3, "final": 0.5}
    PARAM_ANT = {("init", "random"): {"count": 100},
                 ("stagnate", "random"): {"count": 100},
                 ("main", "stochastic"): {"alpha": 0.8, "beta": 0.7, "gamma": 0.9, "count": 200, "LR": 10},
                 ("main", "deterministic"): {"alpha": 0.8, "beta": 0.8, "gamma": 0.5, "count": 50, "LR": 5},
                 ("final", "stochastic"): {"alpha": 0.2, "beta": 0.2, "gamma": 0.5, "count": 150, "LR": 3},
                 ("final", "stochastic"): {"alpha": 0.5, "beta": 0.1, "gamma": 0.1, "count": 100, "LR": 5}}

    M = 1

    # ---------------- generate a random case ----------------
    random.seed(0)
    visit_attractions = random.sample(ATTRACTIONS, k=6)
    current_pos = visit_attractions.pop()
    print(f'Current Position: {current_pos}')
    print(f'Entertainments to visit: {visit_attractions}\n')
    # --------------------------------------------------------

    result = plan_route(visit_attractions, start_time="9:30", current_pos=current_pos)
    print(f'Recommended route: {result}')
