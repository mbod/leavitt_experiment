from .config import NETWORKS, NODES
from .prompts import SYSTEM_PROMPT, TURN_PROMPT

from openai import OpenAI
import json

from dotenv import load_dotenv
_ = load_dotenv()


class Node:

    def __init__(self, 
                 id: str, 
                 network: str,
                 card: str,
                 is_LLM: bool
                ):

        if id not in NODES:
            raise Exception(f'Node id must be one of {NODES}')
        
        self.id = id
        self.is_LLM = is_LLM
        self.in_chat = False

        
        self.LLM = OpenAI()
        
        if not network in NETWORKS.keys():
            raise Exception(f'Network must be one of: {NETWORKS.keys()}')
        
        self.network = network
        
        self.neighbors = NETWORKS[network][id]
        self.current_guess = None
        self.notes = []
        self.initial_data = card
        self.inbox = []
        self.outbox = []

    def __repr__(self):
        return f"""Node(id='{self.id}', network={self.network}, 
                   is_LLM={self.is_LLM},
                   in_chat={self.in_chat},
                   neighbors={self.neighbors},
                   initial_data={self.initial_data},
                   inbox={self.inbox},
                   outbox={self.outbox},
                   notes={self.notes}
                   """


    def send_message(self, recipient, content):
        """
        Send a message `content` to a neighbor checking it is allowed
        Returns:
            status
        """

        recipient_id = recipient.id

        if recipient_id not in self.neighbors:
            raise Exception(f'Trying to send a message to an non-neighbor')

        try:
            recipient.receive_message(self.id, content)
            self.outbox.append({'to': recipient_id,
                                'message': content})
            return f"Message '{content[:10]}...' sent to Node {recipient_id}'"
        except Exception as e:
            print(e)
            return False


    def receive_message(self, sender: str, content: str):
        """
        Receive a message from a sender and add to inbox
        """

        self.inbox.append({'from': sender, 'message': content})


    def take_turn(self):
        """
        Evaluate current knowledge and decide what action to take
        - send message to a neighbor
        - make a guess
        """

        #if self.current_guess:
        #    return f"Node {self.id} has guessed {self.current_guess}"
        
        current_inbox = '\n'.join([ f"{message['from']} said {message['message']}" for message in self.inbox]) if self.inbox else "No interactions"

        current_outbox = '\n'.join([ f"You sent {message['message']} to {message['to']}" for message in self.outbox]) if self.inbox else "No interactions"

        
        notes = '\n'.join(self.notes)

        
        current_knowledge = f"""
        Your initial data is: { self.initial_data }
        You have learned the following from your interactions:
        Your observations:
        {notes}

        Messages you have sent:
        {current_outbox}
                
        Messages you have received:
        {current_inbox}
        """

        messages = [
            {'role': 'system',
             'content': SYSTEM_PROMPT },

            {'role': 'user',
             'content': TURN_PROMPT.format(current_knowledge=current_knowledge, 
                                           neighbor_str = ' and '.join(self.neighbors)) },
        ]

        # TODO - give each node instance a specific LLM
        response = self.LLM.chat.completions.create(
            model="chatgpt-4o-latest",
            messages=messages,
            response_format={"type": "json_object"}
        )

        resp = json.loads(response.choices[0].message.content)

        if resp['current_guess']:
            self.current_guess = resp['current_guess']
        
        self.notes.append(resp['notes'])
        
        # send outgoing messages
        #for message in resp['outgoing_messages']:
        #    self.send_message(nodes[message['to']], message['content'])
        
        return resp