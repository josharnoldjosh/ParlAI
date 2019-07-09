#!/usr/bin/env python3

# Copyright (c) Facebook, Inc. and its affiliates.
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

from copy import deepcopy

from parlai.core.params import ParlaiParser
from parlai.core.agents import create_agent
from parlai.core.worlds import create_task
from parlai.core.worlds import DialogPartnerWorld, validate
from parlai.agents.repeat_label.repeat_label import RepeatLabelAgent


class InteractiveWorld(DialogPartnerWorld):
    def __init__(self, opt, agents, shared=None):
        super().__init__(opt, agents, shared)
        print("[ loading topics.. ]")
        self.load_topics()

    def load_topics(self):
        # Create Wizard data so we can assign personas.
        wizard_opt = self.opt.copy()
        wizard_opt['task'] = 'wizard_of_wikipedia'
        wizard_opt['interactive_task'] = False
        wizard_agent = RepeatLabelAgent(wizard_opt)
        self.wizard_world = create_task(wizard_opt, wizard_agent)
        self.cnt = 0

    def get_new_topic(self):
        # Find a new episode
        while True:
            self.wizard_world.parley()
            msg = self.wizard_world.get_acts()[0]
            if msg.get('episode_done', False):
                self.wizard_world.parley()
                msg = self.wizard_world.get_acts()[0]
                break
        txt = msg.get('text', '').split('\n')
        a1_persona = ""
        a2_persona = ""
        import pdb; pdb.set_trace()
        for t in txt:
            if t.startswith("partner's persona:"):
                a1_persona += t.replace("partner's persona:", 'your persona:') + '\n'
            if t.startswith('your persona:'):
                a2_persona += t + '\n'
        return a1_persona, a2_persona

    def parley(self):
        """Agent 0 goes first. Alternate between the two agents."""
        if self.cnt == 0:
            self.p1, self.p2 = self.get_new_topic()


            
        acts = self.acts
        agents = self.agents
        if self.cnt == 0:
            # add the persona on to the first message to agent 0
            act = {}
            act['text'] = self.p1
            act['episode_done'] = False
            act['id'] = 'persona'
            agents[0].observe(validate(act))
        act = deepcopy(agents[0].act())
        if self.cnt == 0:
            # add the persona on to the first message to agent 1
            act['text'] = self.p2 + act.get('text', 'hi')
            agents[1].observe(validate(act))
        else:
            agents[1].observe(validate(act))
        acts[1] = agents[1].act()
        agents[0].observe(validate(acts[1]))
        self.update_counters()
        self.cnt += 1

        if self.episode_done():
            print("CHAT DONE ")
            print("\n... preparing new chat... \n")
            self.cnt = 0
