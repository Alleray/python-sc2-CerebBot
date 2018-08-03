"""
Created on Mon Jul 23 20:16:20 2018

"""
import random
import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer

"""
This bot can defeat Very Hard Terran AI.
3-base hydralisk push.
"""

class Cerebrate(sc2.BotAI):
    def __init__(self):
        self.lair_started = False
        self.Boost = False
        self.queens = {}
        self.hydraden = False
        self.rwarren = False
        self.assigned_hatcheries = []
        self.more_hatcheries = 2
        self.enemy_at_the_gates = False
    
    async def on_step(self, iteration):
        await self.distribute_workers() 
        await self.spawn_lords()
        await self.morph_extractor()
        await self.expand()
        await self.spawn_army()
        await self.attack()
        await self.control_queens()
        
        if len(self.known_enemy_units) > 2:
            enemy_position = random.choice(self.known_enemy_units).position
            base = self.units(HATCHERY).closest_to(enemy_position)
            self.enemy_at_the_gates = (base.position.distance_to(enemy_position)) < 9.0
        if self.workers.amount >= 33 and not self.lair_started:
                await self.mutate_to_lair()
        elif not self.enemy_at_the_gates and self.workers.amount <= 60:
            await self.spawn_drones()
        else:
            await self.spawn_army()

    async def spawn_drones(self):
        """
        Spawn a new drone if amount of drones is less than 22 per owned expansion
        max workers = 60
        """
        for larva in self.units(LARVA).ready.noqueue:
            if self.can_afford(DRONE) and self.supply_left > 0:
                await self.do(larva.train(DRONE))
                    
    async def spawn_army(self):
        """
        Produces an army and necessary buildings
        Unit upgrades - coming soon
        """
        if not self.units(SPAWNINGPOOL).ready.exists:
            await self.morph_spawning_pool()
        else:
            if not self.units(HYDRALISKDEN).exists:
                await self.mutate_to_lair()
            if not self.units(ROACHWARREN).exists:
                await self.morph_roach_warren()
        if self.units(LAIR).exists:
            await self.morph_hydraden()
        if self.units(HYDRALISKDEN).exists and self.supply_left > 1:
            await self.spawn_hydras()
        if self.enemy_at_the_gates:
            if self.units(ROACHWARREN).exists and self.supply_left > 1:
                await self.spawn_roaches()
            else:
                await self.spawn_zerglings()
        
    async def attack(self):
        for zerglings in self.units(ZERGLING).idle:
            if self.enemy_at_the_gates:
                await self.do(zerglings.attack(self.find_target(self.state)))
            elif self.units(ZERGLING).amount >= 60:
                await self.do(zerglings.attack(self.find_target(self.state)))
        for hydras in self.units(HYDRALISK).idle:
            if self.enemy_at_the_gates:
                await self.do(hydras.attack(self.find_target(self.state)))
            elif self.units(HYDRALISK).amount >= 30:
                await self.do(hydras.attack(self.find_target(self.state)))
        for roaches in self.units(ROACH).idle:
            if self.enemy_at_the_gates:
                await self.do(roaches.attack(self.find_target(self.state)))
            elif self.units(ROACH).amount >= 30:
                await self.do(roaches.attack(self.find_target(self.state)))
                
    async def control_queens(self):
        """
        Builds a queen if a hatchery has no assigned queens
        Assigns new queen to the hatchery
        Injects larvae
        """
        #build a queen
        if len(self.units(QUEEN)) < len(self.units(HATCHERY)):
            if self.units(SPAWNINGPOOL).ready:
                for hatchery in self.units(HATCHERY).ready.noqueue:
                    if hatchery.tag not in self.assigned_hatcheries:
                        if self.can_afford(QUEEN):
                            await self.do(hatchery.train(QUEEN))  
        #assign a queen to the hatchery
        for queen in self.units(QUEEN).idle:
            for hatchery in self.units(HATCHERY).ready:
                if queen.tag not in self.queens:
                    if hatchery.tag not in self.assigned_hatcheries:
                        self.queens[queen.tag] = hatchery.tag
                        self.assigned_hatcheries.append(hatchery.tag)
        #inject larvae
        for queen in self.units(QUEEN).ready.noqueue:
            if queen.tag in self.queens:
                abilities = await self.get_available_abilities(queen)
                hatch = self.units().find_by_tag(self.queens[queen.tag])
                if AbilityId.EFFECT_INJECTLARVA in abilities:
                    await self.do(queen(EFFECT_INJECTLARVA, hatch))   
                    
    async def spawn_roaches(self):
        if self.units(ROACHWARREN).ready.exists:
            for larva in self.units(LARVA).ready.noqueue:
                if self.can_afford(ROACH) and self.supply_left != 0:
                    await self.do(larva.train(ROACH))
            
    async def morph_roach_warren(self):
        if not self.rwarren:
            if self.can_afford(ROACHWARREN):
                await self.build(ROACHWARREN, near=self.start_location)
                self.rwarren = True
        
    async def mutate_to_lair(self):
        hq = self.units(HATCHERY).noqueue.closest_to(self.start_location)
        if not self.units(LAIR).exists and hq.noqueue:
            if self.can_afford(LAIR) and not self.lair_started:
                await self.do(hq.build(LAIR))
                self.lair_started = True
                
    async def spawn_hydras(self):
        if self.units(HYDRALISKDEN).ready.exists:
            for larva in self.units(LARVA).ready.noqueue:
                if self.can_afford(HYDRALISK) and self.supply_left != 0:
                    await self.do(larva.train(HYDRALISK))
    
    def find_target(self,state):
        if len(self.known_enemy_units) > 0:
            return random.choice(self.known_enemy_units).position
        elif len(self.known_enemy_structures) > 0:
            return random.choice(self.known_enemy_structures).position
        else:
            return self.enemy_start_locations[0]
         
    async def spawn_zerglings(self):
        if self.units(SPAWNINGPOOL).exists:
            if self.units(ZERGLING).amount < 40:
                for larva in self.units(LARVA).ready.noqueue:
                    if self.can_afford(ZERGLING) and self.supply_left != 0:
                        await self.do(larva.train(ZERGLING))
        
    async def morph_spawning_pool(self):
        if len(self.owned_expansions) > 1:
            if self.can_afford(SPAWNINGPOOL) \
            and not self.already_pending(SPAWNINGPOOL):
                for hatchery in self.units(HATCHERY).ready:
                    await self.build(SPAWNINGPOOL, near=hatchery)
                    
    async def morph_hydraden(self):
        if not self.units(HYDRALISKDEN).exists and not self.hydraden:
            if self.can_afford(HYDRALISKDEN):
                for spool in self.units(SPAWNINGPOOL).ready:
                    await self.build(HYDRALISKDEN, near=self.start_location)
                    self.hydraden = True
        
    async def spawn_lords(self):
        if not self.already_pending(OVERLORD):
            for larva in self.units(LARVA).ready.noqueue:
                if self.supply_cap < 50:
                    if self.can_afford(OVERLORD) and self.supply_left <= 8:
                        await self.do(larva.train(OVERLORD))
                elif self.supply_cap >= 50 and self.supply_cap < 100:
                    if self.can_afford(OVERLORD) and self.supply_left <= 30:
                        await self.do(larva.train(OVERLORD))
                elif self.supply_cap != 200:
                    if self.can_afford(OVERLORD) and self.supply_left <= 50:
                        await self.do(larva.train(OVERLORD))
    
    async def morph_extractor(self):
        if len(self.owned_expansions) > 2:
            for hatchery in self.units(HATCHERY).ready:
                vespenes = self.state.vespene_geyser.closer_than(10.0, hatchery)
                for vespene in vespenes:
                    if not self.can_afford(EXTRACTOR):
                        break
                    drone = self.select_build_worker(vespene.position)
                    if drone is None:
                        break
                    if not self.units(EXTRACTOR).closer_than(1.0, vespene).exists:
                        await self.do(drone.build(EXTRACTOR, vespene))
                    
    async def expand(self):
        """
        Expand if bot have less than 3 expands or state of owned mineral
        fields is not adequate
        """
        if not self.enemy_at_the_gates:
            if len(self.owned_expansions) < 3:
                if self.can_afford(HATCHERY):
                    await self.expand_now()
        if self.minerals > 2000:
            await self.expand_now()
#        for hatchery in self.units(HATCHERY):
#            if hatchery.ideal_harvesters < 10 and hatchery.ideal_harvesters > 0:
#                if self.can_afford(HATCHERY):
#                    await self.expand_now()
                

run_game(maps.get("AbyssalReefLE"), [
    Bot(Race.Zerg, Cerebrate()),
    Computer(Race.Random, Difficulty.VeryHard)
    ], realtime=False, save_replay_as="Cerebrate.SC2Replay")