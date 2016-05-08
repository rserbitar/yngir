from typing import List
import logging
logging.basicConfig(level=logging.DEBUG)
logger =logging.getLogger()

class Card():
    def __init__(self, name):
        self.name = name
        self.resource__count = 0
        self.damage_count = 0
        self.attached_cards = []
        self.attached_to = None
        self.revealed = True
        self.exhausted = False
        self.location = None


class Planet(Card):
    def __init__(self, name, resources, cards, text, icons):
        super().__init__(name)
        self.resources = resources
        self.cards = cards
        self.text = text
        self.icons = icons


class FactionCard(Card):
    def __init__(self, name, faction, cost, unique, traits, text, loyal, signature):
        super().__init__(name)
        self.cost = cost
        self.action = faction
        self.unique = unique
        self.traits = traits
        self.text = text
        self.loyal = loyal
        self.signature = signature


class Warlord(Card):
    def __init__(self, name, faction, unique, traits, resources, cards, atk, hp, text, atk_bloodied, hp_bloodied,
                 text_bloodied):
        super().__init__(name)
        self.action = faction
        self.unique = unique
        self.traits = traits
        self.resources = resources
        self.cards = cards
        self.atk = atk
        self.hp = hp
        self.text = text
        self.atk_bloodied = atk_bloodied
        self.hp_bloodied = hp_bloodied
        self.text_bloodied = text_bloodied
        self.command = 100
        self.bloodied = False

        def get_effective_command(self):
            command = 0
            if not self.exhausted:
                command = self.command
            return command


class Army(FactionCard):
    def __init__(self, name, faction, cost, unique, traits, loyal, signature, atk, hp, command, text):
        super().__init__(name, faction, cost, unique, traits, text, loyal, signature)
        self.atk = atk
        self.hp = hp
        self.command = command

        def get_effective_command(self):
            command = 0
            if not self.exhausted:
                command = self.command
            return command


class Event(FactionCard):
    def __init__(self, name, faction, cost, unique, traits, loyal, signature, shields, text):
        super().__init__(name, faction, cost, unique, traits, text, loyal, signature)
        self.shields = shields


class Attachment(FactionCard):
    def __init__(self, name, faction, cost, unique, traits, loyal, signature, shields, text):
        super().__init__(name, faction, cost, unique, traits, text, loyal, signature)
        self.shields = shields


class Support(FactionCard):
    pass


class Token(Card):
    def __init__(self, name, faction, atk, hp, traits):
        super().__init__(name)
        self.faction = faction
        self.atk = atk
        self.hp = hp
        self.traits = traits


    def get_effective_command(self):
        return 0


class Player():

    def __init__(self, name):
        self.name = name

    def get_warlord_commitment(self):
        # TODO: finalize
        return 0

    def get_deploy_action(self):
        # TODO: finalize
        card = None
        planet = None
        return card, planet

    def get_combat_move(self, planet_number):
        # TODO: finalize
        attacker = None
        defender = None
        return attacker, defender

    def get_retreat(self, planet_number):
        # TODO: finalize
        return None


class PlayArea():
    def __init__(self, planets: List[Planet]):
        self.planets = list(planets)
        self.hq = 'hq'
        self.cards_in_play = []

    def planet_units(self, planet, side):
        result = []
        if isinstance(planet, int):
            planet = self.planets[planet]
        for card in self.cards_in_play:
            if card.location == (planet, side):
                result.append(card)

    def hq_units(self, side):
        result = []
        for card in self.cards_in_play:
            if card.location == (self.hq, side):
                result.append(card)

    def all_exhausted(self, planet):
        return all([self.all_exhausted_onesided(planet, i) for i in range(2)])

    def all_exhausted_onesided(self, planet, side):
        cards = self.planet_units(planet,side)
        return all([card.exhausted for card in cards])


class Game():
    def __init__(self,
                 planets: List[Planet],
                 player: List[Player],
                 warlords: List[Warlord],
                 decks: List[List[Card]],
                 token_banks: List[List[Token]],
                 unused_planets: List[Planet]):
        self.player = player
        self.warlords = warlords
        self.decks = decks
        self.token_banks = token_banks
        self.unused_planets = unused_planets
        self.play_area = PlayArea(planets)
        self.hands = [[], []]
        self.resources = [0,0]
        self.discard_piles = [[], []]
        self.victory_displays = [[], []]
        self.initiative = 0
        self.turn = 1

    def draw_cards(self, player_num, number=1):
        for _ in range(number):
            self.hands[player_num].append(self.decks[player_num].pop(0))

    def turn(self):
        self.deploy_phase()
        self.command_phase()
        self.combat_phase()
        self.hq_phase()
        self.turn += 1

    def deploy_phase(self):
        player_0 = self.player[self.initiative]
        player_1 = self.player[self.initiative-1]
        passed = [False, False]
        while not all(passed):
            if not passed[0]:
                player_0.get_deploy_action()
            if not passed[1]:
                player_1.get_deploy_action()

    def command_phase(self):
        for player in self.player:
            player.get_warlord_commitment()
        for planet_number in range(5):
            self.resolve_command_struggle(planet_number)

    def combat_phase(self):
        combat_planets = self.get_combat_planets()
        for planet_number in combat_planets:
            self.resolve_combat(planet_number)

    def hq_phase(self):
        for card in self.play_area.cards_in_play:
            card.exhausted = False
            self.draw_cards(0,2)
            self.resources[0] += 4
            self.draw_cards(1, 2)
            self.resources[1] += 4

    def resolve_command_struggle(self, planet_number):
        planet = self.play_area.planets[planet_number]
        planet_cards = planet.cards
        planet_resources = planet.resources
        planet_area = self.play_area.planet_areas[planet_number]
        command0 = sum(card.get_effective_command() for card in planet_area[0])
        command1 = sum(card.get_effective_command() for card in planet_area[1])
        if command0 > command1:
            self.draw_cards(0, planet_cards)
            self.resources[0] += planet_resources
        elif command1 > command0:
            self.draw_cards(1, planet_cards)
            self.resources[1] += planet_resources

    def resolve_combat(self, planet_number):
        initiative = self.get_initiative(planet_number)
        combat = True
        while combat:
            while not self.play_area.all_exhausted(planet_number):
                if not self.play_area.all_exhausted_onesided(planet_number, initiative):
                    attacker, defender = self.player[initiative].get_combat_move(planet_number)
                    combat = self.do_combat_move(attacker, defender)
                    if not combat:
                        break
                if not self.play_area.all_exhausted_onesided(planet_number, initiative-1):
                    attacker, defender = self.player[initiative-1].get_combat_move(planet_number)
                    combat = self.do_combat_move(attacker, defender)
                    if not combat:
                        break
            for i in range(2):
                for card in self.play_area.planet_areas[planet_number][i]:
                    card.exhausted = False
            self.player[initiative].get_retreat(planet_number)
            self.player[initiative-1].get_retreat(planet_number)

    def get_combat_planets(self):
        # TODO: finalize
        return [0]

    def get_initiative(self, planet_number):
        # TODO: finalize
        return self.initiative

    def do_combat_move(self, attacker, defender):
        # TODO: finalize
        return None