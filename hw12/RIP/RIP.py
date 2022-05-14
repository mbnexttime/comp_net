class Router:
    def __init__(self, name, neighs):
        self.name = name
        self.neighs = neighs


class RIP:
    inf = 1_000_000_000_000_000

    def __init__(self, routers):
        self.routers = routers
        self.dist = {}
        self.hop = {}
        for router in routers:
            self.dist[router.name] = {}
            self.hop[router.name] = {}
            for neigh in router.neighs:
                self.dist[router.name][neigh] = 1
                self.hop[router.name][neigh] = neigh

    def calc(self):
        step = 0
        while True:
            changed = False
            step += 1
            print(f'Начинается шаг {step}')
            for router_from in self.routers:
                for router_to in self.routers:
                    if router_from == router_to:
                        continue
                    for router_hop in router_from.neighs:
                        success = self.try_to_update(router_from.name, router_to.name,
                                                     1 + self.get_dist_or_inf(router_to.name, router_hop))
                        if success:
                            self.hop[router_from.name][router_to.name] = router_hop

                        changed |= success
                self.print_router_results(router_from.name)

            if not changed:
                break
        print(f'Протокол сошелся за {step} шаг(а)ов')
        for router in self.routers:
            self.print_router_results(router.name)

    def get_dist_or_inf(self, router_from, router_to):
        if router_to not in self.dist[router_from]:
            return RIP.inf
        return self.dist[router_from][router_to]

    def try_to_update(self, router_from, router_to, d):
        pr = self.get_dist_or_inf(router_from, router_to)
        if pr <= d:
            return False
        self.dist[router_from][router_to] = d
        return True

    def print_router_results(self, router):
        print(f'{"[Source IP]":25} {"[Destination IP]":25} {"[Next Hop]":25} {"[Metric]":25}')
        for (ip, d) in self.dist[router].items():
            if d == RIP.inf:
                d = "inf"
            else:
                d = str(d)

            print(f'{router:25} {ip:25} {self.hop[router][ip]:25} {d:25}')


routers = [
    Router("1.1.1.1", ["2.2.2.2", "3.3.3.3"]),
    Router("2.2.2.2", ["1.1.1.1"]),
    Router("3.3.3.3", ["1.1.1.1", "4.4.4.4", "5.5.5.5"]),
    Router("4.4.4.4", ["3.3.3.3"]),
    Router("5.5.5.5", ["3.3.3.3"])
]

rip = RIP(
    routers
)

rip.calc()