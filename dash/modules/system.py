import psutil


class SystemModule:
    def __init__(self, app, route_prefix="/api/system"):
        self.app = app
        self.route_prefix = route_prefix
        self.app.add_url_rule(self.route_prefix, "system_stats", self.get_stats)

    def get_power(self, avg: bool = False):
        # power = "nan"
        # last_power_check = 0
        # power_check_interval = 5 * 60

        # try:
        #     with open("/var/log/power.csv", "r") as file:
        #         if not avg:
        #             pwrstr = file.readlines()[-1].strip().split(",")[-1]
        #             try:
        #                 return float(pwrstr)
        #             except ValueError:
        #                 pass

        #             return "nan"

        #         pwrlist = [line.strip().split(",")[-1] for line in file.readlines()]

        #         take = 10
        #         i = 0
        #         pwrsum = 0
        #         while take > 0:
        #             i += 1
        #             try:
        #                 pwrsum += float(pwrlist[-i])
        #                 take -= 1
        #             except ValueError:
        #                 pass
        #             finally:
        #                 if i == len(pwrlist):
        #                     break

        #         if pwrsum == 0:
        #             return "nan"

        #         return pwrsum / (10 - take)

        # except Exception as e:
        #     logging.error(e)
        #     return "nan"

        # Average consumption of my laptop, hardcode until better configuration
        return 9

    def get_stats(self):
        # global last_power_check, power
        # if time() - last_power_check > power_check_interval:
        #     last_power_check = time()
        power = self.get_power(False)

        return {
            "cpu": psutil.cpu_percent(interval=1),
            "memory": psutil.virtual_memory()._asdict(),
            "disk": psutil.disk_usage("/")._asdict(),
            "power": power,
        }
