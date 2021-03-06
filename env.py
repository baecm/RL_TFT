
import config_3 as cfg
import numpy as np
from fight.fight import Fight
from buff.items import Item
import time
# env
'''
# to do
1. 스킬 one_champ_tic에서 빠지고 synergy처럼 취급해야함
2. 비디오 완성
'''

class TFT_env(object):
    def __init__(self,elements,champ_state_info,champ_cost_info,champ_level_info,
        champ_distribution,sushi_distribution,synergy_info,agent1=None,agent2=None,
        agent3=None,agent4=None,agent5=None,agent6=None,agent7=None,agent8=None,
        **kwargs):
        '''
        action space :
        act1 = player's act before fight
        act2 = player's act about arrange units
        act3 = about item
        state :
        units, arrange, xp, money, life
        '''
        # base
        self.items = ['items']
        self.act1_spc = ['pick1','pick2','pick3','pick4','pick5','save','sell','reroll','xp']
        self.act2_spc = [i for i in range(28)]
        self.act3_spc = ['item']
        self.champ_state_info = champ_state_info
        self.champ_cost_info = champ_cost_info
        self.champ_level_info = champ_level_info
        self.cur_round = '1-1'
        self.synergy_info = synergy_info
        self.items = [2,3,5,6,7,8,9,10,12]
        self.elements = elements
        # player
        self.need_xp = [2,4,8,14,24,44,76,126,192]
        # about sushi,reroll
        self.sushi_distribution = sushi_distribution
        self.champ_distribution = champ_distribution
        # agent
        self.agent1 = agent1
        self.agent2 = agent2
        self.agent3 = agent3
        self.agent4 = agent4
        self.agent5 = agent5
        self.agent6 = agent6
        self.agent7 = agent7
        self.agent8 = agent8
        self.place_table = [['agent{}'.format(i+1),100] for i in range(8)]
    def init_game(self):
        self.players = [self.agent1,self.agent2,self.agent3,self.agent4,self.agent5,
            self.agent6,self.agent7,self.agent8]
        for n,player in enumerate(self.players):
            player.name = 'agent{}'.format(n+1)
            player.champ_distribution = self.champ_distribution
            player.champ_state_info = self.champ_state_info
            player.champ_level_info = self.champ_level_info
            player.champ_cost_info = self.champ_cost_info
            player.synergy_info = self.synergy_info
            player.act1_spc = self.act1_spc
            player.act2_spc = self.act2_spc
            player.act3_spc = self.act3_spc
            player.cur_round = self.cur_round
            player.need_xp = self.need_xp
            player.init_player()
        self._sushi()
    def _round(self):
        big_round = int(self.cur_round[0])
        sub_round = int(self.cur_round[-1])
        if big_round == 1:
            if sub_round == 4:
                big_round += 1
                sub_round = 1
            else:
                sub_round += 1
        else:
            if sub_round == 7:
                big_round += 1
                sub_round = 1
            else:
                sub_round += 1
        self.cur_round = '{}-{}'.format(big_round,sub_round)

    def _sushi(self):
        self.sushi = []
        stars = np.bincount(np.random.choice(range(5),9,
            p=self.sushi_distribution['r'+str(self.cur_round[0])]))
        for star,n_champs in zip(stars,self.champ_cost_info.items()):
            champs = list(np.random.choice(len(n_champs[1]),star,replace=False))
            self.sushi += [n_champs[1][c] for c in champs]
        orders = np.arange(8)
        np.random.shuffle(orders)
        item = list(np.random.choice(self.items,8,replace=False))
        for i,(order,player) in enumerate(zip(orders,self.players)):
            player.champ_append(self.sushi[order]+'_1',[item[i]])
            print('sushi finished {} champ is {}'.format(player.name,self.sushi[order]))
    def _prepare(self):
        for player in self.players:
            print(player.name)
            player.cur_round = self.cur_round
            player.prepare_round()
    def _match(self):
        match_queue = np.arange(len(self.players))
        np.random.shuffle(match_queue)
        match_queue = list(match_queue)
        if len(match_queue) % 2 == 1:
            ai = np.random.choice(match_queue[:-1],1)[0]
            match_queue.append(ai)
        match_queue = np.reshape(np.array(match_queue),(-1,2))
        return match_queue
    def _continuous(self,agent,win):
        if win:
            if agent.continuous >= 0:
                agent.continuous += 1
            else:
                agent.continuous = 1
        else:
            if agent.continuous <= 0:
                agent.continuous -= 1
            else:
                agent.continuous = -1
    def _game_over(self):
        for player in self.players:
            if player.life <= 0:
                self.players.remove(player)
    def play_round(self):
        result = 'sushi'
        print(self.cur_round)
        if self.cur_round == '1-1':
            1 == 1
        elif (self.cur_round[0] != '1') and (self.cur_round[-1] == '4'):
            self._sushi()
        else:
            self._prepare()
            match_order = self._match()
            for m in match_order:
                a1 = self.players[m[0]]
                a2 = self.players[m[1]]
                if a1.name == 'agent1':
                    print(a1.total_units)
                if a2.name == 'agent1':
                    print(a2.total_units)
                fight = Fight(a1,a2,self.cur_round)
                fight.my_queue = a1.five_champs
                fight.my_cost = a1.five_cost
                fight.my_money = a1.money
                fight.opp_money = a2.money
                fight.place_table = self.place_table
                result,life_change = fight.fight()
                fight.gui.root.destroy()
                time.sleep(1)
                print('finish fight!')
                if result:
                    a2.life -= life_change
                    a1.money += 1
                    self._continuous(a1,True)
                    self._continuous(a2,False)
                    a1.result(result)
                    a2.result(False)
                    self.place_table[int(a2.name[-1])-1] = [a2.name,a2.life]
                else:
                    a1.life -= life_change
                    a2.money += 1
                    self._continuous(a2,True)
                    self._continuous(a1,False)
                    a1.result(True)
                    a2.result(result)
                    self.place_table[int(a1.name[-1])-1] = [a1.name,a1.life]
        self._game_over()
        names = [player.name for player in self.players]
        print('survived players : {}'.format(names))
        self._round()
