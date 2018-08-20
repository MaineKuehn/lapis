from cobald.controller.linear import LinearController
from cobald.interfaces import Pool


class SimulatedLinearController(LinearController):
    def __init__(self, env, target: Pool, low_utilisation=0.5, high_allocation=0.5, rate=1, interval=1):
        super(SimulatedLinearController, self).__init__(target, low_utilisation, high_allocation, rate, interval)
        self.env = env
        self.action = env.process(self.run())
        self._interval = interval

    def run(self):
        while True:
            self.regulate(interval=self._interval)
            # print("[controller] demand %d -> %d, supply %d (global %d), allocation %.2f, utilisation %.2f "
            #       "(available %d)" % (pre_demand, self.target.demand, self.target.supply, globals.global_demand.level,
            #                           self.target.allocation, self.target.utilisation, self.target.level))
            yield self.env.timeout(self._interval)
